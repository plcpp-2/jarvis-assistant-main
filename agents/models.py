from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

class TaskType(Enum):
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    EXECUTION = "execution"
    LEARNING = "learning"
    MONITORING = "monitoring"
    COORDINATION = "coordination"
    CUSTOM = "custom"

class AgentRole(Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCHER = "researcher"
    ANALYZER = "analyzer"
    EXECUTOR = "executor"
    MONITOR = "monitor"
    LEARNER = "learner"
    CUSTOM = "custom"

@dataclass
class TaskResult:
    success: bool
    data: Any
    metrics: Dict[str, float]
    error: Optional[str] = None

@dataclass
class Task:
    id: str
    type: TaskType
    title: str
    description: str
    assigned_to: str
    created_by: str
    status: str
    priority: int
    dependencies: List[str]
    created_at: str
    parameters: Dict[str, Any]
    completed_at: Optional[str] = None
    result: Optional[TaskResult] = None

@dataclass
class AgentMetrics:
    tasks_completed: int
    success_rate: float
    avg_processing_time: float
    learning_progress: float
