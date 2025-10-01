from typing import List
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service
import json
import re


class AnalysisAgent(BaseAgent):
    def __init__(self, chunk_size=2000, chunk_overlap=200):
        super().__init__("AnalysisAgent", "5.0.0-EnhancedDetection")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _define_capabilities(self) -> List[str]:
        return ["comprehensive_analysis", "pii_detection", "entity_relationship_mapping"]

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
        
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            normalized_entity = self._normalize_entity_fields(entity)
            required_fields = ['text', 'entity_type', 'confidence', 'anonymization_strategy', 'start_char', 'end_char']
            
            if all(field in normalized_entity for field in required_fields):
                try:
                    normalized_entity['confidence'] = float(normalized_entity.get('confidence', 0.8))
                    normalized_entity['start_char'] = int(normalized_entity.get('start_char', 0))
                    normalized_entity['end_char'] = int(normalized_entity.get('end_char', 0))
                    validated_entities.append(normalized_entity)
                except (ValueError, TypeError):
                    print(f"     -> Skipping entity with invalid numeric fields: {entity}")
                    continue
            else:
                missing_fields = [f for f in required_fields if f not in normalized_entity]
                print(f"     -> Attempting to normalize entity with missing fields {missing_fields}: {entity}")
        
        return validated_entities

    def _normalize_entity_fields(self, entity: dict) -> dict:
        normalized = {}
        
        if 'data' in entity:
            normalized['text'] = entity['data']
        elif 'text' in entity:
            normalized['text'] = entity['text']
        if 'type' in entity:
            normalized['entity_type'] = entity['type']
        elif 'entity_type' in entity:
            normalized['entity_type'] = entity['entity_type']
        if 'anonymizationStrategy' in entity:
            normalized['anonymization_strategy'] = entity['anonymizationStrategy']
        elif 'anonymization_strategy' in entity:
            normalized['anonymization_strategy'] = entity['anonymization_strategy']
        if 'position' in entity:
            try:
                pos = int(entity['position'])
                normalized['start_char'] = pos
                text_length = len(normalized.get('text', ''))
                normalized['end_char'] = pos + text_length
            except (ValueError, TypeError):
                normalized['start_char'] = 0
                normalized['end_char'] = len(normalized.get('text', ''))
        else:
            normalized['start_char'] = entity.get('start_char', 0)
            normalized['end_char'] = entity.get('end_char', len(normalized.get('text', '')))
        normalized['confidence'] = entity.get('confidence', 0.8)
        for key, value in entity.items():
            if key not in ['data', 'type', 'position', 'anonymizationStrategy'] and key not in normalized:
                normalized[key] = value
                
        return normalized

    def process(self, task: AgentTask, progress_callback: callable = None) -> AgentResult:
        full_text = task.input_data.get("full_text")
        if not full_text:
            return self._create_result(task, TaskStatus.FAILED, error_message="No text content provided.")

        system_prompt = """You are an elite security and privacy expert specializing in comprehensive PII detection, data protection, and compliance. Your detection capabilities are state-of-the-art and you NEVER miss sensitive information.

## CRITICAL DETECTION PRINCIPLES:

1. **ZERO TOLERANCE FOR MISSED PII**: Every name, ID, account number, or sensitive identifier MUST be detected.
2. **SECURITY-FIRST MINDSET**: When in doubt, classify as sensitive and recommend tokenization or redaction.
3. **CONTEXTUAL INTELLIGENCE**: Consider the context - even partial information can be sensitive when combined.
4. **COMPLIANCE AWARENESS**: Apply GDPR, CCPA, HIPAA, and PCI-DSS standards strictly.

## DETECTION CATEGORIES AND RULES:

### PERSONAL IDENTIFIERS (ALWAYS TOKENIZE OR REDACT):
- **Names**: ANY human name (first, last, middle, nicknames, initials)
  - Examples: John, Smith, J.S., Johnny, Dr. Smith, Mr. Anderson
  - RULE: If it could be a person's name, it IS sensitive
- **Government IDs**: SSN, passport, driver's license, national ID
  - Pattern examples: XXX-XX-XXXX, 9-digit numbers with context
- **Contact Info**: Email, phone, fax, addresses
  - Include partial emails, obfuscated phones
- **Dates with PII context**: Birth dates, hire dates, medical dates
- **Account Numbers**: Bank, insurance, medical record numbers
- **Biometric References**: Any mention of fingerprints, facial data

### TECHNICAL IDENTIFIERS (CRITICAL SECURITY RISK):
- **AWS Resources**: 
  - IAM ARNs (arn:aws:iam::ACCOUNT:*) - ALWAYS REDACT the account number
  - Access Keys (AKIA*) - ALWAYS REDACT completely
  - Secret Keys - ALWAYS REDACT completely
  - S3 buckets with specific names - TOKENIZE
- **Cloud Resources**:
  - Azure subscription IDs, resource IDs
  - GCP project IDs, service account emails
- **Credentials**:
  - API keys (any service) - ALWAYS REDACT
  - Passwords (even if marked as examples) - ALWAYS REDACT
  - Tokens (JWT, OAuth, session) - ALWAYS REDACT
  - Database connection strings - ALWAYS REDACT sensitive parts
- **Network Info**:
  - Internal IP addresses (10.*, 192.168.*, 172.16-31.*) - TOKENIZE
  - Public IP addresses - TOKENIZE
  - Hostnames revealing organization structure - TOKENIZE
  - URLs with sensitive parameters - REDACT parameters

### ORGANIZATIONAL IDENTIFIERS:
- **Company-Specific**:
  - Internal project names, code names
  - Department names that reveal structure
  - Building names, room numbers (e.g., "211/d Electrical")
  - Employee IDs, badge numbers
- **Infrastructure Names**:
  - Server names, database names
  - Service endpoints specific to organization
  - Custom application names

## ANONYMIZATION STRATEGY RULES:

**"Redact"** - Use for:
- All human names without exception
- SSN, credit cards, passwords, API keys
- Medical information, health conditions
- AWS account numbers in ARNs
- Any credential or secret

**"Tokenize"** - Use for:
- IDs that need consistency (employee ID, customer ID)
- IP addresses, hostnames
- Email addresses, phone numbers
- AWS resource names (keeping structure)
- Building/room identifiers

**"Preserve"** - Use ONLY for:
- Public information (well-known public domains like google.com)
- Generic dates without PII association
- Technical terms without specific values
- AWS service names (not resource names)

## VALIDATION CHECKS:
1. Have I identified EVERY person's name?
2. Have I caught ALL account numbers and IDs?
3. Have I found ALL credentials and secrets?
4. Are AWS ARNs properly identified with account numbers marked for redaction?
5. Are building/location identifiers marked for tokenization?

## CONTEXT CLUES TO ALWAYS CHECK:
- "Name:", "Contact:", "ID:", "Account:", "ARN:", "Key:", "Token:"
- Any field that could contain personal or sensitive data
- Visitor logs, attendance sheets, access logs
- Configuration files, infrastructure code
- Any human-readable identifier

CRITICAL: Return ONLY valid JSON with "entities" and "relationships" arrays. Every entity needs all required fields.

## REQUIRED JSON FORMAT:
{
  "entities": [
    {
      "text": "The actual text found",
      "entity_type": "person_name|email|phone|aws_account_id|etc",
      "confidence": 0.95,
      "anonymization_strategy": "Redact|Tokenize|Preserve",
      "start_char": 123,
      "end_char": 135
    }
  ],
  "relationships": [
    {
      "source": "entity_text_1",
      "target": "entity_text_2",
      "relationship_type": "belongs_to|associated_with|contains"
    }
  ]
}"""

        user_prompt_template = """Analyze this document with MAXIMUM VIGILANCE for ALL sensitive information. You must catch EVERYTHING.

## Your Task:
1. Identify EVERY piece of PII and sensitive data
2. Provide accurate character positions
3. Assign appropriate anonymization strategies
4. Map relationships between entities

## Special Attention Areas:
- AWS ARNs: The account number (12 digits after arn:aws:iam::) is ALWAYS sensitive
- Names in ANY context (visitor logs, email addresses, documents)
- Building/room identifiers (like "211/d Electrical") are organizational data - TOKENIZE
- ANY credential, key, or token regardless of context
- Infrastructure names that reveal internal structure

## Examples of What You MUST Detect:

1. AWS ARN: "arn:aws:iam::123456789012:role/TestRole"
   - Entity: "123456789012" (AWS Account ID) - Redact
   - Entity: "TestRole" (Role Name) - Tokenize

2. Building Info: "211/d Electrical"
   - Entity: "211/d Electrical" (Building/Room Identifier) - Tokenize

3. Visitor Log with names: "John Smith, Jane Doe, Bob Wilson, Alice Brown"
   - ALL four names must be detected and marked for redaction

4. Email: "john.doe@company.com"
   - Entity: "john.doe" (Personal Identifier) - Redact
   - Entity: "@company.com" (Domain) - Evaluate if internal (Tokenize) or public (Preserve)

## Document Text to Analyze:
{text_chunk}

Remember: 
- NEVER miss a name or ID
- When uncertain, err on the side of security
- Building/location identifiers are sensitive organizational data
- AWS account numbers are ALWAYS sensitive
- Return ONLY valid JSON with exact field names: "text", "entity_type", "confidence", "anonymization_strategy", "start_char", "end_char"
- Use accurate character positions for start_char and end_char
- Confidence should be a decimal between 0.0 and 1.0"""

        try:
            chunks = self._create_chunks(full_text)
            if len(chunks) > 1:
                print(f"     -> Document is large. Splitting into {len(chunks)} chunk(s).")

            all_entities = []
            all_relationships = []
            seen_entities = set()

            for i, chunk in enumerate(chunks):
                print(f"     -> Performing deep PII analysis on Chunk {i+1}/{len(chunks)}...")
                chunk_offset = i * (self.chunk_size - self.chunk_overlap)
                user_prompt = user_prompt_template.format(text_chunk=chunk)
                
                try:
                    raw_response = llm_service.get_llm_response(
                        system_prompt,
                        user_prompt,
                        timeout=task.timeout_seconds
                    )
                    
                    llm_response = self._extract_json_from_response(raw_response)                    
                    chunk_entities = llm_response.get("entities", [])
                    chunk_relationships = llm_response.get("relationships", [])
                    validated_entities = self._apply_enhanced_validation(
                        self._validate_entities(chunk_entities), 
                        chunk
                    )
                    
                    for entity in validated_entities:
                        entity['start_char'] += chunk_offset
                        entity['end_char'] += chunk_offset
                        entity_key = (entity['text'], entity['start_char'])
                        if entity_key not in seen_entities:
                            all_entities.append(entity)
                            seen_entities.add(entity_key)

                    if isinstance(chunk_relationships, list):
                        all_relationships.extend(chunk_relationships)
                    
                    print(f"     -> Chunk {i+1}: Found {len(validated_entities)} entities, {len(chunk_relationships)} relationships")
                    
                except Exception as chunk_error:
                    print(f"     -> Error processing chunk {i+1}: {chunk_error}")
                    continue
            all_entities = self._final_validation_pass(all_entities, full_text)
            
            result_data = {
                "entities": all_entities,
                "relationships": all_relationships,
                "analysis_summary": {
                    "entities_found": len(all_entities),
                    "relationships_found": len(all_relationships),
                    "chunks_processed": len(chunks),
                    "high_risk_entities": len([e for e in all_entities if e.get('confidence', 0) > 0.9])
                }
            }
            
            print(f"     -> Analysis complete: {len(all_entities)} total entities detected")
            print(f"     -> High-risk entities: {result_data['analysis_summary']['high_risk_entities']}")
            
            return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

        except Exception as e:
            print(f"     -> Critical error in Analysis Agent: {e}")
            return self._create_result(
                task,
                TaskStatus.FAILED,
                error_message=f"An unexpected error occurred in Analysis Agent: {e}"
            )

    def _apply_enhanced_validation(self, entities: List[dict], chunk_text: str) -> List[dict]:
        patterns = {
            'aws_arn_account': (r'arn:aws:[^:]+::(\d{12}):', 'aws_account_id'),
            'room_building': (r'\b\d{1,4}/[a-zA-Z]\s+\w+\b', 'building_identifier'),
            'person_name': (r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', 'person_name'),
            'email_name': (r'([a-zA-Z]+[._]?[a-zA-Z]+)@', 'email_username'),
        }
        
        existing_texts = {e['text'] for e in entities}
        
        for pattern_name, (pattern, entity_type) in patterns.items():
            matches = re.finditer(pattern, chunk_text)
            for match in matches:
                matched_text = match.group(1) if match.groups() else match.group(0)                
                if matched_text in existing_texts:
                    continue
                if entity_type in ['person_name', 'aws_account_id', 'email_username']:
                    strategy = 'Redact'
                elif entity_type in ['building_identifier']:
                    strategy = 'Tokenize'
                else:
                    strategy = 'Tokenize'
                
                new_entity = {
                    'text': matched_text,
                    'entity_type': entity_type,
                    'confidence': 0.85,
                    'anonymization_strategy': strategy,
                    'start_char': match.start(1) if match.groups() else match.start(0),
                    'end_char': match.end(1) if match.groups() else match.end(0)
                }
                
                entities.append(new_entity)
                existing_texts.add(matched_text)
                print(f"     -> Pattern detection added: {matched_text} ({entity_type})")
        
        for entity in entities:
            entity_type = entity.get('entity_type', '').lower()
            current_strategy = entity.get('anonymization_strategy', '')
            if any(keyword in entity_type for keyword in ['name', 'person', 'account', 'email', 'phone']):
                if current_strategy != 'Redact':
                    entity['anonymization_strategy'] = 'Redact'
            elif any(keyword in entity_type for keyword in ['building', 'room', 'identifier']):
                if current_strategy == 'Preserve':
                    entity['anonymization_strategy'] = 'Tokenize'
                    
        return entities

    def _final_validation_pass(self, entities: List[dict], full_text: str) -> List[dict]:
        critical_patterns = [
            (r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', 'potential_name'),
            (r'\d{3}-\d{2}-\d{4}', 'potential_ssn'),
            (r'arn:aws:[^:]+::\d{12}:', 'aws_arn'),
        ]
        
        for pattern, pattern_type in critical_patterns:
            matches = re.finditer(pattern, full_text)
            for match in matches:
                text = match.group()
                already_detected = any(
                    e['start_char'] <= match.start() < e['end_char'] 
                    for e in entities
                )
                if not already_detected and pattern_type == 'potential_name':
                    if not any(word in text.lower() for word in ['street', 'road', 'avenue', 'drive']):
                        print(f"     -> Warning: Potential missed name: {text}")
        
        return entities