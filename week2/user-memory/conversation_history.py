"""
Conversation History Management with optional Dify integration for vector search
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
from config import Config

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single conversation turn"""
    session_id: str
    user_message: str
    assistant_message: str
    timestamp: str
    turn_number: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationTurn':
        """Create from dictionary"""
        return cls(**data)


class ConversationHistory:
    """Manages conversation history with optional vector search"""
    
    def __init__(self, user_id: str):
        """
        Initialize conversation history manager
        
        Args:
            user_id: User identifier
        """
        self.user_id = user_id
        self.history_file = os.path.join(
            Config.CONVERSATION_HISTORY_DIR,
            f"{user_id}_history.json"
        )
        self.conversations: List[ConversationTurn] = []
        self.load_history()
        
        # Initialize Dify client if configured
        self.dify_client = None
        if Config.ENABLE_HISTORY_SEARCH and Config.DIFY_API_KEY:
            self.dify_client = DifySearchClient()
    
    def load_history(self):
        """Load conversation history from storage"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conversations = [
                        ConversationTurn.from_dict(turn) 
                        for turn in data.get('conversations', [])
                    ]
                logger.info(f"Loaded {len(self.conversations)} conversation turns for user {self.user_id}")
            except Exception as e:
                logger.error(f"Error loading conversation history: {e}")
                self.conversations = []
        else:
            self.conversations = []
    
    def save_history(self):
        """Save conversation history to storage"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                data = {
                    'user_id': self.user_id,
                    'updated_at': datetime.now().isoformat(),
                    'conversations': [turn.to_dict() for turn in self.conversations]
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.conversations)} conversation turns")
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
    
    def add_turn(self, session_id: str, user_message: str, assistant_message: str):
        """
        Add a conversation turn
        
        Args:
            session_id: Session identifier
            user_message: User's message
            assistant_message: Assistant's response
        """
        turn = ConversationTurn(
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            timestamp=datetime.now().isoformat(),
            turn_number=len(self.conversations) + 1
        )
        self.conversations.append(turn)
        self.save_history()
        
        # Index in Dify if available
        if self.dify_client:
            self.dify_client.index_conversation(turn)
    
    def get_recent_turns(self, limit: int = 10) -> List[ConversationTurn]:
        """
        Get recent conversation turns
        
        Args:
            limit: Maximum number of turns to return
            
        Returns:
            List of recent conversation turns
        """
        return self.conversations[-limit:] if self.conversations else []
    
    def get_session_turns(self, session_id: str) -> List[ConversationTurn]:
        """
        Get all turns from a specific session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation turns from the session
        """
        return [turn for turn in self.conversations if turn.session_id == session_id]
    
    def search_history(self, query: str, limit: int = 5) -> List[ConversationTurn]:
        """
        Search conversation history
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching conversation turns
        """
        # Try vector search with Dify if available
        if self.dify_client:
            return self.dify_client.search_conversations(query, self.user_id, limit)
        
        # Fallback to simple text search
        query_lower = query.lower()
        results = []
        
        for turn in self.conversations:
            if (query_lower in turn.user_message.lower() or 
                query_lower in turn.assistant_message.lower()):
                results.append(turn)
                if len(results) >= limit:
                    break
        
        return results


class DifySearchClient:
    """Client for Dify vector search integration"""
    
    def __init__(self):
        """Initialize Dify client"""
        self.api_key = Config.DIFY_API_KEY
        self.base_url = Config.DIFY_BASE_URL
        self.dataset_id = Config.DIFY_DATASET_ID
        
        if not self.api_key or not self.dataset_id:
            logger.warning("Dify API key or dataset ID not configured")
            self.enabled = False
        else:
            self.enabled = True
            self.headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
    
    def index_conversation(self, turn: ConversationTurn):
        """
        Index a conversation turn in Dify
        
        Args:
            turn: Conversation turn to index
        """
        if not self.enabled:
            return
        
        try:
            # Prepare document for indexing
            document = {
                'name': f"{turn.session_id}_{turn.turn_number}",
                'text': f"User: {turn.user_message}\n\nAssistant: {turn.assistant_message}",
                'metadata': {
                    'session_id': turn.session_id,
                    'timestamp': turn.timestamp,
                    'turn_number': str(turn.turn_number)
                }
            }
            
            # Index document in Dify
            url = f"{self.base_url}/datasets/{self.dataset_id}/documents"
            response = requests.post(
                url,
                headers=self.headers,
                json={'documents': [document]}
            )
            
            if response.status_code == 200:
                logger.debug(f"Indexed conversation turn {turn.session_id}_{turn.turn_number}")
            else:
                logger.error(f"Failed to index conversation: {response.text}")
                
        except Exception as e:
            logger.error(f"Error indexing conversation in Dify: {e}")
    
    def search_conversations(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[ConversationTurn]:
        """
        Search conversations using Dify vector search
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of matching conversation turns
        """
        if not self.enabled:
            return []
        
        try:
            # Perform vector search
            url = f"{self.base_url}/datasets/{self.dataset_id}/search"
            payload = {
                'query': query,
                'limit': limit,
                'retrieval_model': {
                    'search_method': 'semantic_search',
                    'reranking_enable': True,
                    'reranking_model': {
                        'reranking_provider_name': 'cohere',
                        'reranking_model_name': 'rerank-multilingual-v2.0'
                    },
                    'top_k': limit * 2,
                    'score_threshold_enabled': True,
                    'score_threshold': 0.5
                }
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                results = response.json()
                turns = []
                
                for record in results.get('records', []):
                    metadata = record.get('metadata', {})
                    # Parse the text back into user and assistant messages
                    text = record.get('segment', {}).get('content', '')
                    parts = text.split('\n\nAssistant: ')
                    
                    if len(parts) == 2:
                        user_msg = parts[0].replace('User: ', '')
                        assistant_msg = parts[1]
                        
                        turn = ConversationTurn(
                            session_id=metadata.get('session_id', ''),
                            user_message=user_msg,
                            assistant_message=assistant_msg,
                            timestamp=metadata.get('timestamp', ''),
                            turn_number=int(metadata.get('turn_number', 0))
                        )
                        turns.append(turn)
                
                return turns
            else:
                logger.error(f"Failed to search conversations: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching conversations in Dify: {e}")
            return []


class SimpleEmbeddingSearch:
    """Simple embedding-based search without external dependencies"""
    
    def __init__(self):
        """Initialize simple embedding search"""
        # This is a placeholder for a simple embedding search
        # In production, you might use sentence-transformers or similar
        pass
    
    def search(
        self,
        query: str,
        documents: List[str],
        limit: int = 5
    ) -> List[int]:
        """
        Simple text similarity search
        
        Args:
            query: Search query
            documents: List of documents to search
            limit: Maximum number of results
            
        Returns:
            Indices of top matching documents
        """
        # Simple keyword-based scoring
        query_words = set(query.lower().split())
        scores = []
        
        for i, doc in enumerate(documents):
            doc_words = set(doc.lower().split())
            # Calculate Jaccard similarity
            intersection = query_words & doc_words
            union = query_words | doc_words
            score = len(intersection) / len(union) if union else 0
            scores.append((i, score))
        
        # Sort by score and return top indices
        scores.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, _ in scores[:limit]]
