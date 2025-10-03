from typing import List, Dict, Any, Optional
from .vector_store import VectorStoreManager
import json

class RAGRetriever:
    def __init__(self, vector_store: VectorStoreManager = None):
        self.vector_store = vector_store or VectorStoreManager()
    
    def get_entity_patterns(
        self,
        document_type: str,
        text_sample: str,
        category: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        query = f"Document type: {document_type}. Detect entities in: {text_sample[:300]}"
        where_filter = {}
        if category:
            where_filter["category"] = category
        results = self.vector_store.query(
            collection_name="entity_patterns",
            query_text=query,
            n_results=top_k,
            where=where_filter if where_filter else None
        )
        
        patterns = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                relevance_score = 1 - results['distances'][0][i]
                if relevance_score < 0.4:
                    print(f"[RAGRetriever] Skipping low-relevance pattern (score: {relevance_score:.3f})")
                    continue
                
                pattern = {
                    "document": doc,
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i],
                    "relevance_score": relevance_score
                }
                patterns.append(pattern)
        
        return patterns
    
    def get_contextual_rules(
        self,
        entity_types: List[str],
        text_context: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        query = f"Contextual rules for {', '.join(entity_types)} in context: {text_context[:200]}"       
        results = self.vector_store.query(
            collection_name="contextual_patterns",
            query_text=query,
            n_results=top_k
        )
        
        rules = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                relevance_score = 1 - results['distances'][0][i]
                if relevance_score < 0.3:
                    continue
                
                rule = {
                    "document": doc,
                    "metadata": results['metadatas'][0][i],
                    "relevance_score": relevance_score
                }
                rules.append(rule)       
        return rules
    
    def get_compliance_requirements(
        self,
        frameworks: List[str],
        entity_types: List[str],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        query = f"Compliance requirements for {', '.join(frameworks)} covering {', '.join(entity_types)}"
        
        results = self.vector_store.query(
            collection_name="compliance_rules",
            query_text=query,
            n_results=top_k
        )
        
        requirements = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                relevance_score = 1 - results['distances'][0][i]
                if relevance_score < 0.3:
                    continue               
                req = {
                    "document": doc,
                    "metadata": results['metadatas'][0][i],
                    "relevance_score": relevance_score
                }
                requirements.append(req)       
        return requirements
    
    def get_similar_scenarios(
        self,
        document_type: str,
        text_sample: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        query = f"Similar scenario to {document_type}: {text_sample[:300]}"        
        results = self.vector_store.query(
            collection_name="complex_scenarios",
            query_text=query,
            n_results=top_k
        )        
        scenarios = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                scenario = {
                    "document": doc,
                    "metadata": results['metadatas'][0][i],
                    "relevance_score": 1 - results['distances'][0][i]
                }
                scenarios.append(scenario)       
        return scenarios
    
    def get_anonymization_strategy(
        self,
        entity_type: str,
        use_case: str,
        reversible: Optional[bool] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        query = f"Anonymization strategy for {entity_type} in {use_case} use case"       
        where_filter = {}
        if reversible is not None:
            where_filter["reversible"] = reversible        
        results = self.vector_store.query(
            collection_name="anonymization_strategies",
            query_text=query,
            n_results=top_k,
            where=where_filter if where_filter else None
        )
        
        strategies = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                strategy = {
                    "document": doc,
                    "metadata": results['metadatas'][0][i],
                    "relevance_score": 1 - results['distances'][0][i]
                }
                strategies.append(strategy)       
        return strategies
    
    def get_validation_rules(
        self,
        entity_type: str
    ) -> Optional[Dict[str, Any]]:
        results = self.vector_store.query(
            collection_name="validation_rules",
            query_text=f"Validation rules for {entity_type}",
            n_results=1
        )
        
        if results['documents'] and len(results['documents']) > 0 and len(results['documents'][0]) > 0:
            return {
                "document": results['documents'][0][0],
                "metadata": results['metadatas'][0][0]
            }
        
        return None
    
    def get_comprehensive_context(
        self,
        document_type: str,
        text_sample: str,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        context = {
            "document_type": document_type,
            "entity_patterns": self.get_entity_patterns(document_type, text_sample, top_k=15),
            "similar_scenarios": self.get_similar_scenarios(document_type, text_sample, top_k=2)
        }
        
        if entity_types:
            context["contextual_rules"] = self.get_contextual_rules(entity_types, text_sample, top_k=5)
            context["compliance_requirements"] = self.get_compliance_requirements(
                frameworks=["GDPR", "HIPAA", "PCI_DSS"],
                entity_types=entity_types,
                top_k=3
            )
        
        return context