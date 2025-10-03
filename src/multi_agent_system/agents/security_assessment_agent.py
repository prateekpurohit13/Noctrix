from typing import List, Dict, Any, Optional
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service
import json
from ...rag.retrieval import RAGRetriever

class SecurityAssessmentAgent(BaseAgent):
    def __init__(self, rag_retriever: Optional[RAGRetriever] = None):
        super().__init__("SecurityAssessmentAgent", "2.0.0-Enhanced")
        self.rag_retriever = rag_retriever

    def _define_capabilities(self) -> List[str]:
        return ["security_risk_assessment", "compliance_mapping", "threat_detection"]

    @staticmethod
    def _format_guidance_section(title: str, rows: List[str]) -> str:
        if not rows:
            return ""
        body = "\n".join(f"- {row}" for row in rows)
        return f"## {title}\n{body}"

    def _build_rag_guidance(
        self,
        entity_types_found: List[str],
        rag_context_from_pipeline: Dict[str, Any]
    ) -> str:
        sections: List[str] = []
        compliance_rows: List[str] = []
        contextual_rows: List[str] = []

        if self.rag_retriever:
            try:
                compliance_hits = self.rag_retriever.get_compliance_requirements(
                    frameworks=["GDPR", "HIPAA", "PCI_DSS"],
                    entity_types=entity_types_found,
                    top_k=5
                )
                for hit in compliance_hits:
                    doc = hit.get("document", "").replace("\n", " ")
                    compliance_rows.append(doc)
            except Exception as exc:
                print(f"     -> WARNING: Compliance retrieval failed: {exc}")

            try:
                contextual_hits = self.rag_retriever.get_contextual_rules(
                    entity_types=entity_types_found,
                    text_context=json.dumps(entity_types_found),
                    top_k=5
                )
                for rule in contextual_hits:
                    doc = rule.get("document", "").replace("\n", " ")
                    contextual_rows.append(doc)
            except Exception as exc:
                print(f"     -> WARNING: Contextual rule retrieval failed: {exc}")

        if rag_context_from_pipeline:
            for item in rag_context_from_pipeline.get("compliance_requirements", []) or []:
                doc = item.get("document", "").replace("\n", " ")
                if doc:
                    compliance_rows.append(doc)
            for item in rag_context_from_pipeline.get("contextual_rules", []) or []:
                doc = item.get("document", "").replace("\n", " ")
                if doc:
                    contextual_rows.append(doc)

        comp_section = self._format_guidance_section("Compliance References", compliance_rows)
        ctx_section = self._format_guidance_section("Contextual Indicators", contextual_rows)

        for section in [comp_section, ctx_section]:
            if section:
                sections.append(section)

        if not sections:
            return "No additional guidance available."

        return "\n\n".join(sections)

    def process(self, task: AgentTask, progress_callback: callable = None) -> AgentResult:
        entities = task.input_data.get("entities", [])
        relationships = task.input_data.get("relationships", [])

        if not entities:
            print("     -> Skipping Security Assessment: No entities to analyze.")
            return self._create_result(task, TaskStatus.COMPLETED, data=task.input_data)
        entity_type_summary = {}
        for entity in entities:
            entity_type = entity.get("entity_type", "unknown")
            strategy = entity.get("anonymization_strategy", "unknown")
            
            if entity_type not in entity_type_summary:
                entity_type_summary[entity_type] = {
                    "count": 0,
                    "anonymization_strategies": []
                }
            
            entity_type_summary[entity_type]["count"] += 1
            if strategy not in entity_type_summary[entity_type]["anonymization_strategies"]:
                entity_type_summary[entity_type]["anonymization_strategies"].append(strategy)
        sanitized_relationships = []
        for rel in relationships:
            source_type = None
            target_type = None
            
            for entity in entities:
                if entity.get("text") == rel.get("source"):
                    source_type = entity.get("entity_type", "unknown")
                if entity.get("text") == rel.get("target"):
                    target_type = entity.get("entity_type", "unknown")
            
            if source_type and target_type:
                sanitized_relationships.append({
                    "source_type": source_type,
                    "target_type": target_type,
                    "relationship_type": rel.get("relationship_type", "unknown")
                })

        entity_types_found = list(entity_type_summary.keys())
        document_type = task.input_data.get("document_type", "document")
        rag_context_from_pipeline = task.input_data.get("rag_context", {}) or {}
        rag_guidance = self._build_rag_guidance(entity_types_found, rag_context_from_pipeline)
        
        system_prompt = f"""You are a cybersecurity risk analyst. Analyze the security risks for a {document_type} based ONLY on the entity types actually found in the document.

## PRIVACY REQUIREMENTS:
1. NEVER mention actual values from the document (no names, IDs, numbers, etc.)
2. ALWAYS refer to entities by their `entity_type` in backticks
3. Focus ONLY on the entity types that were actually detected: {entity_types_found}

## ANALYSIS SCOPE:
Analyze security risks based on the specific entity types found:

{self._generate_dynamic_assessment_scope(entity_types_found, document_type)}

## RISK SCORING:
- 5 (Critical): Immediate exploitation possible, high business impact
- 4 (High): Significant vulnerability, likely to be exploited
- 3 (Medium): Moderate risk requiring attention
- 2 (Low): Minor issue, best practice violation
- 1 (Info): Informational finding for awareness

## OUTPUT REQUIREMENTS:
For EACH distinct security concern (aim for 2-5 findings based on complexity):
{{
  "finding_summary": "Brief one-sentence summary using ONLY entity types",
  "risk_level": 1-5,
  "detailed_explanation": "Detailed paragraph explaining the risk using ONLY entity types in backticks. Discuss the security implications, attack vectors, and potential impact. NEVER mention actual values.",
  "recommendation": "Concise action item using generic terms",
  "implementation_guidance": "Specific steps to implement the recommendation, referring only to entity types",
  "compliance_mappings": ["List of relevant standards with specific control numbers"],
  "affected_entity_types": ["List of entity_type values involved in this finding"]
}}

REMEMBER: Quality over quantity - provide thorough, actionable findings that add real security value."""

        user_prompt = f"""Analyze this document's security posture based on the entity types and relationships found.

## RAG Knowledge Guidance:
{rag_guidance}

## Entity Type Summary:
{json.dumps(entity_type_summary, indent=2)}

## Entity Relationships (Sanitized):
{json.dumps(sanitized_relationships, indent=2)}

## Document Context:
- Total entities detected: {len(entities)}
- Unique entity types: {len(entity_type_summary)}
- Total relationships: {len(relationships)}

CRITICAL REMINDERS:
1. NEVER use actual values from the document in your response
2. ALWAYS refer to entities by their `entity_type` in backticks
3. If you need to reference a specific instance, say "the `entity_type` entity" or "one of the `entity_type` entities"
4. Focus on the security implications of having these TYPES of entities exposed
5. Consider ALL entity types in your assessment - don't miss any security implications

Provide comprehensive findings as a JSON array named "security_assessment_findings"."""
        
        try:
            print("     -> Calling LLM for Enhanced Security Risk Assessment...")
            llm_response = llm_service.get_llm_response(
                system_prompt, 
                user_prompt,
                timeout=task.timeout_seconds
            )
            
            if isinstance(llm_response, str):
                import re
                json_match = re.search(r'\{.*"security_assessment_findings"\s*:\s*\[(.*?)\]\s*\}', llm_response, re.DOTALL)
                if json_match:
                    findings = json.loads('{' + json_match.group(0) + '}').get("security_assessment_findings", [])
                else:
                    findings = []
            else:
                findings = llm_response.get("security_assessment_findings", [])
            
            if not isinstance(findings, list):
                raise ValueError("LLM response for 'security_assessment_findings' was not a list.")
            cleaned_findings = self._sanitize_findings(findings, entities)
            assessment_summary = {
                "total_findings": len(cleaned_findings),
                "critical_findings": len([f for f in cleaned_findings if f.get("risk_level", 0) >= 4]),
                "entity_types_assessed": list(entity_type_summary.keys()),
                "compliance_frameworks_covered": self._extract_compliance_frameworks(cleaned_findings)
            }
            
            output_data = task.input_data.copy()
            output_data["security_assessment_findings"] = cleaned_findings
            output_data["assessment_summary"] = assessment_summary
            output_data.setdefault("rag_context", rag_context_from_pipeline)
            output_data["rag_guidance"] = rag_guidance

            print(f"     -> Security Assessment complete: {len(cleaned_findings)} findings identified")
            print(f"     -> Critical/High findings: {assessment_summary['critical_findings']}")
            
            return self._create_result(task, TaskStatus.COMPLETED, data=output_data)

        except (ConnectionError, ValueError) as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=str(e))
        except Exception as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=f"An unexpected error occurred in Security Assessment Agent: {e}")
    
    def _generate_dynamic_assessment_scope(self, entity_types: List[str], document_type: str) -> str:
        scope_lines = []
        
        personal_types = ['person_name', 'email_address', 'phone_number', 'ssn', 'national_id']
        found_personal = [t for t in entity_types if t in personal_types]
        if found_personal:
            scope_lines.append(f"### PERSONAL DATA PROTECTION:")
            scope_lines.append(f"- Assess privacy risks for: {', '.join([f'`{t}`' for t in found_personal])}")
            scope_lines.append(f"- Evaluate anonymization effectiveness")
            scope_lines.append(f"- Consider GDPR/privacy compliance requirements")
         
        financial_types = ['credit_card', 'bank_account', 'routing_number', 'iban']
        found_financial = [t for t in entity_types if t in financial_types]
        if found_financial:
            scope_lines.append(f"### FINANCIAL DATA SECURITY:")
            scope_lines.append(f"- Assess PCI-DSS compliance for: {', '.join([f'`{t}`' for t in found_financial])}")
            scope_lines.append(f"- Evaluate encryption and protection measures")
        
        tech_types = ['ip_address', 'url', 'aws_arn', 'aws_role_name', 'api_key', 'access_key']
        found_tech = [t for t in entity_types if t in tech_types]
        if found_tech:
            scope_lines.append(f"### TECHNICAL SECURITY:")
            scope_lines.append(f"- Assess infrastructure exposure for: {', '.join([f'`{t}`' for t in found_tech])}")
            scope_lines.append(f"- Evaluate access control and authentication")
        
        scope_lines.append(f"### DOCUMENT-SPECIFIC RISKS:")
        scope_lines.append(f"- Assess risks specific to {document_type} documents")
        scope_lines.append(f"- Consider data retention and access control requirements")
        scope_lines.append(f"- Evaluate audit trail and monitoring needs")
        
        if not any([found_personal, found_financial, found_tech]):
            scope_lines.append(f"### GENERAL DATA SECURITY:")
            scope_lines.append(f"- Assess data classification requirements for: {', '.join([f'`{t}`' for t in entity_types])}")
            scope_lines.append(f"- Evaluate access controls and data handling procedures")
        
        return "\n".join(scope_lines)
    
    def _sanitize_findings(self, findings: List[Dict], entities: List[Dict]) -> List[Dict]:
        actual_values = set()
        for entity in entities:
            if entity.get("text"):
                actual_values.add(entity["text"])
                actual_values.add(f"'{entity['text']}'")
                actual_values.add(f'"{entity["text"]}"')
                actual_values.add(f"({entity['text']})")
        
        cleaned_findings = []
        for finding in findings:
            cleaned_finding = {}
            for key, value in finding.items():
                if isinstance(value, str):
                    for actual_value in actual_values:
                        if actual_value in value:
                            entity_type = "entity"
                            for entity in entities:
                                if entity.get("text") == actual_value.strip("'\"()"):
                                    entity_type = entity.get("entity_type", "entity")
                                    break
                            value = value.replace(actual_value, f"`{entity_type}`")
                    
                    cleaned_finding[key] = value
                else:
                    cleaned_finding[key] = value
            
            cleaned_findings.append(cleaned_finding)
        
        return cleaned_findings
    
    def _extract_compliance_frameworks(self, findings: List[Dict]) -> List[str]:
        frameworks = set()
        for finding in findings:
            mappings = finding.get("compliance_mappings", [])
            for mapping in mappings:
                if ":" in mapping:
                    framework = mapping.split(":")[0].strip()
                    frameworks.add(framework)
        
        return sorted(list(frameworks))