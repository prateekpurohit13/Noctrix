from typing import List
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service

class PIIDetectionAgent(BaseAgent):
    def __init__(self):
        super().__init__("PIIDetectionAgent", "2.0.0-AI")
    
    def _define_capabilities(self) -> List[str]:
        return ["pii_extraction", "name_detection", "email_detection", "phone_detection"]
    
    def process(self, task: AgentTask) -> AgentResult:
        full_text = task.input_data.get("full_text")
        if not full_text:
            return self._create_result(task, TaskStatus.FAILED, error_message="No text content provided.")

        system_prompt = """
        You are an expert data analyst specializing in Personally Identifiable Information (PII) detection.
        Your task is to analyze text and identify entities such as names, email addresses, and phone numbers.
        Provide a confidence score from 0.0 to 1.0 for each entity.
        Suggest an appropriate anonymization strategy for each entity from the following options: 'Redact', 'Tokenize'.
        You MUST return your findings ONLY as a single JSON object containing a list named "entities".
        """

        user_prompt = f"""
        Analyze the following document text and extract all PII entities.
        
        Each entity in your JSON list should have the following keys:
        - "text": The exact text of the identified entity.
        - "entity_type": The type of PII (e.g., "Person", "Email Address", "Phone Number").
        - "confidence": Your confidence in the identification (e.g., 0.95).
        - "anonymization_strategy": The suggested strategy (e.g., "Redact").

        Document Text:
        ---
        {full_text}
        ---
        """
        
        try:
            print("     -> Calling LLM for PII detection...")
            llm_response = llm_service.get_llm_response(system_prompt, user_prompt)
            entities = llm_response.get("entities", [])

            if not isinstance(entities, list):
                raise ValueError("LLM response for 'entities' was not a list.")

            result_data = {
                "entities": entities,
                "pii_summary": {
                    "total_entities": len(entities)
                }
            }
            return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

        except (ConnectionError, ValueError) as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=str(e))
        except Exception as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=f"An unexpected error occurred in PII Agent: {e}")