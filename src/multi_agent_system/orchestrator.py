import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Dict, Any, Callable
from .base_agent import BaseAgent, AgentTask, AgentRegistry
from ..common.models import DocumentObjectModel

class ProcessingPipeline:
    def __init__(self):
        self.stages = [
            {
                "name": "document_understanding", 
                "agent_capability": "document_analysis",
                "required": True, "timeout_seconds": 30, 
                "description": "Initial text extraction and classification"
            },
            {
                "name": "analysis", 
                "agent_capability": "comprehensive_analysis",
                "required": True, "timeout_seconds": 3600, 
                "description": "Perform comprehensive PII, Security, and Relationship analysis."
            },
            {
                "name": "security_assessment", 
                "agent_capability": "security_risk_assessment",
                "required": True, "timeout_seconds": 3600, 
                "description": "Analyze extracted entities for security risks and vulnerabilities."
            },
            {
                "name": "anonymization", 
                "agent_capability": "anonymization",
                "required": True, "timeout_seconds": 30, 
                "description": "Apply consistent anonymization strategies"
            },
            {
                "name": "final_reporting", 
                "agent_capability": "final_report_and_audit",
                "required": True, "timeout_seconds": 120, 
                "description": "Generate final PDF report and audit logs."
            }
        ]

class AgentOrchestrator:
    def __init__(self, max_workers: int = 1):
        self.registry = AgentRegistry()
        self.pipeline = ProcessingPipeline()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.progress_callback: Callable[[str, float, str], None] | None = None

    def register_agent(self, agent: BaseAgent) -> bool:
        return self.registry.register_agent(agent)

    def set_progress_callback(self, callback: Callable[[str, float, str], None]):
        self.progress_callback = callback

    def _report_progress(self, stage: str, progress: float, message: str):
        if self.progress_callback:
            try:
                self.progress_callback(stage, progress, message)
            except Exception as e:
                print(f"Progress callback error: {e}")

    def process_document(self, dom: DocumentObjectModel) -> Dict[str, Any]:
        document_id = f"doc_{int(time.time() * 1000)}"
        print(f"Starting Multi-Agent Processing Pipeline...")
        print(f"   Document: {dom.file_name}")
        
        pipeline_results = {
            "document_id": document_id,
            "file_name": dom.file_name,
            "started_at": datetime.now().isoformat(),
            "stages": {},
        }
        
        start_time = time.time()
        stage_data = {"dom": dom, "file_name": dom.file_name}
            
        for i, stage_config in enumerate(self.pipeline.stages):
            stage_name = stage_config["name"]           
            print(f"  -> Stage {i+1}/{len(self.pipeline.stages)}: {stage_name}")
            
            capable_agents = self.registry.get_agents_by_capability(stage_config["agent_capability"])
            if not capable_agents:
                error_msg = f"No healthy agents found for capability: {stage_config['agent_capability']}"
                print(f"     {error_msg}")
                pipeline_results["stages"][stage_name] = {"status": "failed", "error": error_msg}
                if stage_config["required"]: break
                else: continue
            
            agent = capable_agents[0]
            stage_start = time.time()
            task = AgentTask(
                task_id=f"{document_id}_{stage_name}",
                task_type=stage_name,
                input_data=stage_data,
                timeout_seconds=stage_config["timeout_seconds"]
            )
            
            try:
                future = self.executor.submit(agent._execute_with_timeout, task)
                result = future.result(timeout=task.timeout_seconds + 5)
                stage_time = int((time.time() - stage_start) * 1000)
                if result.is_success():
                    print(f"Completed in {stage_time}ms")
                    pipeline_results["stages"][stage_name] = {
                        "status": "completed", "agent_name": agent.agent_name,
                        "execution_time_ms": stage_time, "output": result.data
                    }
                    if result.data:
                        stage_data.update(result.data)
                else:
                    print(f"Agent failed: {result.error_message}")
                    pipeline_results["stages"][stage_name] = {"status": "failed", "error": result.error_message}
                    if stage_config["required"]: break
            
            except (FutureTimeoutError, TimeoutError):
                stage_time = int((time.time() - stage_start) * 1000)
                print(f"Stage timed out after {stage_time}ms")
                pipeline_results["stages"][stage_name] = {"status": "timeout", "execution_time_ms": stage_time}
                if stage_config["required"]: break
            except Exception as e:
                stage_time = int((time.time() - stage_start) * 1000)
                print(f"Stage error: {str(e)}")
                pipeline_results["stages"][stage_name] = {"status": "error", "error": str(e)}
                if stage_config["required"]: break
        
        total_time = int((time.time() - start_time) * 1000)
        final_entities = stage_data.get("entities", [])
        
        stage_statuses = [stage.get("status") for stage in pipeline_results["stages"].values()]
        if all(s == "completed" for s in stage_statuses):
            pipeline_status = "SUCCESS"
        elif any(s in ["failed", "timeout", "error"] for s in stage_statuses):
            pipeline_status = "PARTIAL"
        else:
            pipeline_status = "FAILED"

        final_reporting_output = pipeline_results["stages"].get("final_reporting", {}).get("output", {})
        total_entities_found = len(final_reporting_output.get("entities", []))
        final_reporting_output["pipeline_status"] = pipeline_status
        final_reporting_output["total_entities_found"] = total_entities_found
        output_json = {
            "file_name": pipeline_results.get("file_name"),
            "completed_at": datetime.now().isoformat(),
            "output": final_reporting_output,
        }
        return output_json