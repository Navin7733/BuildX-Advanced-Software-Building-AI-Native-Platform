"""
LLM Model Router
Routes tasks to appropriate models based on complexity and cost.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class ModelRouter:
    @staticmethod
    def get_model_for_task(task_type: str, complexity: str = 'medium') -> str:
        """
        Determines the best model based on the task and complexity.
        This saves cost by using cheaper models (e.g. Llama/Mistral/GPT-4o-mini)
        for simpler tasks and Claude 3.5 Sonnet / GPT-4o for complex reasoning.
        """
        premium = settings.LLM_PREMIUM_MODEL
        default = settings.LLM_DEFAULT_MODEL
        fast = settings.LLM_FAST_MODEL
        
        # High-stakes reasoning tasks get premium models
        if task_type in ['architect', 'reviewer']:
            return premium
            
        # Fast, structured, low-stakes tasks
        if task_type in ['memory', 'documentation']:
            return default
            
        # Developer tasks depend on complexity
        if task_type in ['planner', 'frontend', 'backend_dev', 'testing']:
            if complexity == 'high':
                return premium
            return default
            
        return default
