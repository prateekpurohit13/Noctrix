from typing import List
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service
import json

class SecurityAssessmentAgent(BaseAgent):
    def __init__(self):
        super().__init__("SecurityAssessmentAgent", "1.0.0-AI")

    def _define_capabilities(self) -> List[str]:
        return ["security_risk_assessment"]

    def process(self, task: AgentTask, progress_callback: callable = None) -> AgentResult:
        entities = task.input_data.get("entities", [])
        relationships = task.input_data.get("relationships", [])

        if not entities:
            print("     -> Skipping Security Assessment: No entities to analyze.")
            return self._create_result(task, TaskStatus.COMPLETED, data=task.input_data)
        sanitized_entities = [
            {"entity_type": e.get("entity_type")} for e in entities
        ]

        system_prompt = """
        You are a world-class cybersecurity risk analyst. You have been given a structured list of entity types and their relationships.
        Your task is to analyze this structured data to identify potential vulnerabilities and security risks.
        CRITICAL INSTRUCTION: Your entire response MUST BE privacy-preserving. In your explanations and recommendations, you MUST refer to entities by their generic `entity_type` ONLY (e.g., "an `IP Address`", "a `Person`'", a `Hostname`, etc.). DO NOT use or repeat any actual sensitive values from the document.
        """

        user_prompt = f"""
        Analyze the following structured data. For each risk you identify, provide a full assessment.

        For each risk, provide:
        - "finding_summary": A brief, one-sentence summary of the issue.
        - "risk_level": A score from 1 (Low) to 5 (Critical).
        - "detailed_explanation": A paragraph explaining the risk, referring ONLY to entity types.
        - "recommendation": A short, actionable step for the Remediation Roadmap (e.g., "Implement strong password policy").
        - "implementation_guidance": A more detailed sentence explaining HOW to implement the recommendation (e.g., "Configure minimum 12-character complex passwords.").
        - "compliance_mappings": A list of relevant compliance standards, like "NIST CSF: PR.AC-1" or "ISO 27001: A.9.2.1".

        Return your findings ONLY as a single JSON object in a list named "security_assessment_findings".

        Structured Data:
        ---
        {json.dumps({"entities": sanitized_entities, "relationships": relationships}, indent=2)}
        ---
        """
        
        try:
            print("     -> Calling LLM for Security Risk Assessment...")
            llm_response = llm_service.get_llm_response(
                system_prompt, 
                user_prompt,
                timeout=task.timeout_seconds
            )
            
            findings = llm_response.get("security_assessment_findings", [])           
            if not isinstance(findings, list):
                raise ValueError("LLM response for 'security_assessment_findings' was not a list.")
            output_data = task.input_data.copy()
            output_data["security_assessment_findings"] = findings

            return self._create_result(task, TaskStatus.COMPLETED, data=output_data)

        except (ConnectionError, ValueError) as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=str(e))
        except Exception as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=f"An unexpected error occurred in Security Assessment Agent: {e}")