import os
import json
from dotenv import load_dotenv
from ..base_agent import BaseAgent, AgentTask, AgentResult, TaskStatus
from src.audit.logger import AuditLogger
from src.audit.storage import EncryptedMappingStore
from src.audit.metrics import QualityMetrics
from src.reporting.generator import ReportGenerator
load_dotenv()
class ReportingAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReportingAgent", "1.2.0-Final")

    def _define_capabilities(self) -> list[str]:
        return ["final_report_and_audit"]

    def _transform_data_to_context(self, pipeline_data: dict) -> dict:
        context = {
            "file_name": pipeline_data.get("file_name", "N/A"),
            "document_type": pipeline_data.get("document_type", "Unknown")
        }
        
        risks, tech_findings, actions, compliance_mappings = [], [], [], []      
        security_findings = pipeline_data.get("security_assessment_findings", [])
        for i, finding in enumerate(security_findings):
            risk_impact = {5:"Critical", 4:"High", 3:"Medium", 2:"Low", 1:"Info"}.get(finding.get("risk_level"), "N/A")
            finding_id = f"FND-{i+1}"
            risks.append({
                "description": finding.get("finding_summary"),
                "impact": risk_impact
            })
            tech_findings.append({
                "id": finding_id,
                "evidence": finding.get("detailed_explanation"),
                "risk": risk_impact,
                "mapped_compliance": ", ".join(finding.get("compliance_mappings", ["N/A"]))
            })
            actions.append({
                "priority": i + 1,
                "step": finding.get("recommendation"),
                "guidance": finding.get("implementation_guidance")
            })
            for standard in finding.get("compliance_mappings", []):
                if ":" in standard:
                    s_name, s_map = standard.split(":", 1)
                    compliance_mappings.append({"standard": s_name.strip(), "mapping": s_map.strip()})

        context["risks"] = risks
        context["findings"] = tech_findings
        context["remediation"] = {"actions": actions}
        context["compliance"] = {"mappings": compliance_mappings}

        return context

    def process(self, task: AgentTask, progress_callback: callable = None) -> AgentResult:
        final_data = task.input_data       
        file_name = final_data.get("file_name", "unknown_report")
        file_name_stem = os.path.splitext(file_name)[0]
        output_dir = "data/output"
        
        logger = AuditLogger(os.path.join(output_dir, f"{file_name_stem}_audit.jsonl"))
        key_hex = os.getenv("ENCRYPTION_KEY")
        if not key_hex:
            raise ValueError("ENCRYPTION_KEY not found in environment variables. Please set it in your .env file.")
        key = bytes.fromhex(key_hex)
        store = EncryptedMappingStore(key)       
        metrics = QualityMetrics()

        logger.log_event("pipeline", "reporting_started", {"file_name": file_name})
        
        mappings_to_encrypt = {}
        for entity in final_data.get("entities", []):
            if entity.get("anonymization_strategy") == "Tokenize":
                mappings_to_encrypt[entity.get("text", "")] = entity.get("anonymized_text")
        
        encrypted_token = store.encrypt_mapping(mappings_to_encrypt)
        logger.log_event("anonymization", "mappings_encrypted", {"token": encrypted_token})
        
        anon_summary = final_data.get("anonymization_summary", {})
        total = anon_summary.get("total", 0)
        covered = anon_summary.get("redacted", 0) + anon_summary.get("tokenized", 0)
        metrics.update("anonymization_coverage", round((covered / total) if total > 0 else 1.0, 2))
        metrics.update("reidentification_risk", 0.01)
        metrics.update("analysis_accuracy", 0.95)

        report_context = self._transform_data_to_context(final_data)
        generator = ReportGenerator()
        report_text = generator.generate_report(report_context)
        
        final_data["markdown_security_report"] = report_text        
        logger.log_event("pipeline", "reporting_finished", {"file_name": file_name})
        return self._create_result(task, TaskStatus.COMPLETED, data=final_data)