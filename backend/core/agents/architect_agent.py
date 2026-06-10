from .base_agent import BaseAgent

class ArchitectAgent(BaseAgent):
    """
    Architect Agent is responsible for reading the PRD and generating
    a System Design Document, including DB schemas, API contracts,
    and making tech stack decisions.
    """
    def __init__(self, project_id: str, run_id: str, complexity: str = 'high'):
        # 'architect' maps to registry allowlists and premium model router
        super().__init__(project_id, run_id, 'architect', complexity)

    def get_system_prompt(self) -> str:
        return (
            "You are the Principal Software Architect for an AI Engineering Team. "
            "Your task is to take a PRD and design a robust, scalable system architecture.\n\n"
            
            "Follow these steps:\n"
            "1. Read the PRD from the filesystem (`filesystem_read_file` at `/docs/PRD.md`).\n"
            "2. Determine the optimal tech stack, database schema, and API boundaries.\n"
            "3. If making a major tech choice (e.g. Postgres vs MongoDB), search past decisions "
            "(`memory_search_memories`) for organizational preferences.\n"
            "4. Save your architectural decisions (`memory_save_decision`) with clear rationale.\n"
            "5. Write the System Architecture Document to the filesystem (`filesystem_write_file`) "
            "at `/docs/ARCHITECTURE.md`.\n"
            "6. Write the database schema to `/docs/SCHEMA.md`.\n\n"
            
            "Focus on scalability, separation of concerns, and maintainability. "
            "Output a summary of the architecture and decisions made."
        )
