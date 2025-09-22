from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import time
from datetime import datetime


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class AgentResult:
    agent_id: str
    task_id: str
    status: TaskStatus
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def is_success(self) -> bool:
        return self.status == TaskStatus.COMPLETED and self.error_message is None


@dataclass 
class AgentTask:
    task_id: str
    task_type: str
    input_data: Dict[str, Any]
    priority: int = 1
    timeout_seconds: int = 60
    retry_count: int = 0
    max_retries: int = 2
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class BaseAgent(ABC):
    def __init__(self, agent_name: str, version: str = "1.0.0"):
        self.agent_id = f"{agent_name}_{uuid.uuid4().hex[:8]}"
        self.agent_name = agent_name
        self.version = version
        self.capabilities = self._define_capabilities()
        self.is_healthy = True
        self.created_at = datetime.now()
        
    @abstractmethod
    def _define_capabilities(self) -> List[str]:
        pass
    
    @abstractmethod
    def process(self, task: AgentTask) -> AgentResult:
        pass
    
    def health_check(self) -> bool:
        try:
            return self.is_healthy
        except Exception:
            self.is_healthy = False
            return False
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "version": self.version,
            "capabilities": self.capabilities,
            "is_healthy": self.is_healthy,
            "created_at": self.created_at.isoformat()
        }
    
    def _create_result(
        self, 
        task: AgentTask, 
        status: TaskStatus, 
        data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            task_id=task.task_id,
            status=status,
            data=data,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
            metadata={
                "agent_name": self.agent_name,
                "agent_version": self.version,
                "task_type": task.task_type,
                "retry_count": task.retry_count
            }
        )
    
    def _execute_with_timeout(self, task: AgentTask) -> AgentResult:
        start_time = time.time()
        
        try:
            if not self.health_check():
                return self._create_result(
                    task, 
                    TaskStatus.FAILED, 
                    error_message=f"Agent {self.agent_name} is not healthy"
                )
            result = self.process(task)
            execution_time = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time
            
            return result
            
        except TimeoutError:
            return self._create_result(
                task,
                TaskStatus.TIMEOUT,
                error_message=f"Task timed out after {task.timeout_seconds} seconds"
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return self._create_result(
                task,
                TaskStatus.FAILED,
                error_message=f"Agent execution failed: {str(e)}",
                execution_time_ms=execution_time
            )


class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_stats: Dict[str, Dict] = {}
    
    def register_agent(self, agent: BaseAgent) -> bool:
        try:
            self.agents[agent.agent_id] = agent
            self.agent_stats[agent.agent_id] = {
                "tasks_processed": 0,
                "tasks_failed": 0,
                "total_execution_time_ms": 0,
                "last_used": None
            }
            return True
        except Exception:
            return False
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        return self.agents.get(agent_id)
    
    def get_healthy_agents(self) -> List[BaseAgent]:
        return [agent for agent in self.agents.values() if agent.health_check()]
    
    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        return [
            agent for agent in self.agents.values() 
            if capability in agent.capabilities and agent.health_check()
        ]
    
    def update_stats(self, result: AgentResult):
        agent_id = result.agent_id
        if agent_id in self.agent_stats:
            stats = self.agent_stats[agent_id]
            stats["tasks_processed"] += 1
            if result.status == TaskStatus.FAILED:
                stats["tasks_failed"] += 1
            if result.execution_time_ms:
                stats["total_execution_time_ms"] += result.execution_time_ms
            stats["last_used"] = datetime.now().isoformat()