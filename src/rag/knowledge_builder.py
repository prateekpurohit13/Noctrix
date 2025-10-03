import json
from pathlib import Path
from typing import Dict, Any, List, Iterable
from .vector_store import VectorStoreManager
import hashlib

class KnowledgeBaseBuilder:
    def __init__(self, dataset_path: str = "dataset.json", vector_store: VectorStoreManager = None):
        self.dataset_path = Path(dataset_path)
        self.vector_store = vector_store or VectorStoreManager()
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            self.dataset = json.load(f)
        
        print(f"[KnowledgeBuilder] Loaded dataset: {self.dataset['metadata']['dataset_version']}")
        print(f"[KnowledgeBuilder] Total entity types: {self.dataset['metadata']['total_entity_types']}")

    @staticmethod
    def _flatten_strings(value: Any) -> List[str]:
        results: List[str] = []

        if value is None:
            return results
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                results.append(cleaned)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                results.extend(KnowledgeBaseBuilder._flatten_strings(item))
        elif isinstance(value, dict):
            for item in value.values():
                results.extend(KnowledgeBaseBuilder._flatten_strings(item))

        return results

    @staticmethod
    def _normalize_patterns(patterns: Any) -> List[str]:
        normalized = []
        if patterns is None:
            return normalized

        if isinstance(patterns, str):
            normalized.append(patterns)
        elif isinstance(patterns, dict):
            for value in patterns.values():
                normalized.extend(KnowledgeBaseBuilder._normalize_patterns(value))
        elif isinstance(patterns, Iterable):
            for item in patterns:
                normalized.extend(KnowledgeBaseBuilder._normalize_patterns(item))

        return [p for p in normalized if isinstance(p, str) and p.strip()]
    
    def build_all(self, reset_existing: bool = False):
        if reset_existing:
            print("[KnowledgeBuilder] Resetting existing collections...")
            for collection_name in self.vector_store.collections.keys():
                self.vector_store.reset_collection(collection_name)
        
        print("[KnowledgeBuilder] Building knowledge base...")
        
        self.build_entity_patterns()
        self.build_compliance_rules()
        self.build_contextual_patterns()
        self.build_complex_scenarios()
        self.build_anonymization_strategies()
        self.build_validation_rules()
        
        stats = self.vector_store.get_stats()
        print("\n[KnowledgeBuilder] Build Complete! Statistics:")
        for name, count in stats.items():
            print(f"  - {name}: {count} documents")
    
    def build_entity_patterns(self):
        print("[KnowledgeBuilder] Building entity_patterns collection...")        
        documents = []
        metadatas = []
        ids = []
        
        for category_data in self.dataset['entity_definitions']:
            category = category_data['category']
            subcategory = category_data.get('subcategory', 'general')           
            entities = category_data.get('entities', [])
            
            for entity in entities:
                entity_type = entity['entity_type']
                patterns = self._normalize_patterns(entity.get('patterns'))
                examples = self._flatten_strings(entity.get('examples'))
                context_clues = self._flatten_strings(entity.get('context_clues'))
                compliance_details = self._flatten_strings(entity.get('compliance_requirements'))
                anonymization_details = []
                if 'anonymization_strategies' in entity:
                    anonymization_details = [
                        f"{k}: {v}" for k, v in entity['anonymization_strategies'].items()
                        if isinstance(v, str)
                    ]
                doc_parts = [
                    f"Entity Type: {entity_type}",
                    f"Category: {category}",
                    f"Subcategory: {subcategory}",
                    f"Risk Level: {entity.get('risk_level', 'unknown')}"
                ]                
                # Add patterns
                if patterns:
                    doc_parts.append(f"Patterns: {' | '.join(patterns)}")                
                # Add context clues
                if context_clues:
                    doc_parts.append(f"Context Clues: {', '.join(context_clues)}")                
                # Add examples
                if examples:
                    doc_parts.append(f"Examples: {', '.join(examples[:5])}")
                if anonymization_details:
                    doc_parts.append(f"Anonymization Guidance: {', '.join(anonymization_details)}")                
                # Add compliance info
                if compliance_details:
                    doc_parts.append(f"Compliance: {', '.join(compliance_details)}")            
                document = "\n".join(doc_parts)               
                # Create metadata
                metadata = {
                    "entity_type": entity_type,
                    "category": category,
                    "subcategory": subcategory,
                    "risk_level": entity.get('risk_level', 'unknown'),
                    "patterns": json.dumps(patterns),
                    "context_clues": json.dumps(context_clues),
                    "examples": json.dumps(examples),
                    "compliance": json.dumps(compliance_details),
                    "has_validation": 'validation_rules' in entity
                }               
                # Generate unique ID
                doc_id = f"entity_{hashlib.md5(entity_type.encode()).hexdigest()[:12]}"               
                documents.append(document)
                metadatas.append(metadata)
                ids.append(doc_id)
        
        self.vector_store.add_documents(
            collection_name="entity_patterns",
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def build_compliance_rules(self):
        print("[KnowledgeBuilder] Building compliance_rules collection...")       
        documents = []
        metadatas = []
        ids = []        
        compliance_data = self.dataset.get('compliance_mappings', {})
        
        for framework, rules in compliance_data.items():
            doc_parts = [f"Framework: {framework}"]            
            for rule_type, items in rules.items():
                if isinstance(items, list):
                    items_str = ", ".join(items)
                    doc_parts.append(f"{rule_type}: {items_str}")           
            document = "\n".join(doc_parts)
            
            metadata = {
                "framework": framework,
                "rule_types": json.dumps(list(rules.keys())),
                "total_rules": sum(len(v) if isinstance(v, list) else 0 for v in rules.values())
            }           
            doc_id = f"compliance_{framework.lower().replace(' ', '_')}"           
            documents.append(document)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        if documents:
            self.vector_store.add_documents(
                collection_name="compliance_rules",
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
    
    def build_contextual_patterns(self):
        print("[KnowledgeBuilder] Building contextual_patterns collection...")        
        documents = []
        metadatas = []
        ids = []        
        contextual_rules = self.dataset.get('contextual_detection_rules', [])       
        for rule in contextual_rules:
            rule_id = rule['rule_id']           
            doc_parts = [
                f"Rule ID: {rule_id}",
                f"Entity: {rule.get('entity', rule.get('entities', 'N/A'))}"
            ]           
            if 'positive_indicators' in rule:
                pos_str = ", ".join(rule['positive_indicators'])
                doc_parts.append(f"Positive Indicators: {pos_str}")
            
            if 'negative_indicators' in rule:
                neg_str = ", ".join(rule['negative_indicators'])
                doc_parts.append(f"Negative Indicators: {neg_str}")
            
            if 'indicators' in rule:
                ind_str = ", ".join(rule['indicators'])
                doc_parts.append(f"Indicators: {ind_str}")
            
            document = "\n".join(doc_parts)
            
            metadata = {
                "rule_id": rule_id,
                "entity": json.dumps(rule.get('entity', rule.get('entities', []))),
                "has_positive": 'positive_indicators' in rule,
                "has_negative": 'negative_indicators' in rule,
                "classification": rule.get('classification', 'general')
            }
            
            doc_id = f"context_{rule_id}"           
            documents.append(document)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        if documents:
            self.vector_store.add_documents(
                collection_name="contextual_patterns",
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
    
    def build_complex_scenarios(self):
        print("[KnowledgeBuilder] Building complex_scenarios collection...")       
        documents = []
        metadatas = []
        ids = []        
        scenarios = self.dataset.get('complex_scenarios', [])
        
        for scenario in scenarios:
            scenario_id = scenario['scenario_id']           
            doc_parts = [
                f"Scenario: {scenario_id}",
                f"Description: {scenario['description']}",
                f"Input Text Sample: {scenario['input_text'][:500]}..."
            ]
            
            expected = scenario.get('expected_entities', [])
            entity_types = list(set(e['type'] for e in expected))
            doc_parts.append(f"Expected Entity Types: {', '.join(entity_types)}")            
            document = "\n".join(doc_parts)           
            metadata = {
                "scenario_id": scenario_id,
                "description": scenario['description'],
                "entity_count": len(expected),
                "entity_types": json.dumps(entity_types),
                "has_anonymized_output": 'anonymized_output' in scenario
            }            
            doc_id = f"scenario_{scenario_id}"           
            documents.append(document)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        if documents:
            self.vector_store.add_documents(
                collection_name="complex_scenarios",
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
    
    def build_anonymization_strategies(self):
        print("[KnowledgeBuilder] Building anonymization_strategies collection...")       
        documents = []
        metadatas = []
        ids = []        
        strategies = self.dataset.get('anonymization_strategies', {})
        
        for strategy_name, strategy_data in strategies.items():
            doc_parts = [
                f"Strategy: {strategy_name}",
                f"Description: {strategy_data['description']}"
            ]           
            # Add examples
            if 'examples' in strategy_data:
                examples_str = ", ".join([f"{k}: {v}" for k, v in strategy_data['examples'].items()])
                doc_parts.append(f"Examples: {examples_str}")           
            # Add use cases
            if 'use_cases' in strategy_data:
                use_cases_str = ", ".join(strategy_data['use_cases'])
                doc_parts.append(f"Use Cases: {use_cases_str}")           
            document = "\n".join(doc_parts)
            
            metadata = {
                "strategy_name": strategy_name,
                "reversible": strategy_data.get('reversible', False),
                "use_cases": json.dumps(strategy_data.get('use_cases', [])),
                "example_count": len(strategy_data.get('examples', {}))
            }
            
            doc_id = f"strategy_{strategy_name}"           
            documents.append(document)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        if documents:
            self.vector_store.add_documents(
                collection_name="anonymization_strategies",
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
    
    def build_validation_rules(self):
        print("[KnowledgeBuilder] Building validation_rules collection...")       
        documents = []
        metadatas = []
        ids = []       
        validation_data = self.dataset.get('validation_rules', {})        
        for entity_type, rules in validation_data.items():
            doc_parts = [f"Entity Type: {entity_type}"]            
            for rule_name, rule_value in rules.items():
                if isinstance(rule_value, (str, bool)):
                    doc_parts.append(f"{rule_name}: {rule_value}")
                elif isinstance(rule_value, list):
                    doc_parts.append(f"{rule_name}: {', '.join(map(str, rule_value))}")
                elif isinstance(rule_value, dict):
                    items_str = ", ".join([f"{k}: {v}" for k, v in rule_value.items()])
                    doc_parts.append(f"{rule_name}: {items_str}")            
            document = "\n".join(doc_parts)
            
            metadata = {
                "entity_type": entity_type,
                "rule_count": len(rules),
                "has_format": 'format' in rules,
                "has_test_values": 'test_values' in rules or 'test_cards' in rules
            }           
            doc_id = f"validation_{entity_type}"           
            documents.append(document)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        if documents:
            self.vector_store.add_documents(
                collection_name="validation_rules",
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )