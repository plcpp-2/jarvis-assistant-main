import asyncio
from datetime import datetime
from typing import Dict
from sklearn.ensemble import RandomForestClassifier

from .models import AgentRole, Task, TaskResult, AgentMetrics


class Agent:
    def __init__(self, system, agent_id: str, name: str, role: AgentRole):
        self.system = system
        self.id = agent_id
        self.name = name
        self.role = role
        self.status = "active"
        self.capabilities = set()
        self.task_queue = asyncio.Queue()
        self.message_queue = asyncio.Queue()
        self.learning_model = None
        self.metrics = AgentMetrics(0, 0.0, 0.0, 0.0)

        # Initialize agent-specific learning
        self.initialize_learning()

    def initialize_learning(self):
        """Initialize agent's learning capabilities"""
        if self.role in [AgentRole.ANALYZER, AgentRole.LEARNER]:
            self.learning_model = RandomForestClassifier()
            self.training_data = []
            self.performance_history = []

    async def process_task(self, task: Task) -> TaskResult:
        """Process task with learning and metrics tracking"""
        start_time = datetime.now()

        try:
            # Predict task difficulty and resource needs
            task_features = self.extract_task_features(task)
            difficulty_prediction = self.predict_task_difficulty(task_features)

            # Adjust processing based on predictions
            if difficulty_prediction > 0.7:
                await self.request_additional_resources(task)

            # Process task based on type
            result = await self.execute_task_logic(task)

            # Learn from execution
            self.update_learning(task, result)

            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_metrics(True, processing_time)

            return result

        except Exception as e:
            self.update_metrics(False, (datetime.now() - start_time).total_seconds())
            return TaskResult(False, None, {}, str(e))

    def extract_task_features(self, task: Task) -> Dict:
        """Extract features for task prediction"""
        return {
            "type": task.type.value,
            "priority": task.priority,
            "dependency_count": len(task.dependencies),
            "parameter_count": len(task.parameters),
        }

    def predict_task_difficulty(self, features: Dict) -> float:
        """Predict task difficulty based on features"""
        if self.learning_model and self.training_data:
            return self.learning_model.predict_proba([list(features.values())])[0][1]
        return 0.5

    async def request_additional_resources(self, task: Task):
        """Request additional resources for complex tasks"""
        await self.system.orchestrator.allocate_resources(self.id, task.id)

    def update_learning(self, task: Task, result: TaskResult):
        """Update learning model with task results"""
        if self.learning_model:
            features = self.extract_task_features(task)
            self.training_data.append((features, result.success))

            if len(self.training_data) >= 10:
                self.train_model()

    def train_model(self):
        """Train the agent's learning model"""
        X = [list(f.values()) for f, _ in self.training_data]
        y = [success for _, success in self.training_data]
        self.learning_model.fit(X, y)

    async def execute_task_logic(self, task: Task) -> TaskResult:
        """Override this method in specific agent implementations"""
        raise NotImplementedError

    def update_metrics(self, success: bool, processing_time: float):
        """Update agent metrics"""
        self.metrics.tasks_completed += 1
        self.metrics.success_rate = (
            self.metrics.success_rate * (self.metrics.tasks_completed - 1) + int(success)
        ) / self.metrics.tasks_completed
        self.metrics.avg_processing_time = (
            self.metrics.avg_processing_time * (self.metrics.tasks_completed - 1) + processing_time
        ) / self.metrics.tasks_completed
