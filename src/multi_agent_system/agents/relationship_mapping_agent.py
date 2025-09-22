from typing import List
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service
import json

class RelationshipMappingAgent(BaseAgent):
    def __init__(self):
        super().__init__("RelationshipMappingAgent", "2.0.0-AI")

    def _define_capabilities(self) -> List[str]:
        return ["relationship_analysis", "semantic_graph", "entity_correlation"]

    def process(self, task: AgentTask) -> AgentResult:
        full_text = task.input_data.get("full_text", "")
        entities = task.input_data.get("entities", [])

        if not entities:
            print("     -> Skipping relationship mapping: No entities found.")
            return self._create_result(task, TaskStatus.COMPLETED, data={"relationships": [], "entities": entities})

        system_prompt = """
        You are a security intelligence analyst. Your job is to understand the connections between different pieces of information in a document.
        Given the document's text and a list of pre-identified entities, your task is to describe the relationships between them.
        Focus on meaningful connections, such as a person associated with an action, an IP address accessing a system, or a user being part of a security policy.
        You MUST return your findings ONLY as a single JSON object containing a list named "relationships".
        """

        user_prompt = f"""
        Analyze the text and the list of entities to identify connections.
        
        Each object in your "relationships" list must have:
        - "source": The text of the source entity.
        - "target": The text of the target entity.
        - "description": A brief explanation of how they are related (e.g., "logged in from", "member of", "configured rule for").

        Document Text:
        ---
        {full_text}
        ---

        Identified Entities:
        ---
        {json.dumps(entities, indent=2)}
        ---
        """

        try:
            print("     -> Calling LLM for Relationship Mapping...")
            llm_response = llm_service.get_llm_response(system_prompt, user_prompt)
            relationships = llm_response.get("relationships", [])
            
            if not isinstance(relationships, list):
                raise ValueError("LLM response for 'relationships' was not a list.")

            result_data = {
                "entities": entities,
                "relationships": relationships,
                "graph_stats": {
                    "nodes": len(entities),
                    "edges": len(relationships)
                }
            }
            return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

        except (ConnectionError, ValueError) as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=str(e))
        except Exception as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=f"An unexpected error occurred in Relationship Agent: {e}")