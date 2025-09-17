"""
Context Compression Strategies for the experiment
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from openai import OpenAI
import tiktoken
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format=Config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class CompressionStrategy(Enum):
    """Different context compression strategies"""
    NO_COMPRESSION = "no_compression"
    NON_CONTEXT_AWARE_INDIVIDUAL = "non_context_aware_individual_summary"  # Summarize each page individually then concat
    NON_CONTEXT_AWARE_COMBINED = "non_context_aware_combined_summary"     # Concat all pages then summarize once
    CONTEXT_AWARE = "context_aware_summary"
    CONTEXT_AWARE_CITATIONS = "context_aware_with_citations"
    WINDOWED_CONTEXT = "windowed_context"


@dataclass
class CompressedContent:
    """Represents compressed content"""
    original_length: int
    compressed_length: int
    content: str
    citations: List[Dict[str, str]] = field(default_factory=list)
    strategy: CompressionStrategy = CompressionStrategy.NO_COMPRESSION
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ContextCompressor:
    """Handles different context compression strategies"""
    
    def __init__(self, strategy: CompressionStrategy, api_key: str, enable_streaming: bool = True):
        """
        Initialize the context compressor
        
        Args:
            strategy: Compression strategy to use
            api_key: API key for LLM
            enable_streaming: Whether to enable streaming for summarization
        """
        self.strategy = strategy
        self.enable_streaming = enable_streaming
        self.client = OpenAI(
            api_key=api_key,
            base_url=Config.MOONSHOT_BASE_URL
        )
        self.model = Config.MODEL_NAME
        
        # Initialize tokenizer for token counting
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info(f"Context compressor initialized with strategy: {strategy.value}, streaming: {enable_streaming}")
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        try:
            return len(self.encoding.encode(text))
        except:
            # Fallback to character-based estimation (1 token ≈ 4 chars)
            return len(text) // 4
    
    def compress_search_results(
        self, 
        search_results: Dict[str, Any],
        query: str,
        current_context: Optional[str] = None
    ) -> CompressedContent:
        """
        Compress search results based on the selected strategy
        
        Args:
            search_results: Raw search results from web tool
            query: The original search query
            current_context: Current conversation context (for context-aware strategies)
            
        Returns:
            Compressed content
        """
        if self.strategy == CompressionStrategy.NO_COMPRESSION:
            return self._no_compression(search_results)
        elif self.strategy == CompressionStrategy.NON_CONTEXT_AWARE_INDIVIDUAL:
            return self._non_context_aware_individual_summary(search_results)
        elif self.strategy == CompressionStrategy.NON_CONTEXT_AWARE_COMBINED:
            return self._non_context_aware_combined_summary(search_results)
        elif self.strategy == CompressionStrategy.CONTEXT_AWARE:
            return self._context_aware_summary(search_results, query, current_context)
        elif self.strategy == CompressionStrategy.CONTEXT_AWARE_CITATIONS:
            return self._context_aware_with_citations(search_results, query, current_context)
        elif self.strategy == CompressionStrategy.WINDOWED_CONTEXT:
            # For windowed context, return full content (compression happens later)
            return self._no_compression(search_results)
        else:
            raise ValueError(f"Unknown compression strategy: {self.strategy}")
    
    def compress_for_history(
        self,
        content: str,
        tool_name: str,
        query: str,
        preserve_citations: bool = True
    ) -> CompressedContent:
        """
        Compress content for message history (used in windowed context strategy)
        
        Args:
            content: Content to compress
            tool_name: Name of the tool that generated the content
            query: The query that triggered the tool call
            preserve_citations: Whether to preserve citations
            
        Returns:
            Compressed content for history
        """
        original_length = len(content)
        
        try:
            prompt = f"""Compress the following {tool_name} results into a concise summary that preserves key information.
Focus on information relevant to: {query}

Original content:
{content[:10000]}  # Limit for history compression

Requirements:
1. Keep all important facts, names, dates, and affiliations
2. Remove redundant information
3. Maintain clarity and coherence
{"4. Include [Source: URL] citations for important facts" if preserve_citations else ""}
5. Maximum length: {Config.SUMMARY_MAX_TOKENS} tokens

