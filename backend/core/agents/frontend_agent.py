from .base_agent import BaseAgent

class FrontendAgent(BaseAgent):
    """
    Frontend Agent reads Architecture and UI requirements, then
    generates React JS components, pages, and routing.
    """
    def __init__(self, project_id: str, run_id: str, complexity: str = 'medium'):
        super().__init__(project_id, run_id, 'frontend', complexity)

    def get_system_prompt(self) -> str:
        return (
            "You are a Staff Frontend Engineer for an AI Engineering Team. "
            "Your task is to implement the React user interface.\n\n"
            
            "Follow these steps:\n"
            "1. Read `/docs/ARCHITECTURE.md` and `/docs/PRD.md` (`filesystem_read_file`).\n"
            "2. Generate modern, beautiful React components using Tailwind/CSS.\n"
            "3. Write the code to the filesystem (`filesystem_write_file`).\n"
            "4. Ensure components are modular and responsive.\n"
            "5. Log your progress to memory (`memory_save_memory`).\n\n"
            
            "Focus on excellent user experience, rich aesthetics, and clean state management. "
            "Output a summary of the components and pages created."
        )
