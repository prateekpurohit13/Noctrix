from typing import List
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service

class SecurityEntityAgent(BaseAgent):
    def __init__(self):
        super().__init__("SecurityEntityAgent", "2.0.0-AI")

    def _define_capabilities(self) -> List[str]:
        return ["security_analysis", "network_entity_detection", "ip_detection", "hostname_detection"]

    def process(self, task: AgentTask) -> AgentResult:
        full_text = task.input_data.get("full_text")
        if not full_text:
            return self._create_result(task, TaskStatus.FAILED, error_message="No text content provided.")

        system_prompt = """
        You are a senior security operations center (SOC) analyst with expertise in identifying technical security entities within unstructured text.
        Your task is to find entities like IP addresses, hostnames, firewall rules, and IAM roles.
        For each entity, you must provide a security classification ('critical', 'important', 'informational') and suggest an anonymization strategy ('Tokenize', 'Redact', 'Preserve').
        For IP addresses, you MUST add a 'classification' metadata field indicating if it is 'private' or 'public'.
        You MUST return your findings ONLY as a single JSON object containing a list named "entities".
        """

        user_prompt = f"""
            Analyze the following document text and extract all security-related entities.

            Each entity in your JSON list should have the following keys:
            - "text": The exact text of the identified entity.
            - "entity_type": The type of security entity (e.g., "IP Address", "Hostname", "Firewall Rule").
            - "security_classification": The assessed risk level ('critical', 'important', 'informational').
            - "anonymization_strategy": The suggested strategy ('Tokenize', 'Redact', 'Preserve').
            - "metadata": A dictionary for extra details. For IPs, this must contain {{"classification": "private/public"}}.

            Document Text:
            ---
            {full_text}
            ---
        """
        try:
            print("     -> Calling LLM for Security Entity detection...")
            llm_response = llm_service.get_llm_response(system_prompt, user_prompt)
            entities = llm_response.get("entities", [])
            
            if not isinstance(entities, list):
                raise ValueError("LLM response for 'entities' was not a list.")
            all_entities = task.input_data.get("entities", []) + entities

            result_data = {
                "entities": all_entities,
                "security_summary": {
                    "security_entities_found": len(entities)
                }
            }
            return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

        except (ConnectionError, ValueError) as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=str(e))
        except Exception as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=f"An unexpected error occurred in Security Agent: {e}")