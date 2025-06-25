"""Agent implementations with reasoning and planning capabilities."""

from typing import Dict, Any, List, Optional, Union, TypedDict, Annotated
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import AnyMessage, add_messages
# from langgraph.checkpoint import MemorySaver  # Not available in current version
import logging
import re

from .task_types import TaskType
from .tools import AVAILABLE_TOOLS, BaseTool
from .memory import IntegratedMemorySystem


logger = logging.getLogger(__name__)


# Define a more structured state for the agent
class AgentState(TypedDict):
    messages: List[BaseMessage]
    intermediate_steps: List[tuple[str, str]]

# The prompt that drives the ReAct logic
REACT_PROMPT = """
You are Atomia, an advanced educational AI agent. Your goal is to execute a plan to help a student learn.
You must break down the plan into smaller steps, thinking step-by-step and using specialized tools to accomplish each part.

Your tools are:
{tools}

Follow this format for your response:

Thought: Analyze the current situation, the plan, and what you need to do next. This is your internal monologue.
Action:
```json
{{
  "tool_name": "tool_to_use",
  "tool_input": "input for the tool"
}}
```

After an action, you will receive an Observation. You will then repeat the Thought/Action process.
If you have gathered enough information to answer the user's request, provide a final, comprehensive answer prefixed with "Final Answer:".

---
Plan:
{plan}

Previous Steps (Action/Observation History):
{intermediate_steps}

User Request:
{user_input}

Begin!
"""

class AtomiaAgent:
    """Main educational agent with reasoning capabilities."""
    
    def __init__(self, llm, **kwargs):
        self.llm = llm
        self.tools = {tool.name: tool for tool in AVAILABLE_TOOLS}
        self.workflow = self._build_workflow()
        logging.info("AtomiaAgent initialized.")

    def _get_tools_string(self):
        return "\\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools.values()])

    def _parse_action(self, text: str):
        action_match = re.search(r"Action:\n```json\n(.*?)\n```", text, re.DOTALL)
        if action_match:
            import json
            try:
                action_data = json.loads(action_match.group(1))
                return action_data['tool_name'], action_data['tool_input']
            except (json.JSONDecodeError, KeyError):
                return None, None
        return None, None

    def _build_workflow(self) -> StateGraph:
        graph = StateGraph(AgentState)
        graph.add_node("agent", self._agent_node)
        graph.add_node("tool_executor", self._tool_node)

        graph.set_entry_point("agent")
        graph.add_conditional_edges(
            "agent",
            self._should_continue,
            {"continue": "tool_executor", "end": END}
        )
        graph.add_edge("tool_executor", "agent")
        
        return graph.compile()

    def _should_continue(self, state: AgentState) -> str:
        # The agent node returns a list of AIMessages. If the list contains a tool call, continue.
        # Otherwise, end. This logic needs to be based on the content of the messages.
        if isinstance(state['messages'][-1], AIMessage) and state['messages'][-1].tool_calls:
            return "continue"
        return "end"

    async def _agent_node(self, state: AgentState) -> dict:
        # This implementation needs to use the LLM with tool-calling capabilities
        # For now, this is a simplified stub
        response = await self.llm.ainvoke(state['messages'])
        return {'messages': [response]}

    async def _tool_node(self, state: AgentState) -> dict:
        # Simplified tool execution
        tool_call = state['messages'][-1].tool_calls[0]
        tool = self.tools[tool_call['name']]
        observation = tool.run(tool_call['args'])
        return {'messages': [HumanMessage(content=str(observation), name="tool_observation")]}

    async def process(self, messages: List[BaseMessage], **kwargs):
        """Main entry point for the agent's workflow."""
        # The workflow expects a dictionary with a 'messages' key.
        return await self.workflow.ainvoke({"messages": messages})

    def _get_context_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation of _get_context_node method
        # This method should return the context node for the given state
        # Implementation details are not provided in the original file or the code block
        # This method should be implemented based on the specific requirements of the workflow
        # For now, we'll return an empty dictionary as a placeholder
        return {}

    def _finalize_node(self, state: dict) -> dict:
        """Prepares the final output of the agent."""
        state["final_output"] = "\\n".join(state["observations"])
        return state

    # ... rest of the existing code ... 