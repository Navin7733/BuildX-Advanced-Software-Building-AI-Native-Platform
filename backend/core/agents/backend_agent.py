from .base_agent import BaseAgent

class BackendAgent(BaseAgent):
    """
    Backend Agent reads the Architecture and Schema docs, then
    generates Django models, views, and API logic.
    """
    def __init__(self, project_id: str, run_id: str, complexity: str = 'medium'):
        super().__init__(project_id, run_id, 'backend_dev', complexity)

    def get_system_prompt(self) -> str:
        return (
            "You are a Staff Backend Engineer for an AI Engineering Team. "
            "Your task is to implement the backend APIs and database models.\n\n"
            
            "Follow these steps:\n"
            "1. Read `/docs/ARCHITECTURE.md` and `/docs/SCHEMA.md` (`filesystem_read_file`).\n"
            "2. Generate the necessary Django models, serializers, and views.\n"
            "3. Write the code to the filesystem (`filesystem_write_file`).\n"
            "4. Validate your schema using the Database MCP server (`database_validate_schema`).\n"
            "5. Log your progress to memory (`memory_save_memory`).\n\n"
            
            "Write production-grade code with error handling, logging, and type hints. "
            "Output a summary of the endpoints created."
        )
