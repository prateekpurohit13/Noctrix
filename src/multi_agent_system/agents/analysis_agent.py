from typing import List
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service
import json
import re


class AnalysisAgent(BaseAgent):
    def __init__(self, chunk_size=2000, chunk_overlap=200):
        super().__init__("AnalysisAgent", "4.0.0-AdvancedPrompt")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _define_capabilities(self) -> List[str]:
        return ["comprehensive_analysis"]

    def _create_chunks(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap
        return chunks

    def _extract_json_from_response(self, response_text: str) -> dict:
        try:
            if isinstance(response_text, dict):
                return response_text
            
            if isinstance(response_text, str):
                response_text = re.sub(r'```json\s*', '', response_text)
                response_text = re.sub(r'```\s*$', '', response_text)
                
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    return json.loads(json_str)
                return json.loads(response_text.strip())
            return {"entities": [], "relationships": []}
            
        except json.JSONDecodeError as e:
            print(f"     -> JSON parsing failed: {e}")
            print(f"     -> Response content: {response_text[:500]}...")
            return {"entities": [], "relationships": []}
        except Exception as e:
            print(f"     -> Unexpected error in JSON extraction: {e}")
            return {"entities": [], "relationships": []}

    def _validate_entities(self, entities: List[dict]) -> List[dict]:
        validated_entities = []
        required_fields = ['text', 'entity_type', 'confidence', 'anonymization_strategy', 'start_char', 'end_char']
        
        for entity in entities:
            if not isinstance(entity, dict):
                continue
                
            if all(field in entity for field in required_fields):
                try:
                    entity['confidence'] = float(entity.get('confidence', 0.5))
                    entity['start_char'] = int(entity.get('start_char', 0))
                    entity['end_char'] = int(entity.get('end_char', 0))
                    validated_entities.append(entity)
                except (ValueError, TypeError):
                    print(f"     -> Skipping entity with invalid numeric fields: {entity}")
                    continue
            else:
                missing_fields = [f for f in required_fields if f not in entity]
                print(f"     -> Skipping entity missing fields {missing_fields}: {entity}")
        
        return validated_entities

    def process(self, task: AgentTask, progress_callback: callable = None) -> AgentResult:
        full_text = task.input_data.get("full_text")
        if not full_text:
            return self._create_result(task, TaskStatus.FAILED, error_message="No text content provided.")

        system_prompt = """You are an expert security and data privacy analyst specializing in PII detection, security entity identification, and relationship mapping.

Your expertise includes:
- Personal Identifiable Information (PII) detection across multiple jurisdictions (GDPR, CCPA, HIPAA)
- Technical security entity identification (network, IAM, cryptographic elements)
- Entity relationship analysis and data flow mapping
- Risk assessment and anonymization strategy recommendation

CRITICAL REQUIREMENTS:
1. Your response MUST be a valid JSON object with exactly two top-level keys: "entities" and "relationships"
2. Every entity MUST have ALL these fields: "text", "entity_type", "confidence", "anonymization_strategy", "start_char", "end_char"
3. Character indices must be accurate relative to the provided chunk
4. Confidence scores should reflect detection certainty (0.0-1.0)
5. Anonymization strategies should match data sensitivity levels
6. Return ONLY valid JSON - no explanatory text, no markdown formatting, no code blocks"""

        user_prompt_template = """Analyze the following document text to identify ALL PII and security-related entities with their relationships.

## Entity Categories to Detect:

### Personal Identifiable Information (PII):
- **Person Names**: Full names, first/last names, nicknames, initials
- **Contact Information**: Email addresses, phone numbers, fax numbers
- **Physical Addresses**: Street addresses, cities, states, ZIP codes, countries
- **Identification Numbers**: SSN, driver's license, passport, employee ID, customer ID
- **Financial Information**: Credit/debit card numbers, bank accounts, IBAN, SWIFT codes
- **Medical Information**: Patient ID, medical record numbers, health conditions
- **Dates**: Birth dates, hire dates, transaction dates (format: YYYY-MM-DD, MM/DD/YYYY, etc.)
- **Biometric Data**: Fingerprints references, facial recognition data mentions
- **Online Identifiers**: Usernames, user IDs, session IDs, cookies, device IDs

### Technical Security Entities:
- **Network Information**: IP addresses (IPv4/IPv6), MAC addresses, hostnames, domain names, URLs
- **Credentials**: API keys, passwords (even if masked), tokens, certificates
- **Security Configurations**: Firewall rules, IAM policies, security group rules
- **System Information**: Server names, database names, service endpoints, ports
- **Cryptographic Elements**: Encryption keys, hashes, digital signatures
- **Log Entries**: Security events, audit logs, IDS/IPS alerts

Anonymization Strategy Guidelines:
- "Redact": For highly sensitive PII (SSN, credit cards, passwords, medical info, full names with context)
- "Tokenize": For identifiers that need consistency (IDs, hostnames, email domains, IP addresses)
- "Preserve": For non-sensitive or public information (dates without PII context, generic times, public domains)

Return ONLY a valid JSON object in this exact format:
{{"entities": [], "relationships": []}}

Document Text Chunk:
{text_chunk}"""

        try:
            chunks = self._create_chunks(full_text)
            if len(chunks) > 1:
                print(f"     -> Document is large. Splitting into {len(chunks)} chunk(s).")

            all_entities = []
            all_relationships = []
            seen_entities = set()

            for i, chunk in enumerate(chunks):
                print(f"     -> Calling LLM for Detailed Analysis on Chunk {i+1}/{len(chunks)}...")
                chunk_offset = i * (self.chunk_size - self.chunk_overlap)
                user_prompt = user_prompt_template.format(text_chunk=chunk)
                
                try:
                    raw_response = llm_service.get_llm_response(
                        system_prompt,
                        user_prompt,
                        timeout=task.timeout_seconds
                    )
                    
                    # Extract and validate JSON
                    llm_response = self._extract_json_from_response(raw_response)                    
                    chunk_entities = llm_response.get("entities", [])
                    chunk_relationships = llm_response.get("relationships", [])
                    validated_entities = self._validate_entities(chunk_entities)
                    for entity in validated_entities:
                        entity['start_char'] += chunk_offset
                        entity['end_char'] += chunk_offset
                        entity_key = (entity['text'], entity['start_char'])
                        if entity_key not in seen_entities:
                            all_entities.append(entity)
                            seen_entities.add(entity_key)

                    if isinstance(chunk_relationships, list):
                        all_relationships.extend(chunk_relationships)
                    
                    print(f"     -> Chunk {i+1} processed: {len(validated_entities)} entities, {len(chunk_relationships)} relationships")
                    
                except Exception as chunk_error:
                    print(f"     -> Error processing chunk {i+1}: {chunk_error}")
                    continue

            result_data = {
                "entities": all_entities,
                "relationships": all_relationships,
                "analysis_summary": {
                    "entities_found": len(all_entities),
                    "relationships_found": len(all_relationships),
                    "chunks_processed": len(chunks)
                }
            }
            
            print(f"     -> Analysis complete: {len(all_entities)} total entities found")
            return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

        except Exception as e:
            print(f"     -> Critical error in Analysis Agent: {e}")
            return self._create_result(
                task,
                TaskStatus.FAILED,
                error_message=f"An unexpected error occurred in Analysis Agent: {e}"
            )