Provide a focused summary:"""

            # Log prompt length
            prompt_tokens = self.count_tokens(prompt)
            logger.info(f"Simple summary request - Prompt tokens: {prompt_tokens}, Prompt length: {len(prompt)} chars")

            if self.enable_streaming:
                # Stream the summary to console
                print(f"\n📝 Creating simple summary...\n", flush=True)
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=Config.SUMMARY_MAX_TOKENS,
                    stream=True
                )
                
                summary_parts = []
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        summary_parts.append(content)
                print("\n")  # New lines after streaming
                compressed = "".join(summary_parts)
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=Config.SUMMARY_MAX_TOKENS
                )
                compressed = response.choices[0].message.content
            
            return CompressedContent(
                original_length=original_length,
                compressed_length=len(compressed),
                content=compressed,
                strategy=CompressionStrategy.WINDOWED_CONTEXT
            )
            
        except Exception as e:
            logger.error(f"Error compressing for history: {str(e)}")
            # Fallback to truncation
            truncated = content[:2000] + "\n\n[Content truncated for history...]"
            return CompressedContent(
                original_length=original_length,
                compressed_length=len(truncated),
                content=truncated,
                strategy=CompressionStrategy.WINDOWED_CONTEXT
            )
    
    def _no_compression(self, search_results: Dict[str, Any]) -> CompressedContent:
        """
        Strategy 1: No compression - return all original content
        """
        all_content = []
        total_length = 0
        
        for result in search_results.get('results', []):
            content = f"""
===== Search Result =====
Title: {result.get('title', 'N/A')}
URL: {result.get('url', 'N/A')}
Snippet: {result.get('snippet', 'N/A')}

Full Content:
{result.get('content', 'No content available')}
========================
"""
            all_content.append(content)
            total_length += len(result.get('content', ''))
        
        full_content = "\n\n".join(all_content)
        
        return CompressedContent(
            original_length=total_length,
            compressed_length=len(full_content),
            content=full_content,
            strategy=CompressionStrategy.NO_COMPRESSION
        )
    
    def _non_context_aware_individual_summary(self, search_results: Dict[str, Any]) -> CompressedContent:
        """
        Strategy 2A: Non-context-aware summarization - Summarize each page individually then concatenate
        """
        summaries = []
        total_original = 0
        
        for result in search_results.get('results', []):
            if not result.get('content'):
                continue
                
            original_content = result.get('content', '')
            total_original += len(original_content)
            
            try:
                # Summarize each page independently
                prompt = f"""Summarize the following webpage content in 2-3 paragraphs:

Title: {result.get('title', 'N/A')}
URL: {result.get('url', 'N/A')}

Content:
{original_content[:5000]}  # Limit to prevent token overflow

Provide a concise summary:"""

                # Log prompt length
                prompt_tokens = self.count_tokens(prompt)
                logger.info(f"Non-context-aware summary - Prompt tokens: {prompt_tokens}, Prompt length: {len(prompt)} chars")

                if self.enable_streaming:
                    # Stream the summary to console
                    print(f"\n📝 Summarizing: {result.get('title', 'N/A')[:50]}...", end=" ", flush=True)
                    stream = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=300,
                        stream=True
                    )
                    
                    summary_parts = []
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            print(content, end="", flush=True)
                            summary_parts.append(content)
                    print()  # New line after streaming
                    summary = "".join(summary_parts)
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=300
                    )
                    summary = response.choices[0].message.content
                
                summaries.append(f"""
Source: {result.get('title', 'N/A')}
URL: {result.get('url', 'N/A')}
Summary: {summary}
""")
                
            except Exception as e:
                logger.error(f"Error summarizing page: {str(e)}")
                # Fallback to snippet
                summaries.append(f"""
Source: {result.get('title', 'N/A')}
URL: {result.get('url', 'N/A')}
Summary: {result.get('snippet', 'No summary available')}
""")
        
        compressed_content = "\n".join(summaries)
        
        return CompressedContent(
            original_length=total_original,
            compressed_length=len(compressed_content),
            content=compressed_content,
            strategy=CompressionStrategy.NON_CONTEXT_AWARE_INDIVIDUAL
        )
    
    def _non_context_aware_combined_summary(self, search_results: Dict[str, Any]) -> CompressedContent:
        """
        Strategy 2B: Non-context-aware summarization - Concatenate all pages then summarize once
        """
        # Combine all content first
        all_content = []
        total_original = 0
        max_chars_per_page = 5000  # Limit each page to prevent token overflow
        
        for result in search_results.get('results', []):
            if result.get('content'):
                original_content = result.get('content', '')
                total_original += len(original_content)
                
                # Limit each page's content
                limited_content = original_content[:max_chars_per_page]
                
                all_content.append(f"""
