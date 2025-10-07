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
            "You are an expert document analyst with deep understanding of various document types. "
            "Analyze the actual content and classify it accurately based on what the document truly contains. "
            "Be specific and descriptive - avoid generic classifications unless the document is genuinely unclear."
        )

        hint_payload = json.dumps(hints, ensure_ascii=False)
        user_prompt = (
            "Analyze and classify this document based on its actual content. Provide a specific, meaningful document type.\n\n"
            "GUIDELINES:\n"
            "- Classify based on the document's primary purpose and content\n"
            "- Be specific: prefer 'Network Firewall Configuration' over 'Generic Document'\n"
            "- Use hints only if they align with the actual text content\n"
            "- Identify 1-3 relevant security domains (e.g., network_security, physical_security, cloud_security, data_privacy)\n"
            "- Only use 'Generic Document' if the content is truly unclear or mixed-purpose\n\n"
            f"DOCUMENT TEXT:\n<<<\n{text_sample}\n>>>\n\n"
            f"HINTS (for reference only):\n{hint_payload}\n\n"
            "Return JSON with:\n"
            "{\n"
            "  \"document_type\": \"Specific descriptive name\",\n"
            "  \"security_domains\": [\"domain1\", \"domain2\"],\n"
            "  \"rationale\": \"Brief explanation of classification\"\n"
            "}"
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
        """Generate flexible hints based on content patterns, not exact matches."""
        hints: List[Dict[str, Any]] = []

        def add_hint(document_type: str, reason: str, confidence: float):
            hints.append({
                "document_type": document_type,
                "reason": reason,
                "confidence": confidence
            })

        # Use more flexible pattern matching
        text_lower = text.lower()
        
        # Physical security indicators
        if any(term in text_lower for term in ["visitor", "sign in", "entry", "badge", "access log"]):
            add_hint("Visitor/Access Log", "Contains visitor or access control terminology", 0.7)
        
        # Cloud/IAM indicators
        if any(term in text_lower for term in ["iam", "role", "policy", "permission", "aws", "azure", "gcp", "assume role"]):
            add_hint("Cloud IAM Configuration", "Contains cloud identity and access management terms", 0.75)
        
        # Network security indicators
        if any(term in text_lower for term in ["firewall", "port", "tcp", "udp", "ip address", "subnet", "source ranges"]):
            add_hint("Network Security Document", "Contains networking and security terminology", 0.7)
        
        # Compliance/Policy indicators
        if any(term in text_lower for term in ["compliance", "audit", "regulation", "policy", "standard"]):
            add_hint("Compliance/Policy Document", "Contains compliance or policy language", 0.65)
        
        # Monitoring indicators
        if any(term in text_lower for term in ["monitor", "alert", "dashboard", "metric", "log", "cctv", "camera"]):
            add_hint("Monitoring/Operations Document", "Contains monitoring or operational terms", 0.65)
        
        # Security incident indicators
        if any(term in text_lower for term in ["incident", "breach", "vulnerability", "threat", "attack"]):
            add_hint("Security Incident Document", "Contains incident or threat terminology", 0.7)

        # If no strong hints found
        if not hints:
            add_hint("Generic Document", "No strong structural indicators found", 0.3)

        # Sort by confidence but don't make them definitive
        return sorted(hints, key=lambda h: h["confidence"], reverse=True)

    def _apply_classification_hints(
        self,
        response: Dict[str, Any],
        hints: List[Dict[str, Any]]
    ) -> Tuple[str, List[str]]:
        """Apply hints only when LLM classification is clearly weak."""
        document_type = (response or {}).get("document_type", "unknown")
        security_domains = response.get("security_domains", []) if isinstance(response, dict) else []

        if isinstance(security_domains, str):
            security_domains = [security_domains]

        # Trust the LLM first - only override if it clearly failed
        if document_type.lower() in {"unknown", "unclear", "generic", "generic document", ""}:
            # Use hints only when LLM couldn't classify
            top_hint = hints[0] if hints else None
            if top_hint and top_hint["confidence"] >= 0.65:
                document_type = top_hint["document_type"]
                print(f"     -> Using hint classification: {document_type}")

        # Infer security domains from document type if not provided
        if not security_domains or security_domains == ["general"]:
            security_domains = self._infer_security_domains(document_type)

        return document_type, security_domains

    def _infer_security_domains(self, document_type: str) -> List[str]:
        """Infer security domains based on document type keywords."""
        doc_type_lower = document_type.lower()
        domains = []
        
        if any(term in doc_type_lower for term in ["iam", "role", "policy", "cloud", "aws", "azure"]):
            domains.extend(["cloud_security", "identity_access_management"])
        
        if any(term in doc_type_lower for term in ["network", "firewall", "port", "ip"]):
            domains.append("network_security")
        
        if any(term in doc_type_lower for term in ["visitor", "access", "badge", "physical"]):
            domains.extend(["physical_security", "data_privacy"])
        
        if any(term in doc_type_lower for term in ["compliance", "audit", "regulation"]):
            domains.append("compliance")
        
        if any(term in doc_type_lower for term in ["incident", "breach", "vulnerability"]):
            domains.append("incident_response")
        
        # Default fallback
        return domains if domains else ["data_privacy"]

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