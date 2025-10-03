from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import json
import re
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from .. import llm_service
from ...rag.retrieval import RAGRetriever

class DocumentUnderstandingAgent(BaseAgent):
    def __init__(self, rag_retriever: Optional[RAGRetriever] = None):
        super().__init__("DocumentUnderstandingAgent", "3.0.0-AI-Describe")
        self.rag_retriever = rag_retriever

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
            classification_sample = full_text[:3000]
            hints = self._generate_classification_hints(classification_sample)
            doc_type_response = self._get_document_classification(classification_sample, hints)
            document_type, security_domains = self._apply_classification_hints(
                doc_type_response,
                hints
            )
            print(f"     -> Classified as: '{document_type}'")
        except (ConnectionError, ValueError) as e:
            return self._create_result(task, TaskStatus.FAILED, error_message=f"Failed during classification: {e}")

        retrieval_context: Dict[str, Any] = {}

        try:
            print("     -> Calling LLM for dynamic document description...")
            document_description = self._generate_dynamic_description(
                document_type,
                full_text[:2000],
                hints
            )
            print(f"     -> Generated dynamic document description.")
        except Exception as e:
            print(f"     -> ERROR: Failed to generate document description: {e}")
            return self._create_result(task, TaskStatus.FAILED, 
                                     error_message=f"Failed to generate document description: {e}")
        
        if self.rag_retriever:
            try:
                retrieval_context = self.rag_retriever.get_comprehensive_context(
                    document_type=document_type,
                    text_sample=full_text[:2000],
                    entity_types=None
                ) or {}
                retrieval_context["retrieved_at"] = datetime.utcnow().isoformat() + "Z"
            except Exception as retrieval_error:
                print(f"     -> WARNING: RAG retrieval failed: {retrieval_error}")

        result_data = {
            "dom": dom,
            "document_type": document_type,
            "document_description": document_description,
            "security_domains": security_domains,
            "full_text": full_text,
            "rag_context": retrieval_context
        }
        return self._create_result(task, TaskStatus.COMPLETED, data=result_data)

    def _get_document_classification(
        self,
        text_sample: str,
        hints: List[Dict[str, Any]]
    ) -> dict:
        system_prompt = (
            "You are an expert document analyst. Identify the document type and security domains based strictly on the "
            "actual document text. Never assume it's a 'Network Diagram' unless the content truly matches."
        )

        hint_payload = json.dumps(hints, ensure_ascii=False)
        user_prompt = (
            "Classify the document described below. Use the hints as supportive evidence only if they align with the text.\n"
            "Return JSON with keys: document_type (short title), security_domains (list of 1-3 domains),"
            " and rationale (brief justification). Document text should always take precedence over hints.\n"
            f"Document text (truncated):\n<<<\n{text_sample}\n>>>\n\n"
            f"Derived hints:\n{hint_payload}\n"
            "JSON Schema:{\n  \"document_type\": \"string\",\n  \"security_domains\": [\"string\"],\n  \"rationale\": \"string\"\n}"
        )

        raw_response = llm_service.get_llm_response(
            system_prompt,
            user_prompt,
            model_name=llm_service.FAST_MODEL,
            timeout=60
        )

        if isinstance(raw_response, str):
            try:
                return json.loads(raw_response)
            except json.JSONDecodeError:
                return {"document_type": raw_response.strip(), "security_domains": ["general"], "rationale": "LLM string"}

        return raw_response or {"document_type": "unknown", "security_domains": ["general"], "rationale": "no-response"}

    def _generate_dynamic_description(
        self,
        document_type: str,
        sample_text: str,
        hints: List[Dict[str, Any]]
    ) -> str:
        hint_summary = json.dumps([
            {"document_type": h.get("document_type"), "reason": h.get("reason")}
            for h in hints[:3]
        ], ensure_ascii=False)

        system_prompt = (
            "You are drafting a neutral description for a document type. Explain the typical purpose of this type without"
            " repeating sensitive details or examples from the provided text."
        )

        user_prompt = (
            f"Document type: {document_type}\n"
            "Use the context summary to stay aligned but DO NOT include the literal tokens from the excerpt.\n"
            f"Context summary (for your awareness only): {hint_summary}\n"
            "Respond with JSON: {\"description\": \"A [document_type]...\"}."
        )

        response = llm_service.get_llm_response(
            system_prompt,
            user_prompt,
            model_name=llm_service.FAST_MODEL,
            timeout=60
        )

        description = response.get("description", "").strip() if isinstance(response, dict) else ""
        if not description or len(description) < 10:
            raise ValueError(f"Invalid description returned: '{description}'")
            
        return description

    def _generate_classification_hints(self, text: str) -> List[Dict[str, Any]]:
        upper_text = text.upper()
        hints: List[Dict[str, Any]] = []

        def add_hint(document_type: str, reason: str, confidence: float):
            hints.append({
                "document_type": document_type,
                "reason": reason,
                "confidence": confidence
            })

        if re.search(r"VISITOR(S)?\s+LOG", upper_text) or "PLEASE SIGN IN" in upper_text:
            add_hint(
                "Visitor Log",
                "Found headers such as 'VISITORS LOG BOOK' or sign-in columns.",
                0.95
            )

        if re.search(r"GROUPNAME\"|POLICYDOCUMENT", text, re.IGNORECASE):
            add_hint(
                "AWS IAM Policy",
                "Detected IAM policy keywords like GroupName and PolicyDocument.",
                0.9
            )

        if "ASSUME ROLE POLICY" in upper_text or "ROLEID" in upper_text:
            add_hint(
                "AWS IAM Role Policy",
                "Detected role policy commands and trust policy references.",
                0.9
            )

        if re.search(r"SOURCE RANGES" , upper_text) and re.search(r"TCP:22", upper_text):
            add_hint(
                "Firewall Rule Table",
                "Contains firewall rule columns such as source ranges and TCP/UDP allowances.",
                0.88
            )

        ip_hits = re.findall(r"\b(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}\b", text)
        if len(ip_hits) >= 3:
            add_hint(
                "Network Monitoring Dashboard",
                "Multiple IP addresses and monitoring terms detected.",
                0.8
            )

        if re.search(r"CCTV", upper_text) or "CAMERAS" in upper_text:
            add_hint(
                "CCTV Monitoring Sheet",
                "Camera monitoring terminology present.",
                0.75
            )

        if not hints:
            add_hint("Generic Document", "No strong structural indicators found.", 0.3)

        return sorted(hints, key=lambda h: h["confidence"], reverse=True)

    def _apply_classification_hints(
        self,
        response: Dict[str, Any],
        hints: List[Dict[str, Any]]
    ) -> Tuple[str, List[str]]:
        document_type = (response or {}).get("document_type", "unknown")
        security_domains = response.get("security_domains", []) if isinstance(response, dict) else []

        if isinstance(security_domains, str):
            security_domains = [security_domains]

        if not security_domains:
            security_domains = ["data_privacy"]

        top_hint = hints[0] if hints else None

        if top_hint and top_hint["confidence"] >= 0.9:
            if document_type.lower() in {"unknown", "network diagram", "generic document"}:
                document_type = top_hint["document_type"]

        restricted_domains = {
            "Visitor Log": ["physical_security", "data_privacy"],
            "AWS IAM Policy": ["cloud_security", "identity_access_management"],
            "AWS IAM Role Policy": ["cloud_security", "identity_access_management"],
            "Firewall Rule Table": ["network_security", "cloud_security"],
            "Network Monitoring Dashboard": ["network_security"]
        }

        if document_type in restricted_domains:
            security_domains = restricted_domains[document_type]

        return document_type, security_domains

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