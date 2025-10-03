from typing import List, Dict, Optional, Any
import hashlib
import json
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from ...rag.retrieval import RAGRetriever

class AnonymizationAgent(BaseAgent):
    def __init__(self, rag_retriever: Optional[RAGRetriever] = None):
        super().__init__("AnonymizationAgent", "2.1.0-Robust")
        self.anonymization_registry = {}
        self.rag_retriever = rag_retriever

    def _define_capabilities(self) -> List[str]:
        return ["anonymization", "tokenization", "redaction", "data_masking"]

    def process(self, task: AgentTask, progress_callback: callable = None) -> AgentResult:
        final_data = task.input_data
        full_text = final_data.get("full_text", "")
        entities = final_data.get("entities", [])

        if not entities:
            return self._create_result(task, TaskStatus.COMPLETED, data=final_data)      
        anonymized_text = full_text
        rag_guidance = self._fetch_rag_strategies(entities)
        entities_to_anonymize = sorted(
            list({e.get("text"): e for e in entities if e.get("anonymization_strategy") in ["Redact", "Tokenize"]}.values()),
            key=lambda x: len(x.get("text", "")),
            reverse=True
        )

        for entity in entities_to_anonymize:
            strategy = entity.get("anonymization_strategy") or "Preserve"
            if (not strategy or strategy == "Preserve") and rag_guidance:
                guidance = rag_guidance.get(entity.get("entity_type"))
                if guidance:
                    strategy = guidance.get("suggested_strategy", strategy)
                    entity["anonymization_strategy"] = strategy
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
        if rag_guidance:
            final_data["anonymization_guidance"] = rag_guidance
        
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

    def _fetch_rag_strategies(self, entities: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
        if not self.rag_retriever:
            return {}

        guidance: Dict[str, Dict[str, any]] = {}
        unique_types = {entity.get("entity_type") for entity in entities if entity.get("entity_type")}

        for entity_type in unique_types:
            try:
                strategies = self.rag_retriever.get_anonymization_strategy(
                    entity_type=entity_type,
                    use_case="compliance",
                    top_k=1
                )
                if strategies:
                    strategy_doc = strategies[0]
                    metadata = strategy_doc.get("metadata", {}) or {}
                    suggested = metadata.get("strategy_name")
                    if not suggested:
                        suggested = metadata.get("strategy", "")

                    guidance[entity_type] = {
                        "document": strategy_doc.get("document"),
                        "metadata": metadata,
                        "relevance_score": strategy_doc.get("relevance_score"),
                        "suggested_strategy": metadata.get("strategy_name") or metadata.get("strategy") or "Tokenize"
                    }
            except Exception as exc:
                print(f"     -> WARNING: Failed to retrieve anonymization guidance for {entity_type}: {exc}")

        return guidance