from typing import List
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service

class AnalysisAgent(BaseAgent):
    def __init__(self, chunk_size=2000, chunk_overlap=200):
        super().__init__("AnalysisAgent", "3.0.0-Chunking")
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

    def process(self, task: AgentTask) -> AgentResult:
        full_text = task.input_data.get("full_text")
        if not full_text:
            return self._create_result(task, TaskStatus.FAILED, error_message="No text content provided.")

        system_prompt = """
        You are an expert security and data privacy analyst. Your task is to perform a comprehensive analysis of the provided text.
        You must identify PII entities, technical security entities, and the relationships between them.
        Your response MUST be a single, valid JSON object with two top-level keys: "entities" and "relationships".
        Every entity in the "entities" list MUST have the following keys: "text", "entity_type", "confidence", "anonymization_strategy", "start_char", and "end_char".
        """

        user_prompt_template = """
        Analyze the following document text. Find all PII and security entities and their relationships.

        - For each entity, provide:
          - "text": The exact text of the entity.
          - "entity_type": A specific type like "Person", "Email Address", "Date", "Time", "IP Address", "Hostname".
          - "confidence": A float from 0.0 to 1.0.
          - "anonymization_strategy": Suggest "Redact" for sensitive PII, "Tokenize" for identifiers, or "Preserve" for non-sensitive data.
          - "start_char": The starting character index of the entity IN THE PROVIDED CHUNK.
          - "end_char": The ending character index of the entity IN THE PROVIDED CHUNK.

        - For each relationship, provide:
          - "source": The text of the source entity.
          - "target": The text of the target entity.
          - "description": A brief explanation of their connection.

        Return a single JSON object with the keys "entities" and "relationships".

        Document Text Chunk:
        ---
        {text_chunk}
        ---
        """
        
        try:
            chunks = self._create_chunks(full_text)
            print(f"     -> Document is large. Splitting into {len(chunks)} chunk(s).")
            all_entities = []
            all_relationships = []
            seen_entities = set()

            for i, chunk in enumerate(chunks):
                print(f"     -> Calling LLM for Detailed Analysis on Chunk {i+1}/{len(chunks)}...")
                # Calculate the offset of the current chunk within the full document
                chunk_offset = i * (self.chunk_size - self.chunk_overlap)               
                user_prompt = user_prompt_template.format(text_chunk=chunk)
                llm_response = llm_service.get_llm_response(system_prompt, user_prompt, timeout=task.timeout_seconds)
                chunk_entities = llm_response.get("entities", [])
                chunk_relationships = llm_response.get("relationships", [])

                for entity in chunk_entities:
                    if not all(k in entity for k in ['start_char', 'end_char', 'text']):
                        continue                   
                    entity['start_char'] += chunk_offset
                    entity['end_char'] += chunk_offset                  
                    # Deduplicate entities found in overlapping regions
                    entity_key = (entity['text'], entity['start_char'])
                    if entity_key not in seen_entities:
                        all_entities.append(entity)
                        seen_entities.add(entity_key)

                all_relationships.extend(chunk_relationships)

            result_data = {
                "entities": all_entities,
                "relationships": all_relationships,
                "analysis_summary": {
                    "entities_found": len(all_entities),
                    "relationships_found": len(all_relationships)
                }
            }
            return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

        except (ConnectionError, ValueError) as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=str(e))
        except Exception as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=f"An unexpected error occurred in Analysis Agent: {e}")