===== Page: {result.get('title', 'N/A')} =====
URL: {result.get('url', 'N/A')}
Content: {limited_content}
""")
        
        if not all_content:
            return CompressedContent(
                original_length=0,
                compressed_length=0,
                content="No content available",
                strategy=CompressionStrategy.NON_CONTEXT_AWARE_COMBINED
            )
        
        combined_content = "\n\n".join(all_content)
        
        try:
            # Create a single summary for all combined content
            prompt = f"""Summarize the following combined webpage content comprehensively:

{combined_content}

Requirements:
1. Create a comprehensive summary covering all pages
2. Include key information from each source
3. Maintain factual accuracy
4. Maximum length: {Config.SUMMARY_MAX_TOKENS} tokens

Provide a comprehensive summary:"""

            # Log prompt length
            prompt_tokens = self.count_tokens(prompt)
            logger.info(f"Non-context-aware combined summary - Prompt tokens: {prompt_tokens}, Prompt length: {len(prompt)} chars")

            if self.enable_streaming:
                # Stream the summary to console
                print(f"\n📄 Creating combined summary for all {len(search_results.get('results', []))} pages...\n", flush=True)
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates comprehensive summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=Config.SUMMARY_MAX_TOKENS,
                    stream=True
                )
                
                summary_parts = []
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        summary_parts.append(content)
                print("\n")  # New lines after streaming
                summary = "".join(summary_parts)
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates comprehensive summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=Config.SUMMARY_MAX_TOKENS
                )
                summary = response.choices[0].message.content
            
            return CompressedContent(
                original_length=total_original,
                compressed_length=len(summary),
                content=summary,
                strategy=CompressionStrategy.NON_CONTEXT_AWARE_COMBINED
            )
            
        except Exception as e:
            logger.error(f"Error creating combined summary: {str(e)}")
            # Fallback to concatenated snippets
            fallback = "\n\n".join([
                f"{r.get('title', 'N/A')}: {r.get('snippet', 'No summary available')}"
                for r in search_results.get('results', [])
            ])
            return CompressedContent(
                original_length=total_original,
                compressed_length=len(fallback),
                content=fallback,
                strategy=CompressionStrategy.NON_CONTEXT_AWARE_COMBINED
            )
    
    def _context_aware_summary(
        self, 
        search_results: Dict[str, Any],
        query: str,
        current_context: Optional[str] = None
    ) -> CompressedContent:
        """
        Strategy 3: Context-aware summarization considering the query
        """
        # Combine all content with per-page limits
        all_content = []
        total_original = 0
        max_chars_per_page = 5000  # Limit each page to prevent token overflow
        
        for result in search_results.get('results', []):
            if result.get('content'):
                original_content = result.get('content', '')
                total_original += len(original_content)
                
                # Limit each page's content
                limited_content = original_content[:max_chars_per_page]
                
                all_content.append(f"""
Title: {result.get('title', 'N/A')}
URL: {result.get('url', 'N/A')}
Content: {limited_content}
""")
        
        combined_content = "\n\n".join(all_content)
        
        try:
            # Create context-aware summary
            prompt = f"""Given the search query: "{query}"
{f"Current context: {current_context[:1000]}" if current_context else ""}

Analyze the following search results and provide a focused summary that directly addresses the query.
Focus on extracting information most relevant to answering: {query}

Search Results:
{combined_content}  # Already limited per page

Requirements:
1. Focus only on information relevant to the query
2. Prioritize current/recent information
3. Include specific names, dates, and affiliations
4. Maximum length: {Config.SUMMARY_MAX_TOKENS} tokens

