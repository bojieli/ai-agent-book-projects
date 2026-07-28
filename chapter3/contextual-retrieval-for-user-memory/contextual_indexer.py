"""Contextual RAG Indexer with Advanced Memory Cards

This module combines contextual chunking for conversation histories with
advanced JSON cards for structured user memory.
"""

import os
import json
import logging
import requests
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from config import IndexConfig, IndexMode, ChunkingConfig
from chunker import ConversationChunk
from contextual_chunking import ContextualConversationChunk, ContextualConversationChunker
from advanced_memory_manager import AdvancedMemoryManager, AdvancedMemoryCard
from indexer import SearchResult


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass 
class ContextualSearchResult(SearchResult):
    """Enhanced search result with contextual information"""
    context: str = ""
    contextual_chunk: Optional[ContextualConversationChunk] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["context"] = self.context
        if self.contextual_chunk:
            result["contextual_info"] = {
                "context": self.contextual_chunk.context,
                "context_tokens": self.contextual_chunk.context_tokens,
                "generation_time": self.contextual_chunk.generation_time
            }
        return result


class ContextualMemoryIndexer:
    """
    Dual-layer memory indexer combining:
    1. Contextual RAG for conversation chunks
    2. Advanced JSON cards for structured facts
    """
    
    def __init__(self,
                 user_id: str,
                 index_config: Optional[IndexConfig] = None,
                 chunking_config: Optional[ChunkingConfig] = None,
                 use_contextual: bool = True):
        """
        Initialize the contextual memory indexer.
        
        Args:
            user_id: User identifier
            index_config: Index configuration
            chunking_config: Chunking configuration
            use_contextual: Whether to use contextual chunking
        """
        self.user_id = user_id
        self.index_config = index_config or IndexConfig()
        self.chunking_config = chunking_config or ChunkingConfig()
        self.use_contextual = use_contextual
        
        # Initialize contextual chunker
        self.contextual_chunker = ContextualConversationChunker(
            chunking_config=self.chunking_config,
            use_contextual=use_contextual
        )
        
        # Initialize advanced memory manager
        self.memory_manager = AdvancedMemoryManager(
            user_id=user_id,
            storage_dir=self.index_config.chunk_store_path
        )
        
        # Storage for chunks
        self.contextual_chunks: Dict[str, ContextualConversationChunk] = {}
        self.doc_id_mapping: Dict[str, str] = {}
        
        # Retrieval pipeline URL
        self.retrieval_url = "http://localhost:4242"
        
        # Create directories
        Path(self.index_config.index_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.index_config.chunk_store_path).mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            "chunks_indexed": 0,
            "memory_cards": 0,
            "context_generation_time": 0.0,
            "indexing_time": 0.0
        }
        
        self._check_retrieval_pipeline()
        logger.info(f"Initialized ContextualMemoryIndexer for user {user_id}")
    
    def _check_retrieval_pipeline(self):
        """Check if the retrieval pipeline service is available"""
        try:
            response = requests.get(f"{self.retrieval_url}/health", timeout=2)
            if response.status_code == 200:
                logger.info("✓ Retrieval pipeline service is available")
            else:
                logger.warning(f"Retrieval pipeline returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Retrieval pipeline service not available at {self.retrieval_url}: {e}")
            logger.info("Note: The retrieval pipeline needs to be running. Start it with:")
            logger.info("  cd projects/week3/retrieval-pipeline && python api_server.py")
    
    def process_conversation_history(self,
                                    chunks: List[ConversationChunk],
                                    conversation_id: str,
                                    generate_summary_cards: bool = True) -> Dict[str, Any]:
        """
        Process conversation history with both contextual chunking and memory cards.
        
        Args:
            chunks: Basic conversation chunks
            conversation_id: Conversation identifier
            generate_summary_cards: Whether to generate summary cards
            
        Returns:
            Processing results
        """
        start_time = time.time()
        results = {
            "conversation_id": conversation_id,
            "contextual_chunks": 0,
            "memory_cards_before": len(self.memory_manager.categories),
            "memory_cards_after": 0,
            "processing_time": 0
        }
        
        # Step 1: Generate contextual chunks
        logger.info(f"Processing {len(chunks)} chunks for conversation {conversation_id}")
        
        if self.use_contextual:
            contextual_chunks = self.contextual_chunker.contextualize_chunks(chunks)
            logger.info(f"Generated {len(contextual_chunks)} contextual chunks")
        else:
            # Convert to contextual chunks without context
            contextual_chunks = [
                ContextualConversationChunk.from_basic_chunk(chunk)
                for chunk in chunks
            ]
        
        # Store contextual chunks
        for chunk in contextual_chunks:
            self.contextual_chunks[chunk.chunk_id] = chunk
        
        results["contextual_chunks"] = len(contextual_chunks)
        
        # Step 2: Index contextual chunks
        self._index_contextual_chunks(contextual_chunks)
        
        # Step 3: Generate summary cards if requested
        if generate_summary_cards:
            summary_cards = self._generate_summary_cards(chunks, conversation_id)
            for card in summary_cards:
                self.memory_manager.add_card(card)
            
            logger.info(f"Generated {len(summary_cards)} summary cards")
            results["new_summary_cards"] = len(summary_cards)
        
        # Step 4: Create conversation summary linking to memory cards
        conversation_summary = self.memory_manager.summarize_for_conversation(conversation_id)
        results["memory_cards_after"] = sum(len(cards) for cards in self.memory_manager.categories.values())
        results["conversation_summary"] = conversation_summary
        
        # Update statistics
        results["processing_time"] = time.time() - start_time
        self.stats["chunks_indexed"] += len(contextual_chunks)
        self.stats["memory_cards"] = results["memory_cards_after"]
        self.stats["indexing_time"] += results["processing_time"]
        
        logger.info(f"Processing complete for conversation {conversation_id} in {results['processing_time']:.2f}s")
        
        return results
    
    def _index_contextual_chunks(self, chunks: List[ContextualConversationChunk]):
        """Index contextual chunks in the retrieval pipeline"""
        documents = []
        
        for chunk in chunks:
            # Use contextualized text for indexing
            doc = {
                "text": chunk.contextualized_text,
                "metadata": {
                    "doc_id": chunk.chunk_id,
                    "test_id": chunk.test_id,
                    "conversation_id": chunk.conversation_id,
                    "chunk_index": chunk.chunk_index,
                    "start_round": chunk.start_round,
                    "end_round": chunk.end_round,
                    "has_context": bool(chunk.context),
                    "context_preview": chunk.context[:100] if chunk.context else "",
                    **chunk.metadata
                }
            }
            documents.append(doc)
        
        # Send to retrieval pipeline
        try:
            indexed_count = 0
            for doc in documents:
                try:
                    response = requests.post(
                        f"{self.retrieval_url}/index",
                        json=doc, timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        generated_doc_id = result.get("doc_id")
                        our_chunk_id = doc.get("metadata", {}).get("doc_id")
                        
                        if generated_doc_id and our_chunk_id:
                            self.doc_id_mapping[generated_doc_id] = our_chunk_id
                        
                        indexed_count += 1
                except Exception as e:
                    logger.warning(f"Error indexing document: {e}")
            
            logger.info(f"Indexed {indexed_count}/{len(documents)} contextual chunks")
            
        except Exception as e:
            logger.error(f"Error connecting to retrieval pipeline: {e}")
    
    def _generate_summary_cards(self, 
                               chunks: List[ConversationChunk],
                               conversation_id: str) -> List[AdvancedMemoryCard]:
        """
        Generate summary cards from conversation chunks using LLM extraction.
        
        Uses an LLM to analyze conversation chunks and extract structured memory cards
        following the Advanced JSON Cards format from week2/user-memory.
        """
        cards = []
        
        if not chunks:
            return cards
        
        # Combine all conversation text
        full_text = "\n".join([chunk.to_text() for chunk in chunks])
        
        # Use LLM to extract structured memory cards
        try:
            # Initialize LLM client if needed
            if not hasattr(self, '_llm_client'):
                from openai import OpenAI
                from config import Config
                config = Config.from_env()
                client_config, model = config.llm.get_client_config()
                base_url = client_config.pop("base_url", None)
                
                if base_url:
                    self._llm_client = OpenAI(base_url=base_url, **client_config)
                else:
                    self._llm_client = OpenAI(**client_config)
                self._llm_model = model
            
            # Create extraction prompt
            extraction_prompt = f"""Analyze this conversation and extract structured memory cards.

Conversation:
{full_text}

Extract any important information into memory cards. Each card MUST include:
- category: The type of information (e.g., 'personal', 'financial', 'medical', 'travel', 'family', 'work')
- card_key: A unique identifier for this card
- backstory: Context about when/why this information was learned (1-2 sentences)
- date_created: Current timestamp (YYYY-MM-DD HH:MM:SS)
- person: Who this relates to (e.g., "John Smith (primary)", "Sarah Smith (daughter)")
- relationship: Role/relationship (e.g., "primary account holder", "family member")
- Additional relevant fields based on the information type

Respond with a JSON array of memory cards. If no significant information found, return empty array [].

Example format:
[{{
    "category": "financial",
    "card_key": "bank_account_primary",
    "backstory": "User shared their banking details while setting up automatic bill payments",
    "date_created": "2024-01-15 10:30:00",
    "person": "John Smith (primary)",
    "relationship": "primary account holder",
    "bank_name": "Chase Bank",
    "account_type": "checking",
    "account_ending": "4567"
}}]

Extract memory cards:"""
            
            # Call LLM for extraction
            response = self._llm_client.chat.completions.create(
                model=self._llm_model,
                messages=[
                    {"role": "system", "content": "You are a memory extraction assistant. Extract structured information from conversations into memory cards."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=_reasoning_safe_temperature(self._llm_model, 0.3),
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            extracted_data = json.loads(content) if content else {}
            
            # Handle both single card and array of cards
            if isinstance(extracted_data, dict):
                # Check if it's a wrapper with 'cards' key
                if 'cards' in extracted_data:
                    extracted_cards = extracted_data['cards']
                elif 'memory_cards' in extracted_data:
                    extracted_cards = extracted_data['memory_cards']
                else:
                    # Single card
                    extracted_cards = [extracted_data] if extracted_data else []
            elif isinstance(extracted_data, list):
                extracted_cards = extracted_data
            else:
                extracted_cards = []
            
            # Convert extracted data to AdvancedMemoryCard objects
            for card_data in extracted_cards:
                try:
                    # Ensure required fields
                    if 'backstory' not in card_data:
                        card_data['backstory'] = f"Information extracted from conversation {conversation_id}"
                    if 'date_created' not in card_data:
                        card_data['date_created'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if 'person' not in card_data:
                        card_data['person'] = 'User (primary)'
                    if 'relationship' not in card_data:
                        card_data['relationship'] = 'primary account holder'
                    
                    # Extract main fields
                    category = card_data.pop('category', 'general')
                    card_key = card_data.pop('card_key', f"{category}_{conversation_id[:8]}")
                    backstory = card_data.pop('backstory')
                    date_created = card_data.pop('date_created')
                    person = card_data.pop('person')
                    relationship = card_data.pop('relationship')
                    
                    # Create card with remaining fields as data
                    card = AdvancedMemoryCard(
                        category=category,
                        card_key=card_key,
                        backstory=backstory,
                        date_created=date_created,
                        person=person,
                        relationship=relationship,
                        data=card_data  # All remaining fields
                    )
                    cards.append(card)
                    
                except Exception as e:
                    logger.warning(f"Error creating memory card: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error generating memory cards with LLM: {e}")
            # Fallback to basic extraction if LLM fails
            cards = self._fallback_extraction(chunks, conversation_id, full_text)
        
        return cards
    
    def _fallback_extraction(self, chunks: List[ConversationChunk], 
                             conversation_id: str, full_text: str) -> List[AdvancedMemoryCard]:
        """Fallback extraction method if LLM is unavailable"""
        cards = []
        
        # Extract basic information based on keywords
        categories_keywords = {
            'financial': ['bank', 'account', 'money', 'payment', 'credit', 'loan', 'savings', 'checking'],
            'medical': ['doctor', 'medical', 'health', 'appointment', 'prescription', 'hospital', 'clinic'],
            'travel': ['flight', 'travel', 'trip', 'vacation', 'hotel', 'booking', 'destination'],
            'family': ['family', 'child', 'parent', 'spouse', 'daughter', 'son', 'wife', 'husband'],
            'work': ['job', 'work', 'employer', 'salary', 'office', 'meeting', 'project', 'colleague']
        }
        
        text_lower = full_text.lower()
        
        for category, keywords in categories_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                card = AdvancedMemoryCard(
                    category=category,
                    card_key=f"{category}_{conversation_id[:8]}",
                    backstory=f"Information about {category} topics discussed in conversation",
                    date_created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    person="User (primary)",
                    relationship="primary account holder",
                    data={
                        "conversation_id": conversation_id,
                        "topics": [kw for kw in keywords if kw in text_lower][:3],
                        "extracted_from": f"{len(chunks)} conversation chunks",
                        "extraction_method": "fallback_keywords"
                    }
                )
                cards.append(card)
                break  # Only add one card per conversation in fallback mode
        
        return cards
    
    def search_with_context(self,
                           query: str,
                           top_k: int = 3,
                           include_memory_cards: bool = True) -> Dict[str, Any]:
        """
        Search both contextual chunks and memory cards.
        
        Args:
            query: Search query
            top_k: Number of results
            include_memory_cards: Whether to search memory cards too
            
        Returns:
            Combined search results
        """
        results = {
            "query": query,
            "chunk_results": [],
            "memory_card_results": [],
            "combined_context": ""
        }
        
        # Search contextual chunks via retrieval pipeline or fallback to local search
        try:
            response = requests.post(
                f"{self.retrieval_url}/search",
                json={
                    "query": query,
                    "mode": "hybrid",
                    "top_k": max(20, top_k),
                    "rerank_top_k": top_k,
                    "skip_reranking": False
                },
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get("reranked_results", [])
            
            for item in search_results:
                metadata = item.get("metadata", {})
                chunk_id = metadata.get("doc_id")
                
                if chunk_id and chunk_id in self.contextual_chunks:
                    contextual_chunk = self.contextual_chunks[chunk_id]
                    
                    # Create a basic ConversationChunk for compatibility
                    from chunker import ConversationChunk
                    basic_chunk = ConversationChunk(
                        chunk_id=contextual_chunk.chunk_id,
                        conversation_id=contextual_chunk.conversation_id,
                        test_id=contextual_chunk.test_id,
                        chunk_index=contextual_chunk.chunk_index,
                        start_round=contextual_chunk.start_round,
                        end_round=contextual_chunk.end_round,
                        messages=contextual_chunk.messages,
                        metadata=contextual_chunk.metadata,
                        context_before=contextual_chunk.context_before,
                        context_after=contextual_chunk.context_after,
                        created_at=contextual_chunk.created_at
                    )
                    
                    result = ContextualSearchResult(
                        chunk_id=chunk_id,
                        score=float(item.get("rerank_score", 0)),
                        chunk=basic_chunk,
                        match_type="hybrid",
                        context=contextual_chunk.context,
                        contextual_chunk=contextual_chunk
                    )
                    results["chunk_results"].append(result.to_dict())
            
        except Exception as e:
            logger.error(f"Error searching via retrieval pipeline: {e}")
            logger.info("Falling back to local search...")
            
            # Fallback: Local search through contextual chunks
            query_lower = query.lower()
            local_results = []
            
            for chunk_id, chunk in self.contextual_chunks.items():
                # Search in contextualized text (skip chunks with empty text)
                if query_lower and chunk.contextualized_text and query_lower in chunk.contextualized_text.lower():
                    # Calculate a simple relevance score based on frequency
                    score = chunk.contextualized_text.lower().count(query_lower) / len(chunk.contextualized_text)
                    local_results.append((score, chunk_id, chunk))
            
            # Sort by score and take top_k
            local_results.sort(key=lambda x: x[0], reverse=True)
            
            for score, chunk_id, contextual_chunk in local_results[:top_k]:
                # Create a basic ConversationChunk for compatibility
                from chunker import ConversationChunk
                basic_chunk = ConversationChunk(
                    chunk_id=contextual_chunk.chunk_id,
                    conversation_id=contextual_chunk.conversation_id,
                    test_id=contextual_chunk.test_id,
                    chunk_index=contextual_chunk.chunk_index,
                    start_round=contextual_chunk.start_round,
                    end_round=contextual_chunk.end_round,
                    messages=contextual_chunk.messages,
                    metadata=contextual_chunk.metadata,
                    context_before=contextual_chunk.context_before,
                    context_after=contextual_chunk.context_after,
                    created_at=contextual_chunk.created_at
                )
                
                results["chunk_results"].append({
                    "chunk_id": chunk_id,
                    "score": score,
                    "context": contextual_chunk.context,
                    "conversation_id": contextual_chunk.conversation_id,
                    "rounds": f"{contextual_chunk.start_round}-{contextual_chunk.end_round}",
                    "text": contextual_chunk.original_text
                })
            
            logger.info(f"Local search returned {len(results['chunk_results'])} results")
        
        # Search memory cards
        if include_memory_cards:
            card_results = self.memory_manager.search_cards(query)
            for memory_id, card in card_results[:top_k]:
                results["memory_card_results"].append({
                    "memory_id": memory_id,
                    "category": card.category,
                    "backstory": card.backstory,
                    "person": card.person,
                    "data": card.data
                })
        
        # Build combined context
        context_parts = []
        
        if results["memory_card_results"]:
            context_parts.append("=== RELEVANT MEMORY CARDS ===")
            for card_result in results["memory_card_results"]:
                context_parts.append(f"- {card_result['category']}: {card_result['backstory']}")
        
        if results["chunk_results"]:
            context_parts.append("\n=== RELEVANT CONVERSATION CHUNKS ===")
            for chunk_result in results["chunk_results"]:
                context_parts.append(f"- {chunk_result.get('context', 'No context')}")
        
        results["combined_context"] = "\n".join(context_parts)
        
        return results
    
    def get_agent_context(self, max_memory_cards: int = 10) -> str:
        """
        Get the complete context for the agent including memory cards.
        
        Args:
            max_memory_cards: Maximum number of memory cards to include
            
        Returns:
            Formatted context string
        """
        return self.memory_manager.get_context_string(max_cards=max_memory_cards)
    
    def save_index(self, path: Optional[str] = None):
        """Save the index and memory to disk"""
        path = path or self.index_config.index_path
        
        # Save contextual chunks
        chunks_data = {
            chunk_id: chunk.to_dict()
            for chunk_id, chunk in self.contextual_chunks.items()
        }
        
        with open(f"{path}_contextual_chunks.json", 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        
        # Memory cards are automatically saved by the memory manager
        
        # Save statistics
        with open(f"{path}_stats.json", 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
        
        logger.info(f"Saved index to {path}")
    
    def load_index(self, path: Optional[str] = None):
        """Load the index from disk"""
        path = path or self.index_config.index_path
        
        try:
            # Load contextual chunks
            with open(f"{path}_contextual_chunks.json", 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            self.contextual_chunks = {}
            for chunk_id, chunk_dict in chunks_data.items():
                # Convert messages
                from chunker import ConversationMessage
                messages = []
                for msg_data in chunk_dict.get('messages', []):
                    messages.append(ConversationMessage(**msg_data))
                
                # Create contextual chunk
                chunk = ContextualConversationChunk(
                    chunk_id=chunk_dict['chunk_id'],
                    conversation_id=chunk_dict['conversation_id'],
                    test_id=chunk_dict['test_id'],
                    chunk_index=chunk_dict['chunk_index'],
                    start_round=chunk_dict['start_round'],
                    end_round=chunk_dict['end_round'],
                    messages=messages,
                    original_text=chunk_dict.get('original_text', ''),
                    context=chunk_dict.get('context', ''),
                    contextualized_text=chunk_dict.get('contextualized_text', ''),
                    context_tokens=chunk_dict.get('context_tokens', 0),
                    generation_time=chunk_dict.get('generation_time', 0),
                    metadata=chunk_dict.get('metadata', {}),
                    context_before=chunk_dict.get('context_before'),
                    context_after=chunk_dict.get('context_after'),
                    created_at=chunk_dict.get('created_at', '')
                )
                self.contextual_chunks[chunk_id] = chunk
            
            # Memory cards are automatically loaded by the memory manager
            
            # Load statistics
            stats_path = f"{path}_stats.json"
            if Path(stats_path).exists():
                with open(stats_path, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            
            logger.info(f"Loaded {len(self.contextual_chunks)} contextual chunks from {path}")
            
            # Re-index in retrieval pipeline
            self._index_contextual_chunks(list(self.contextual_chunks.values()))
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        stats = self.stats.copy()
        
        # Add chunker statistics
        stats["chunker_stats"] = self.contextual_chunker.get_statistics()
        
        # Add memory manager statistics
        stats["memory_stats"] = self.memory_manager.get_statistics()
        
        # Calculate averages
        if stats["chunks_indexed"] > 0:
            stats["avg_indexing_time"] = stats["indexing_time"] / stats["chunks_indexed"]
        
        return stats
