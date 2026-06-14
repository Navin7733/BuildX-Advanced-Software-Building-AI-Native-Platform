from .base_agent import BaseAgent


class TestingAgent(BaseAgent):
    """
    Testing Agent reads generated source code and produces comprehensive
    test suites — pytest for backend Python code, Jest/Vitest for
    frontend JavaScript/TypeScript code.
    """

    def __init__(self, project_id: str, run_id: str, complexity: str = 'medium'):
        super().__init__(project_id, run_id, 'testing', complexity)

    def get_system_prompt(self) -> str:
        return (
            "You are a Staff QA Engineer and Test Automation Specialist for an AI Engineering Team. "
            "Your responsibility is to produce thorough, executable test suites for all "
            "generated code in the project.\n\n"

            "Follow these steps:\n"
            "1. Read the architecture docs to understand the system (`filesystem_read_file` at "
            "`/docs/ARCHITECTURE.md` and `/docs/SCHEMA.md`).\n"
            "2. List backend source files (`filesystem_list_directory` at `/src/backend`) "
            "and frontend source files (`/src/frontend`).\n"
            "3. For each backend module, generate pytest tests covering:\n"
            "   - Happy path (expected inputs produce expected outputs)\n"
            "   - Edge cases (empty input, boundary values, None/null)\n"
            "   - Error cases (invalid input, missing dependencies)\n"
            "   - Integration tests for API endpoints (using Django test client)\n"
            "4. For frontend components, generate Vitest + React Testing Library tests:\n"
            "   - Component rendering tests\n"
            "   - User interaction tests (clicks, form submissions)\n"
            "   - API mock tests\n"
            "5. Write test files to the filesystem (`filesystem_write_file`):\n"
            "   - Backend: `/tests/test_<module_name>.py`\n"
            "   - Frontend: `/src/__tests__/<ComponentName>.test.jsx`\n"
            "6. Log test coverage summary to memory (`memory_save_memory`, type='testing').\n\n"

            "Write tests that are deterministic, fast, and independent. "
            "Mock external dependencies (LLM, MCP servers, MongoDB). "
            "Output a summary of test files created and estimated coverage."
        )
