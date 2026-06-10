from .base_agent import BaseAgent

class MemoryAgent(BaseAgent):
    """
    Memory Agent runs asynchronously after workflows to consolidate,
    tag, and embed new memories and decisions.
    """
    def __init__(self, project_id: str, run_id: str, complexity: str = 'medium'):
        super().__init__(project_id, run_id, 'memory', complexity)

    def get_system_prompt(self) -> str:
        return (
            "You are the Memory Agent for an AI Engineering Team. "
            "Your task is to review recent project activity and consolidate it into long-term memory.\n\n"
            
            "Follow these steps:\n"
            "1. Review recent agent logs and outputs.\n"
            "2. Identify key decisions, bugs, refactoring patterns, and team conventions.\n"
            "3. Use `memory_save_memory` and `memory_save_decision` to store these insights cleanly.\n"
            "4. Deduplicate any redundant information.\n\n"
            
            "Focus on extracting 'why' decisions were made, not just 'what' was done. "
            "Output a summary of memories consolidated."
        )
