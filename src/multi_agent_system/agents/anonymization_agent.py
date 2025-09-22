from typing import List
import hashlib
import json
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus

class AnonymizationAgent(BaseAgent):
    def __init__(self):
        super().__init__("AnonymizationAgent", "2.0.0")
        self.anonymization_registry = {}

    def _define_capabilities(self) -> List[str]:
        return ["anonymization", "tokenization", "redaction", "data_masking"]

    def process(self, task: AgentTask) -> AgentResult:
        entities = task.input_data.get("entities", [])
        full_text = task.input_data.get("full_text", "")
        if not entities:
            return self._create_result(task, TaskStatus.COMPLETED, data={"anonymized_text": full_text, "anonymization_summary": {}})
        
        anonymization_summary = { "redacted": 0, "tokenized": 0, "preserved": 0, "total": 0 }
        anonymized_text = full_text
        processed_entities = []
        unique_entities = sorted(
            list({json.dumps(e, sort_keys=True) for e in entities}), 
            key=lambda x: len(json.loads(x)['text']), 
            reverse=True
        )

        for entity_json in unique_entities:
            entity = json.loads(entity_json)           
            if not isinstance(entity, dict) or 'text' not in entity or 'anonymization_strategy' not in entity:
                continue
            strategy = entity.get("anonymization_strategy", "Preserve")
            original_text = entity["text"]

            if strategy == "Preserve":
                anonymization_summary["preserved"] += 1
                entity["anonymized_text"] = original_text
                processed_entities.append(entity)
                continue

            anonymized_replacement = original_text
            if strategy == "Redact":
                anonymized_replacement = "[REDACTED]"
                anonymization_summary["redacted"] += 1
            elif strategy == "Tokenize":
                entity_type = entity.get("entity_type", "ENTITY")
                anonymized_replacement = self._tokenize_text(original_text, entity_type)
                anonymization_summary["tokenized"] += 1
            
            anonymized_text = anonymized_text.replace(original_text, anonymized_replacement, 1)           
            entity["anonymized_text"] = anonymized_replacement
            processed_entities.append(entity)          
        anonymization_summary["total"] = len(processed_entities)
        result_data = {
            "anonymized_text": anonymized_text,
            "anonymized_entities": processed_entities,
            "anonymization_summary": anonymization_summary,
            "registry_size": len(self.anonymization_registry)
        }
        
        return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

    def _tokenize_text(self, text: str, entity_type: str) -> str:
        if text in self.anonymization_registry:
            return self.anonymization_registry[text]
        token_prefix = entity_type.upper().replace(" ", "_")       
        hash_obj = hashlib.sha256(text.encode())
        hash_hex = hash_obj.hexdigest()[:8]        
        token = f"[{token_prefix}_{hash_hex}]"
        self.anonymization_registry[text] = token
        return token