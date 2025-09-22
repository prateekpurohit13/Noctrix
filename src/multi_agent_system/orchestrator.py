from typing import Dict, Optional, Any, Callable
from queue import Queue
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentRegistry
from ..common.models import DocumentObjectModel


class ProcessingPipeline:   
    def __init__(self):
        self.stages = [
            {
                "name": "document_understanding",
                "agent_capability": "document_analysis",
                "required": True,
                "timeout_seconds": 30,
                "description": "OCR processing, document type detection, structure analysis"
            },
            {
                "name": "analysis",
                "agent_capability": "comprehensive_analysis",
                "required": True,
                "timeout_seconds": 600,
                "description": "Perform PII, Security, and Relationship analysis in one step."
            },
            # {
            #     "name": "pii_detection", 
            #     "agent_capability": "pii_extraction",
            #     "required": True,
            #     "timeout_seconds": 180,
            #     "description": "Extract names, emails, phone numbers, SSN"
            # },
            # {
            #     "name": "security_entities",
            #     "agent_capability": "security_analysis", 
            #     "required": True,
            #     "timeout_seconds": 180,
            #     "description": "Extract IPs, hostnames, IAM policies, network configs"
            # },
            # {
            #     "name": "relationship_mapping",
            #     "agent_capability": "relationship_analysis",
            #     "required": False,
            #     "timeout_seconds": 180,
            #     "description": "Build entity relationships and semantic graphs"
            # },
            {
                "name": "security_assessment",
                "agent_capability": "security_risk_assessment",
                "required": True,
                "timeout_seconds": 3600,
                "description": "Analyze extracted entities for security risks and vulnerabilities."
            },
            {
                "name": "anonymization",
                "agent_capability": "anonymization",
                "required": True, 
                "timeout_seconds": 180,
                "description": "Apply consistent anonymization strategies"
            }
        ]


class AgentOrchestrator:
    def __init__(self, max_workers: int = 5):
        self.registry = AgentRegistry()
        self.pipeline = ProcessingPipeline()
        self.task_queue = Queue()
        self.result_cache: Dict[str, AgentResult] = {}
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.is_running = False
        self.progress_callback: Optional[Callable] = None
        
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
        print(f"   Pipeline ID: {document_id}")
        
        pipeline_results = {
            "document_id": document_id,
            "file_name": dom.file_name,
            "started_at": datetime.now().isoformat(),
            "stages": {},
        }
        
        start_time = time.time()
        
        try:
            stage_data = {"dom": dom}
            
            for i, stage_config in enumerate(self.pipeline.stages):
                stage_name = stage_config["name"]
                capability = stage_config["agent_capability"]
                is_required = stage_config["required"]
                timeout = stage_config["timeout_seconds"]              
                progress = (i / len(self.pipeline.stages)) * 100
                self._report_progress(stage_name, progress, f"Starting {stage_config['description']}")                
                print(f"  -> Stage {i+1}/{len(self.pipeline.stages)}: {stage_name}")
               
                capable_agents = self.registry.get_agents_by_capability(capability)               
                if not capable_agents:
                    error_msg = f"No healthy agents found for capability: {capability}"
                    print(f"     ❌ {error_msg}")
                    pipeline_results["stages"][stage_name] = {"status": "failed", "error": error_msg}
                    if is_required: break
                    else: continue
                
                agent = capable_agents[0]
                task = AgentTask(
                    task_id=f"{document_id}_{stage_name}",
                    task_type=stage_name,
                    input_data=stage_data,
                    timeout_seconds=timeout
                )
                
                stage_start = time.time()                
                try:
                    future = self.executor.submit(agent._execute_with_timeout, task)
                    result = future.result(timeout=timeout + 5)
                    stage_time = int((time.time() - stage_start) * 1000)                   
                    if result.is_success():
                        print(f"Completed in {stage_time}ms")
                        pipeline_results["stages"][stage_name] = {
                            "status": "completed",
                            "agent_id": result.agent_id,
                            "agent_name": agent.agent_name,
                            "execution_time_ms": stage_time,
                            "output": result.data
                        }
                        if result.data:
                            stage_data.update(result.data)
                    else:
                        print(f"Agent failed: {result.error_message}")
                        pipeline_results["stages"][stage_name] = {"status": "failed", "agent_id": result.agent_id, "error": result.error_message}
                        if is_required: break
                except (FutureTimeoutError, TimeoutError):
                    stage_time = int((time.time() - stage_start) * 1000)
                    print(f"Stage timed out after {stage_time}ms")
                    pipeline_results["stages"][stage_name] = {"status": "timeout", "agent_id": agent.agent_id, "execution_time_ms": stage_time}
                    if is_required: break
                except Exception as e:
                    stage_time = int((time.time() - stage_start) * 1000)
                    print(f"Stage error: {str(e)}")
                    pipeline_results["stages"][stage_name] = {"status": "error", "error": str(e)}
                    if is_required: break
                if 'result' in locals():
                    self.registry.update_stats(result)
            total_time = int((time.time() - start_time) * 1000)
            final_entities = stage_data.get("anonymized_entities", stage_data.get("entities", []))
            
            pipeline_results.update({
                "completed_at": datetime.now().isoformat(),
                "processing_summary": {
                    "total_time_ms": total_time,
                    "stages_completed": sum(1 for s in pipeline_results["stages"].values() if s["status"] == "completed"),
                    "stages_failed": sum(1 for s in pipeline_results["stages"].values() if s["status"] in ["failed", "timeout", "error"]),
                    "total_entities_found": len(final_entities),
                    "total_relationships_found": len(stage_data.get("relationships", []))
                }
            })

            print(f"Multi-Agent Processing Complete:")
            print(f"   - Total entities found: {len(final_entities)}")
            print(f"   - Processing time: {total_time}ms")
            self._report_progress("complete", 100.0, "Processing complete")
            
            return pipeline_results
            
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            pipeline_results["completed_at"] = datetime.now().isoformat()
            pipeline_results["error"] = str(e)           
            print(f"Pipeline failed: {str(e)}")
            return pipeline_results
    
    def get_system_status(self) -> Dict[str, Any]:
        healthy_agents = self.registry.get_healthy_agents()
        all_agents = list(self.registry.agents.values())
        
        return {
            "total_agents": len(all_agents),
            "healthy_agents": len(healthy_agents),
            "agent_details": [agent.get_info() for agent in all_agents],
            "pipeline_stages": len(self.pipeline.stages),
            "max_workers": self.max_workers,
            "system_healthy": len(healthy_agents) >= 3
        }