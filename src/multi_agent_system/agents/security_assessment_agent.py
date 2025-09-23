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
            {"entity_type": e.get("entity_type"), "text_preview": e.get("text", "")[:10] + "..."} 
            for e in entities
        ]

        system_prompt = """
        You are a world-class cybersecurity risk analyst and penetration tester. You have been given a structured list of security entities and their relationships, which were extracted from a client's document.
        Your task is to analyze this structured data to identify potential vulnerabilities, misconfigurations, and security risks. You must think like an attacker.
        CRITICAL INSTRUCTION: In your `detailed_explanation` and `recommendation`, you MUST NOT repeat the sensitive `text` value of any entity. Instead, you MUST refer to the entities by their generic `entity_type` (e.g., "an `IP Address`", "a `Person`'s name", "the `Hostname`"). Your entire analysis must be privacy-preserving.
        """

        user_prompt = f"""
        Analyze the following structured data. Identify and describe any security risks.

        For each risk you identify, provide:
        - "finding_summary": A brief, one-sentence summary of the issue.
        - "risk_level": A score from 1 (Low) to 5 (Critical).
        - "detailed_explanation": A paragraph explaining the risk, referring only to entity types.
        - "recommendation": An actionable mitigation step, referring only to entity types.

        Return your findings ONLY as a single JSON object containing a list named "security_assessment_findings". If no risks are found, return an empty list.

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
                model_name=llm_service.SMART_MODEL,
                timeout=task.timeout_seconds
            )
            
            findings = llm_response.get("security_assessment_findings", [])           
            if not isinstance(findings, list):
                raise ValueError("LLM response for 'security_assessment_findings' was not a list.")
            output_data = {
                "security_assessment_findings": findings
            }
            return self._create_result(task, TaskStatus.COMPLETED, data=output_data)

        except (ConnectionError, ValueError) as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=str(e))
        except Exception as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=f"An unexpected error occurred in Security Assessment Agent: {e}")