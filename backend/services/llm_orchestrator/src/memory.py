"""Memory systems for the LLM agent."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import redis
import json
import chromadb
from chromadb.utils import embedding_functions


class ShortTermMemory:
    """In-memory conversation buffer for current session."""
    
    def __init__(self, window_size: int = 10):
        self.memory = ConversationBufferWindowMemory(
            k=window_size,
            return_messages=True,
            memory_key="chat_history"
        )
    
    def add_message(self, role: str, content: str):
        """Add a message to memory."""
        if role == "human":
            self.memory.chat_memory.add_user_message(content)
        else:
            self.memory.chat_memory.add_ai_message(content)
    
    def get_messages(self) -> List[BaseMessage]:
        """Get all messages in the buffer."""
        return self.memory.chat_memory.messages
    
    def clear(self):
        """Clear the memory buffer."""
        self.memory.clear()


class LongTermMemory:
    """Redis-based memory for cross-session persistence."""
    
    def __init__(self, redis_client: redis.Redis, ttl_hours: int = 24):
        self.redis_client = redis_client
        self.ttl_seconds = ttl_hours * 3600
    
    def store_interaction(self, user_id: str, session_id: str, interaction: Dict[str, Any]):
        """Store an interaction in long-term memory."""
        key = f"interaction:{user_id}:{session_id}:{datetime.utcnow().isoformat()}"
        self.redis_client.setex(
            key,
            self.ttl_seconds,
            json.dumps(interaction)
        )
    
    def get_recent_interactions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent interactions for a user."""
        pattern = f"interaction:{user_id}:*"
        keys = self.redis_client.keys(pattern)
        
        # Sort by timestamp (embedded in key)
        keys = sorted(keys, reverse=True)[:limit]
        
        interactions = []
        for key in keys:
            data = self.redis_client.get(key)
            if data:
                interactions.append(json.loads(data))
        
        return interactions
    
    def store_user_context(self, user_id: str, context: Dict[str, Any]):
        """Store user-specific context."""
        key = f"context:{user_id}"
        self.redis_client.set(key, json.dumps(context))
    
    def get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user context."""
        data = self.redis_client.get(f"context:{user_id}")
        return json.loads(data) if data else None


class SemanticMemory:
    """Vector database for semantic search over past interactions and knowledge."""
    
    def __init__(self, collection_name: str = "atomia_memory"):
        self.client = chromadb.Client()
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Create or get collection
        try:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
        except ValueError:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
    
    def add_memory(self, content: str, metadata: Dict[str, Any], memory_id: Optional[str] = None):
        """Add a memory to the semantic store."""
        if not memory_id:
            memory_id = f"mem_{datetime.utcnow().timestamp()}"
        
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[memory_id]
        )
    
    def search_memories(self, query: str, n_results: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for relevant memories."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_dict
        )
        
        memories = []
        for i in range(len(results['ids'][0])):
            memories.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return memories
    
    def delete_memory(self, memory_id: str):
        """Delete a specific memory."""
        self.collection.delete(ids=[memory_id])


class IntegratedMemorySystem:
    """Combines all memory systems for the agent."""
    
    def __init__(self, redis_client: redis.Redis, window_size: int = 10, ttl_hours: int = 24):
        self.short_term = ShortTermMemory(window_size)
        self.long_term = LongTermMemory(redis_client, ttl_hours)
        self.semantic = SemanticMemory()
    
    def remember_interaction(self, user_id: str, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Store interaction across all memory systems."""
        # Add to short-term
        self.short_term.add_message(role, content)
        
        # Prepare interaction data
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        
        # Store in long-term
        self.long_term.store_interaction(user_id, session_id, interaction)
        
        # Add to semantic memory with user context
        semantic_metadata = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": interaction["timestamp"],
            "role": role,
            **(metadata or {})
        }
        self.semantic.add_memory(content, semantic_metadata)
    
    def get_relevant_context(self, user_id: str, query: str, include_recent: bool = True) -> Dict[str, Any]:
        """Get all relevant context for the current query."""
        context = {
            "current_conversation": [msg.content for msg in self.short_term.get_messages()],
            "user_profile": self.long_term.get_user_context(user_id),
            "relevant_memories": [],
            "recent_interactions": []
        }
        
        # Search semantic memories
        semantic_results = self.semantic.search_memories(
            query,
            filter_dict={"user_id": user_id}
        )
        context["relevant_memories"] = semantic_results
        
        # Get recent interactions if requested
        if include_recent:
            context["recent_interactions"] = self.long_term.get_recent_interactions(user_id, limit=5)
        
        return context 