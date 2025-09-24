from typing import List
import hashlib
import json
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus

class AnonymizationAgent(BaseAgent):
    def __init__(self):
        super().__init__("AnonymizationAgent", "2.1.0-Robust")
        self.anonymization_registry = {}

    def _define_capabilities(self) -> List[str]:
        return ["anonymization", "tokenization", "redaction", "data_masking"]

    def process(self, task: AgentTask, progress_callback: callable = None) -> AgentResult:
        final_data = task.input_data
        full_text = final_data.get("full_text", "")
        entities = final_data.get("entities", [])

        if not entities:
            return self._create_result(task, TaskStatus.COMPLETED, data=final_data)      
        anonymized_text = full_text
        entities_to_anonymize = sorted(
            list({e.get("text"): e for e in entities if e.get("anonymization_strategy") in ["Redact", "Tokenize"]}.values()),
            key=lambda x: len(x.get("text", "")),
            reverse=True
        )

        for entity in entities_to_anonymize:
            strategy = entity.get("anonymization_strategy")
            original_text = entity.get("text")
            if not original_text: continue
            anonymized_replacement = original_text
            if strategy == "Redact":
                anonymized_replacement = "[REDACTED]"
            elif strategy == "Tokenize":
                entity_type = entity.get("entity_type", "ENTITY")
                anonymized_replacement = self._tokenize_text(original_text, entity_type)
            
            anonymized_text = anonymized_text.replace(original_text, anonymized_replacement)

        for entity in entities:
            strategy = entity.get("anonymization_strategy")
            if strategy == "Redact":
                entity["anonymized_text"] = "[REDACTED]"
            elif strategy == "Tokenize":
                entity["anonymized_text"] = self._tokenize_text(entity.get("text", ""), entity.get("entity_type", "ENTITY"))
            else:
                entity["anonymized_text"] = entity.get("text", "")

        anonymization_summary = {
            "redacted": sum(1 for e in entities if e.get("anonymization_strategy") == "Redact"),
            "tokenized": sum(1 for e in entities if e.get("anonymization_strategy") == "Tokenize"),
            "preserved": sum(1 for e in entities if e.get("anonymization_strategy") == "Preserve"),
        }
        anonymization_summary["total"] = sum(anonymization_summary.values())
        final_data["anonymized_text"] = anonymized_text
        final_data["anonymization_summary"] = anonymization_summary
        
        return self._create_result(task, TaskStatus.COMPLETED, data=final_data)

    def _tokenize_text(self, text: str, entity_type: str) -> str:
        if text in self.anonymization_registry:
            return self.anonymization_registry[text]
        
        token_prefix = entity_type.upper().replace(" ", "_").replace("(", "").replace(")", "")        
        hash_obj = hashlib.sha256(text.encode())
        hash_hex = hash_obj.hexdigest()[:8]      
        token = f"[{token_prefix}_{hash_hex}]"
        self.anonymization_registry[text] = token
        return token