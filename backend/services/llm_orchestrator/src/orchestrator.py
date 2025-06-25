"""Main orchestrator for the LLM agent system."""

from typing import Dict, Any, Optional, List
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
import redis
import logging
import asyncio
import functools
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from .config import config
from .task_types import TaskType
from .agents import AtomiaAgent
from .memory import IntegratedMemorySystem


# Configurar logging estándar
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class AsyncAzureLLM:
    """Wrapper for Azure ChatCompletionsClient to make it async compatible."""
    def __init__(self, client, model_name):
        self._client = client
        self._model_name = model_name

    def _map_role(self, role: str) -> str:
        """Map LangChain role names to Azure/OpenAI role names."""
        if role == "human":
            return "user"
        if role == "ai":
            return "assistant"
        return role

    async def ainvoke(self, messages: List[BaseMessage]):
        # Convert LangChain messages to a list of dicts for Azure SDK
        azure_messages = [{"role": self._map_role(msg.type), "content": msg.content} for msg in messages]

        loop = asyncio.get_event_loop()
        
        func = functools.partial(
            self._client.complete, 
            messages=azure_messages, 
            model=self._model_name
        )
        
        response = await loop.run_in_executor(None, func)
        
        # Return a LangChain AIMessage
        return AIMessage(content=response.choices[0].message.content)


class LLMOrchestrator:
    """Orchestrates LLM agents for educational tasks."""
    
    def __init__(self):
        # Initialize LLM using the native Azure AI SDK
        sync_client = ChatCompletionsClient(
            endpoint=config.azure_ai_endpoint,
            credential=AzureKeyCredential(config.azure_ai_key),
        )
        self.llm = AsyncAzureLLM(sync_client, config.azure_ai_model)
        
        # Initialize Redis
        self.redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            decode_responses=True
        )
        
        # Initialize memory system
        self.memory = IntegratedMemorySystem(
            redis_client=self.redis_client,
            window_size=config.memory_window_size,
            ttl_hours=config.cache_ttl_hours
        )
        
        # Initialize agent
        self.agent = AtomiaAgent(
            llm=self.llm,
            memory_system=self.memory,
            config={
                "max_iterations": config.max_iterations,
                "enable_reflection": config.enable_reflection,
                "max_retries": config.max_retries
            }
        )
    
    async def process(
        self,
        task_type: TaskType,
        user_input: str,
        user_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a user request through the appropriate agent."""
        try:
            logging.info(f"Processing orchestrator request for user {user_id}")
            agent_input = {"messages": [HumanMessage(content=user_input)]}
            response = await self.agent.process(messages=agent_input["messages"])
            final_content = response['messages'][-1].content
            return {"success": True, "response": final_content, "task_type": task_type.value, "metadata": metadata or {}}
        except Exception as e:
            error_str = str(e)
            logging.error(f"Orchestrator error for user {user_id}: {error_str}")
            return {"success": False, "error": error_str, "response": "I encountered an error processing your request.", "task_type": task_type.value, "metadata": {}}
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get the current context for a user."""
        return self.memory.long_term.get_user_context(user_id) or {}
    
    async def update_user_context(self, user_id: str, context: Dict[str, Any]):
        """Update user context."""
        self.memory.long_term.store_user_context(user_id, context)
    
    def clear_session(self, session_id: str):
        """Clear a specific session's short-term memory."""
        self.memory.short_term.clear()
    
    async def search_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search semantic memories for a user."""
        return self.memory.semantic.search_memories(
            query=query,
            n_results=limit,
            filter_dict={"user_id": user_id}
        )


# Global orchestrator instance
orchestrator = LLMOrchestrator() 