Provide a query-focused summary:"""

            # Log prompt length
            prompt_tokens = self.count_tokens(prompt)
            logger.info(f"Context-aware summary - Prompt tokens: {prompt_tokens}, Prompt length: {len(prompt)} chars")

            if self.enable_streaming:
                # Stream the summary to console
                print(f"\n🎯 Creating context-aware summary for query: '{query[:50]}...'\n", flush=True)
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates focused, context-aware summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=Config.SUMMARY_MAX_TOKENS,
                    stream=True
                )
                
                summary_parts = []
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        summary_parts.append(content)
                print("\n")  # New lines after streaming
                summary = "".join(summary_parts)
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates focused, context-aware summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=Config.SUMMARY_MAX_TOKENS
                )
                summary = response.choices[0].message.content
            
            return CompressedContent(
                original_length=total_original,
                compressed_length=len(summary),
                content=summary,
                strategy=CompressionStrategy.CONTEXT_AWARE
            )
            
        except Exception as e:
            logger.error(f"Error creating context-aware summary: {str(e)}")
            # Fallback to simple concatenation
            fallback = "\n\n".join([r.get('snippet', '') for r in search_results.get('results', [])])
            return CompressedContent(
                original_length=total_original,
                compressed_length=len(fallback),
                content=fallback,
                strategy=CompressionStrategy.CONTEXT_AWARE
            )
    
    def _context_aware_with_citations(
        self,
        search_results: Dict[str, Any],
        query: str,
        current_context: Optional[str] = None
    ) -> CompressedContent:
        """
        Strategy 4: Context-aware summarization with citations
        """
        # Track sources with per-page limits
        sources = []
        all_content = []
        total_original = 0
        max_chars_per_page = 5000  # Limit each page to prevent token overflow
        
        for i, result in enumerate(search_results.get('results', [])):
            if result.get('content'):
                source_id = f"[{i+1}]"
                original_content = result.get('content', '')
                total_original += len(original_content)
                
                # Limit each page's content
                limited_content = original_content[:max_chars_per_page]
                
                sources.append({
                    'id': source_id,
                    'title': result.get('title', 'N/A'),
                    'url': result.get('url', 'N/A')
                })
                
                all_content.append(f"""
{source_id} Title: {result.get('title', 'N/A')}
Content: {limited_content}
""")
        
        combined_content = "\n\n".join(all_content)
        
        try:
            # Create context-aware summary with citations
            prompt = f"""Given the search query: "{query}"
{f"Current context: {current_context[:1000]}" if current_context else ""}

Analyze the following search results and provide a focused summary with citations.

Search Results (with source IDs):
{combined_content}  # Already limited per page

Requirements:
1. Focus on information relevant to: {query}
2. Include inline citations using [1], [2], etc. for each fact
3. Prioritize current/recent information
4. Include specific names, dates, and affiliations with citations
5. Maximum length: {Config.SUMMARY_MAX_TOKENS} tokens

Provide a query-focused summary with citations:"""

            # Log prompt length
            prompt_tokens = self.count_tokens(prompt)
            logger.info(f"Citation-based summary - Prompt tokens: {prompt_tokens}, Prompt length: {len(prompt)} chars")

            if self.enable_streaming:
                # Stream the summary to console
                print(f"\n📚 Creating summary with citations for: '{query[:50]}...'\n", flush=True)
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates focused summaries with proper citations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=Config.SUMMARY_MAX_TOKENS,
                    stream=True
                )
                
                summary_parts = []
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        summary_parts.append(content)
                print("\n")  # New lines after streaming
                summary = "".join(summary_parts)
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates focused summaries with proper citations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=Config.SUMMARY_MAX_TOKENS
                )
                summary = response.choices[0].message.content
            
            # Append source list
            source_list = "\n\nSources:\n"
            for source in sources:
                source_list += f"{source['id']} {source['title']} - {source['url']}\n"
            
            final_content = summary + source_list
            
            return CompressedContent(
                original_length=total_original,
                compressed_length=len(final_content),
                content=final_content,
                citations=sources,
                strategy=CompressionStrategy.CONTEXT_AWARE_CITATIONS
            )
            
        except Exception as e:
            logger.error(f"Error creating summary with citations: {str(e)}")
            # Fallback
            fallback = "\n\n".join([
                f"[{i+1}] {r.get('title', '')}: {r.get('snippet', '')}"
                for i, r in enumerate(search_results.get('results', []))
            ])
            return CompressedContent(
                original_length=total_original,
                compressed_length=len(fallback),
                content=fallback,
                citations=sources,
                strategy=CompressionStrategy.CONTEXT_AWARE_CITATIONS
            )
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation)
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
