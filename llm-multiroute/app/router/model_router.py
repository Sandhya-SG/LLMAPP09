from enum import Enum

from app.config import settings


class TaskType(str, Enum):
    CLASSIFY = "classify"
    SENTIMENT = "sentiment"
    SUMMARIZE = "summarize"
    INTENT = "intent"


class ModelRouter:
    def __init__(self):
        self._route_map: dict[TaskType, str] = {
            TaskType.CLASSIFY: settings.OLLAMA_MODEL_CLASSIFY,
            TaskType.SENTIMENT: settings.OLLAMA_MODEL_SENTIMENT,
            TaskType.SUMMARIZE: settings.OLLAMA_MODEL_SUMMARIZE,
            TaskType.INTENT: settings.OLLAMA_MODEL_INTENT,
        }

    def get_model(self, task_type: TaskType) -> str:
        return self._route_map[task_type]

    def get_routes(self) -> dict[str, str]:
        return {task.value: model for task, model in self._route_map.items()}


model_router = ModelRouter()
