from typing import Dict, List, Any
import re
from pathlib import Path
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from ...common.models import DocumentObjectModel

class DocumentUnderstandingAgent(BaseAgent):
    def __init__(self):
        super().__init__("DocumentUnderstandingAgent", "1.0.0")
        self.document_patterns = {
            "visitor_log": {
                "keywords": ["visitor", "log", "sign in", "name", "time in", "time out"],
                "structure_indicators": ["date", "name", "reason", "visit"],
                "security_domains": ["access_control", "physical_security"]
            },
            "employee_verification": {
                "keywords": ["employee", "id", "verification", "hr", "staff"],
                "structure_indicators": ["employee id", "department", "position", "status"],
                "security_domains": ["user_management", "access_control"]
            },
            "network_config": {
                "keywords": ["ip", "router", "switch", "network", "config", "firewall"],
                "structure_indicators": ["address", "port", "protocol", "rule"],
                "security_domains": ["network_security", "infrastructure"]
            },
            "policy_document": {
                "keywords": ["policy", "procedure", "compliance", "security", "guideline"],
                "structure_indicators": ["section", "requirement", "control", "standard"],
                "security_domains": ["security_policy", "compliance"]
            },
            "incident_report": {
                "keywords": ["incident", "alert", "security", "breach", "vulnerability"],
                "structure_indicators": ["severity", "impact", "response", "remediation"],
                "security_domains": ["incident_response", "security_operations"]
            },
            "access_log": {
                "keywords": ["access", "login", "authentication", "session", "audit"],
                "structure_indicators": ["user", "timestamp", "resource", "action"],
                "security_domains": ["access_control", "audit_logging"]
            }
        }
    
    def _define_capabilities(self) -> List[str]:
        return ["document_analysis", "structure_detection", "type_classification", "metadata_extraction"]
    
    def process(self, task: AgentTask) -> AgentResult:       
        try:
            dom = task.input_data.get("dom")
            if not dom:
                return self._create_result(
                    task, 
                    TaskStatus.FAILED,
                    error_message="No DocumentObjectModel provided"
                )
            
            structure_analysis = self._analyze_document_structure(dom)
            document_type, confidence = self._classify_document_type(dom)
            security_domains = self._identify_security_domains(dom, document_type)
            full_text = self._extract_and_clean_text(dom)
            metadata = self._generate_metadata(dom, document_type, structure_analysis)
            
            result_data = {
                "document_type": document_type,
                "classification_confidence": confidence,
                "security_domains": security_domains,
                "structure_analysis": structure_analysis,
                "full_text": full_text,
                "metadata": metadata,
                "processing_notes": [
                    "Document understanding completed without LLM",
                    f"Classified as: {document_type} (confidence: {confidence:.2f})",
                    f"Security domains: {', '.join(security_domains)}"
                ]
            }
            
            return self._create_result(task, TaskStatus.COMPLETED, data=result_data)          
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._create_result(
                task,
                TaskStatus.FAILED, 
                error_message=f"Document understanding failed: {str(e)}"
            )
    
    def _analyze_document_structure(self, dom: DocumentObjectModel) -> Dict[str, Any]:        
        structure = {
            "total_sections": len(dom.sections) if dom.sections else 0,
            "section_types": {},
            "has_tables": False,
            "has_forms": False,
            "text_density": 0.0,
            "image_count": 0,
            "estimated_complexity": "low"
        }       
        total_text_length = 0
        sections = dom.sections if dom.sections else []       
        for section in sections:
            section_type = getattr(section, 'type', 'unknown')
            structure["section_types"][section_type] = structure["section_types"].get(section_type, 0) + 1
            text_content = getattr(section, 'text_content', None)
            
            if text_content:
                total_text_length += len(text_content)
                if self._has_table_structure(text_content):
                    structure["has_tables"] = True
                if self._has_form_structure(text_content):
                    structure["has_forms"] = True          
            if section_type == "image":
                structure["image_count"] += 1
        
        structure["text_density"] = total_text_length / max(len(sections), 1)       
        if structure["text_density"] > 1000 or structure["total_sections"] > 10:
            structure["estimated_complexity"] = "high"
        elif structure["text_density"] > 500 or structure["total_sections"] > 5:
            structure["estimated_complexity"] = "medium"
        
        return structure
    
    def _classify_document_type(self, dom: DocumentObjectModel) -> tuple[str, float]:
        full_text = self._extract_and_clean_text(dom).lower()      
        best_match = "unknown"
        best_score = 0.0       
        for doc_type, patterns in self.document_patterns.items():
            score = 0.0
            total_indicators = 0
            keyword_matches = 0
            for keyword in patterns["keywords"]:
                if keyword.lower() in full_text:
                    keyword_matches += 1
            
            keyword_score = keyword_matches / len(patterns["keywords"])
            score += keyword_score * 0.6
            structure_matches = 0
            for indicator in patterns["structure_indicators"]:
                if indicator.lower() in full_text:
                    structure_matches += 1
            
            structure_score = structure_matches / len(patterns["structure_indicators"])
            score += structure_score * 0.4
            
            if score > best_score:
                best_score = score
                best_match = doc_type
        
        # Ensure minimum confidence threshold
        if best_score < 0.3:
            best_match = "unknown"
            best_score = 0.0
        
        return best_match, best_score
    
    def _identify_security_domains(self, dom: DocumentObjectModel, document_type: str) -> List[str]:        
        if document_type in self.document_patterns:
            base_domains = self.document_patterns[document_type]["security_domains"].copy()
        else:
            base_domains = ["general"]
        
        full_text = self._extract_and_clean_text(dom).lower()
        
        domain_keywords = {
            "user_management": ["user", "account", "credential", "password", "authentication"],
            "network_security": ["network", "firewall", "router", "ip", "port", "protocol"],
            "access_control": ["access", "permission", "authorization", "role", "privilege"],
            "incident_response": ["incident", "breach", "alert", "vulnerability", "threat"],
            "compliance": ["compliance", "audit", "regulation", "standard", "requirement"],
            "data_protection": ["data", "privacy", "encryption", "pii", "confidential"]
        }
        
        for domain, keywords in domain_keywords.items():
            if domain not in base_domains:
                keyword_count = sum(1 for keyword in keywords if keyword in full_text)
                if keyword_count >= 2:
                    base_domains.append(domain)       
        return base_domains
    
    def _extract_and_clean_text(self, dom: DocumentObjectModel) -> str:        
        text_parts = []
        sections = dom.sections if dom.sections else []
        
        for section in sections:
            section_type = getattr(section, 'type', 'unknown')
            
            if section_type == 'table':
                table_text = self._extract_table_text(section)
                if table_text:
                    text_parts.append(table_text)
            else:
                text_content = getattr(section, 'text_content', None)
                if text_content:
                    clean_text = self._clean_text(text_content)
                    if clean_text:
                        text_parts.append(clean_text)
        
        extracted_text = "\n".join(text_parts)      
        return extracted_text
    
    def _extract_table_text(self, table_element) -> str:       
        text_parts = []
        if hasattr(table_element, 'rows') and table_element.rows:
            for row in table_element.rows:
                row_texts = []
                if isinstance(row, list):
                    for cell in row:
                        if hasattr(cell, 'text_content') and cell.text_content:
                            cell_text = str(cell.text_content).strip()
                            if cell_text and cell_text != 'None':
                                row_texts.append(cell_text)                   
                    if row_texts:
                        text_parts.append(' '.join(row_texts))
        
        return '\n'.join(text_parts)
    
    def _clean_text(self, text: str) -> str:       
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        text = text.strip()  
        text = re.sub(r'[†‡•▪▫]', '', text)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
        
        return text
    
    def _has_table_structure(self, text: str) -> bool:       
        if not text:
            return False
            
        lines = text.split('\n')
        table_indicators = [
            len([line for line in lines if '|' in line]) > 2,
            len([line for line in lines if '\t' in line]) > 2, 
            len([line for line in lines if re.search(r'\s{5,}', line)]) > 2,
            bool(re.search(r'(?i)(column|row|table|header)', text))
        ]
        
        return sum(table_indicators) >= 2
    
    def _has_form_structure(self, text: str) -> bool:        
        if not text:
            return False      
        form_indicators = [
            'sign in' in text.lower(),
            'please' in text.lower() and ('fill' in text.lower() or 'complete' in text.lower()),
            len(re.findall(r':\s*$', text, re.MULTILINE)) > 2,
            any(word in text.lower() for word in ['name:', 'date:', 'time:', 'reason:'])
        ]
        
        return sum(form_indicators) >= 2
    
    def _generate_metadata(self, dom: DocumentObjectModel, document_type: str, structure: Dict) -> Dict[str, Any]:       
        return {
            "original_filename": dom.file_name,
            "file_hash": dom.file_hash,
            "processed_timestamp": dom.processed_timestamp,
            "content_type": dom.detected_content_type,
            "language": dom.detected_language,
            "page_count": dom.page_count,
            "document_classification": {
                "type": document_type,
                "structure_complexity": structure["estimated_complexity"],
                "has_structured_data": structure["has_tables"] or structure["has_forms"],
                "content_density": structure["text_density"]
            },
            "processing_metadata": {
                "agent_version": self.version,
                "processing_method": "rule_based_classification",
                "confidence_metrics": {
                    "type_classification": "rule_based",
                    "structure_detection": "pattern_matching"
                }
            }
        }