from typing import List
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service

class DocumentUnderstandingAgent(BaseAgent):
    def __init__(self):
        super().__init__("DocumentUnderstandingAgent", "3.0.0-AI-Describe")

    def _define_capabilities(self) -> List[str]:
        return ["document_analysis"]

    def process(self, task: AgentTask, progress_callback: callable = None) -> AgentResult:
        dom = task.input_data.get("dom")
        if not dom:
            return self._create_result(task, TaskStatus.FAILED, error_message="No DocumentObjectModel provided")

        full_text = self._extract_and_clean_text(dom)
        if not full_text.strip():
            result_data = { "dom": dom, "document_type": "blank_or_image_only", "document_description": "The document is blank or contains no extractable text.", "security_domains": [], "full_text": "" }
            return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

        try:
            print("     -> Calling LLM for document classification...")
            doc_type_response = self._get_document_classification(full_text[:3000])
            document_type = doc_type_response.get("document_type", "unknown")
            security_domains = doc_type_response.get("security_domains", ["general"])
            print(f"     -> Classified as: '{document_type}'")
        except (ConnectionError, ValueError) as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=f"Failed during classification: {e}")

        try:
            print("     -> Calling LLM for dynamic document description...")
            document_description = self._generate_dynamic_description(document_type, full_text[:2000])
            print(f"     -> Generated dynamic document description.")
        except Exception as e:
            print(f"     -> ERROR: Failed to generate document description: {e}")
            return self._create_result(task, TaskStatus.FAILED, 
                                     error_message=f"Failed to generate document description: {e}")
        
        result_data = {
            "dom": dom,
            "document_type": document_type,
            "document_description": document_description,
            "security_domains": security_domains,
            "full_text": full_text
        }
        return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

    def _get_document_classification(self, text_sample: str) -> dict:
        system_prompt = """
        You are an expert document analyst. Your job is to classify a document based on its content.
        Return a single JSON object with two keys: "document_type" (a concise label like "Network Diagram" or "Visitor Log") and "security_domains" (a list like ["network_security", "data_privacy"]).
        """
        user_prompt = f"Analyze the following document text and classify it.\n\nDocument Text:\n---\n{text_sample}\n---"
        
        return llm_service.get_llm_response(
            system_prompt, user_prompt,
            model_name=llm_service.FAST_MODEL, timeout=60
        )

    def _generate_dynamic_description(self, document_type: str, sample_text: str) -> str:
        system_prompt = f"""Generate a professional description for a "{document_type}" document.

Rules:
1. Describe what this document type is and its purpose
2. Keep it professional and generic
3. Do NOT include specific details from content
4. Return JSON: {{"description": "your text here"}}"""

        user_prompt = f"""Describe what a "{document_type}" document typically contains and its purpose.

Example: If document type is "Invoice", describe what invoices are for, not the specific invoice details.

Response format: {{"description": "A [document_type] is a document that..."}}"""

        response = llm_service.get_llm_response(
            system_prompt, user_prompt,
            model_name=llm_service.FAST_MODEL, timeout=60
        )
        description = response.get("description", "").strip()
        if not description or len(description) < 10:
            raise ValueError(f"Invalid description returned: '{description}'")
            
        return description

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