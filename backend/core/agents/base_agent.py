"""
Base LangGraph Agent for BuildX
Provides the common StateGraph structure and MCP tool integration.
"""
import logging
from typing import TypedDict, Annotated, Sequence
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation

from core.llm.client import get_llm
from core.llm.router import ModelRouter
from core.mcp.tool_adapter import get_tools_for_agent
from core.memory.short_term import ShortTermMemory

logger = logging.getLogger(__name__)


# ─── State Definition ──────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    project_id: str
    run_id: str
    agent_type: str
    current_plan: str
    review_feedback: str
    iteration: int


class BaseAgent:
    """
    Base class for all BuildX agents using LangGraph.
    Implements a standard Plan -> Execute -> Review loop with MCP tools.
    """
    def __init__(self, project_id: str, run_id: str, agent_type: str, complexity: str = 'medium'):
        self.project_id = project_id
        self.run_id = run_id
        self.agent_type = agent_type
        
        # 1. Setup Memory
        self.stm = ShortTermMemory(project_id, run_id)
        
        # 2. Setup LLM via Router
        model_name = ModelRouter.get_model_for_task(agent_type, complexity)
        self.llm = get_llm(model=model_name)
        
        # 3. Load MCP Tools for this specific agent
        self.tools = get_tools_for_agent(agent_type, project_id, run_id)
        self.tool_executor = ToolExecutor(self.tools) if self.tools else None
        
        # Bind tools to LLM if available
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

        # 4. Build LangGraph
        self.graph = self._build_graph()

    def get_system_prompt(self) -> str:
        """Override in subclasses to provide specific system instructions."""
        return f"You are a helpful {self.agent_type} agent."

    def _build_graph(self):
        """Constructs the standard Agent workflow graph."""
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("agent", self.call_model)
        if self.tools:
            workflow.add_node("tools", self.call_tools)

        # Set entry point
        workflow.set_entry_point("agent")

        # Define edges
        if self.tools:
            workflow.add_conditional_edges(
                "agent",
                self.should_continue,
                {
                    "continue": "tools",
                    "end": END
                }
            )
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)

        return workflow.compile()

    def call_model(self, state: AgentState):
        """Invoke the LLM with the current state messages and system prompt."""
        messages = state['messages']
        
        # Ensure system prompt is present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=self.get_system_prompt())] + list(messages)

        response = self.llm_with_tools.invoke(messages)
        
        # Save to short term memory for real-time tracking
        self.stm.append_list('messages', {'role': 'assistant', 'content': response.content})
        
        return {"messages": [response], "iteration": state.get("iteration", 0) + 1}

    def call_tools(self, state: AgentState):
        """Execute the tool calls requested by the LLM."""
        messages = state['messages']
        last_message = messages[-1]

        # Process all tool calls in the last message
        tool_responses = []
        for tool_call in last_message.tool_calls:
            action = ToolInvocation(
                tool=tool_call["name"],
                tool_input=tool_call["args"],
            )
            logger.info(f"Agent {self.agent_type} calling MCP tool: {action.tool}")
            
            # Execute via ToolExecutor (which uses the MCP Client under the hood)
            response = self.tool_executor.invoke(action)
            
            # Convert response to tool message
            from langchain_core.messages import ToolMessage
            tool_responses.append(ToolMessage(
                content=str(response),
                name=action.tool,
                tool_call_id=tool_call["id"]
            ))

        return {"messages": tool_responses}

    def should_continue(self, state: AgentState):
        """Determine whether to use tools or end."""
        messages = state['messages']
        last_message = messages[-1]
        
        # If there is a tool call, continue to 'tools' node
        if "tool_calls" in last_message.additional_kwargs or hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
            
        # Otherwise end
        return "end"

    def run(self, input_text: str) -> str:
        """Execute the agent workflow."""
        logger.info(f"Running {self.agent_type} agent. Input: {input_text}")
        
        initial_state = {
            "messages": [HumanMessage(content=input_text)],
            "project_id": self.project_id,
            "run_id": self.run_id,
            "agent_type": self.agent_type,
            "iteration": 0
        }
        
        # Save input to STM
        self.stm.append_list('messages', {'role': 'user', 'content': input_text})

        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        # Return the final message content
        final_message = final_state["messages"][-1]
        return final_message.content
