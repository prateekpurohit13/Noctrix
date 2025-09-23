from typing import List
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service

class DocumentUnderstandingAgent(BaseAgent):
    def __init__(self):
        super().__init__("DocumentUnderstandingAgent", "2.0.0-AI")

    def _define_capabilities(self) -> List[str]:
        return ["document_analysis"]

    def process(self, task: AgentTask, progress_callback: callable = None) -> AgentResult:
        dom = task.input_data.get("dom")
        if not dom:
            return self._create_result(task, TaskStatus.FAILED, error_message="No DocumentObjectModel provided")

        full_text = self._extract_and_clean_text(dom)
        if not full_text:
            result_data = {
                "dom": dom,
                "document_type": "unknown_no_text",
                "security_domains": [],
                "full_text": ""
            }
            return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

        system_prompt = """
        You are an expert document analyst. Your job is to look at the text from a document and determine its type and purpose.
        You MUST return a single, valid JSON object with two keys: "document_type" and "security_domains".
        The "document_type" should be a concise label, like "Network Diagram", "Firewall Configuration", "Visitor Log", "Test Score Report", or "Employee Data Sheet".
        The "security_domains" should be a list of relevant domains, like ["network_security", "physical_security", "user_access_control", "data_privacy"].
        """
        
        user_prompt = f"""
        Analyze the following document text and classify it. To be fast and efficient, you only need to analyze the first 3000 characters of the text provided.

        Document Text:
        ---
        {full_text[:3000]} 
        ---
        """
        
        try:
            print("     -> Calling LLM for document classification (using fast model)...")
            llm_response = llm_service.get_llm_response(
                system_prompt,
                user_prompt,
                model_name=llm_service.FAST_MODEL,
                timeout=60
            )
            
            document_type = llm_response.get("document_type", "unknown")
            security_domains = llm_response.get("security_domains", ["general"])
            print(f"     -> Classified as: '{document_type}'")

            result_data = {
                "dom": dom,
                "document_type": document_type,
                "security_domains": security_domains,
                "full_text": full_text
            }
            
            return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

        except (ConnectionError, ValueError) as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=str(e))
        except Exception as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=f"An unexpected error in AI Document Understanding: {e}")

    def _extract_and_clean_text(self, dom) -> str:
        text_parts = []
        sections = dom.sections if dom.sections else []
        for section in sections:
            section_type = getattr(section, 'type', 'unknown')
            if section_type == 'table' and hasattr(section, 'rows'):
                for row in section.rows:
                    row_texts = []
                    if isinstance(row, list):
                        for cell in row:
                            cell_text = getattr(cell, 'text_content', None)
                            if cell_text and str(cell_text).strip() != 'None':
                                row_texts.append(str(cell_text).strip())
                    if row_texts:
                        text_parts.append(" ".join(row_texts))
            else:
                text_content = getattr(section, 'text_content', None)
                if text_content:
                    text_parts.append(text_content.strip())
        
        return "\n".join(text_parts)