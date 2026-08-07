"""
Hierarchical Semantic Routing for Tool Discovery.

Implements a two-stage algorithm for matching tool requests to relevant tools:
1. Server-level routing: Filter candidate servers by domain/platform
2. Tool-level routing: Rank tools within selected servers by semantic similarity

This approach reduces search complexity while maintaining precision, inspired by MCP-Zero.
"""

from typing import List, Dict, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from tool_knowledge_base import ServerDefinition, ToolDefinition
import config


class SemanticRouter:
    """Hierarchical semantic routing for tool discovery."""
    
    def __init__(self, servers: List[ServerDefinition]):
        self.servers = servers
        self.server_vectorizer = TfidfVectorizer(stop_words='english')
        self.tool_vectorizers: Dict[str, TfidfVectorizer] = {}
        
        # Precompute server embeddings
        self._build_server_index()
        
        # Precompute tool embeddings for each server
        self._build_tool_indices()
    
    def _build_server_index(self):
        """Build TF-IDF index for servers."""
        if not self.servers:
            self.server_embeddings = None
            return
        server_descriptions = [f"{s.name} {s.description}" for s in self.servers]
        try:
            self.server_embeddings = self.server_vectorizer.fit_transform(server_descriptions)
        except ValueError:
            self.server_embeddings = None
    
    def _build_tool_indices(self):
        """Build TF-IDF indices for tools within each server."""
        for server in self.servers:
            if not server.tools:
                continue
            
            tool_descriptions = [
                f"{tool.name} {tool.description}"
                for tool in server.tools
            ]
            
            vectorizer = TfidfVectorizer(stop_words='english')
            embeddings = vectorizer.fit_transform(tool_descriptions)
            
            self.tool_vectorizers[server.name] = vectorizer
            
            # Store embeddings on server for later use
            server._tool_embeddings = embeddings
    
    def route_request(self, tool_request: str, top_k_servers: int = None, 
                      top_k_tools: int = None) -> List[ToolDefinition]:
        """
        Route a tool request to relevant tools using hierarchical semantic matching.
        
        Args:
            tool_request: Natural language description of needed tool
            top_k_servers: Number of top servers to search (default from config)
            top_k_tools: Number of tools to return per server (default from config)
        
        Returns:
            List of relevant tools ranked by relevance
        """
        if top_k_servers is None:
            top_k_servers = config.TOP_K_SERVERS
        if top_k_tools is None:
            top_k_tools = config.TOP_K_TOOLS
        
        # Stage 1: Server-level routing
        relevant_servers = self._route_to_servers(tool_request, top_k_servers)
        
        # Stage 2: Tool-level routing within selected servers
        relevant_tools = []
        for server, server_score in relevant_servers:
            tools_with_scores = self._route_to_tools(server, tool_request, top_k_tools)
            
            # Combine server and tool scores
            for tool, tool_score in tools_with_scores:
                combined_score = 0.3 * server_score + 0.7 * tool_score
                relevant_tools.append((tool, combined_score))
        
        # Sort by combined score and filter by threshold
        relevant_tools.sort(key=lambda x: x[1], reverse=True)
        relevant_tools = [
            (tool, score) for tool, score in relevant_tools 
            if score >= config.SIMILARITY_THRESHOLD
        ]
        
        # Return top tools
        return [tool for tool, _ in relevant_tools[:top_k_tools * top_k_servers]]
    
    def retrieve(self, query: str, top_k: int) -> List[ToolDefinition]:
        """
        Flat top-k tool retrieval across ALL servers (single-shot RAG-style routing).

        Unlike ``route_request`` (which first narrows to a few candidate servers),
        this scores every tool in every server and returns the global top-k. It is the
        most direct embodiment of "turn tool selection into knowledge retrieval": given
        the task description, fetch only the handful of tools most likely to be relevant.

        Args:
            query: Natural language task/request description
            top_k: Number of tools to return

        Returns:
            Up to ``top_k`` tools ranked by combined (server + tool) similarity.
        """
        # Score against every server so no candidate tool is filtered out prematurely.
        relevant_servers = self._route_to_servers(query, len(self.servers))

        scored_tools = []
        for server, server_score in relevant_servers:
            for tool, tool_score in self._route_to_tools(server, query, len(server.tools)):
                combined_score = 0.3 * server_score + 0.7 * tool_score
                scored_tools.append((tool, combined_score))

        scored_tools.sort(key=lambda x: x[1], reverse=True)
        return [tool for tool, _ in scored_tools[:top_k]]

    def _route_to_servers(self, request: str, top_k: int) -> List[Tuple[ServerDefinition, float]]:
        """
        Stage 1: Route request to top-k relevant servers.
        
        Args:
            request: Tool request description
            top_k: Number of top servers to return
        
        Returns:
            List of (server, similarity_score) tuples
        """
        if not self.servers or self.server_embeddings is None:
            return []
        # Vectorize the request
        request_vector = self.server_vectorizer.transform([request])
        # Calculate similarities with all servers
        similarities = cosine_similarity(request_vector, self.server_embeddings)[0]
        
        # Get top-k servers
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [(self.servers[idx], similarities[idx]) for idx in top_indices]
    
    def _route_to_tools(self, server: ServerDefinition, request: str, 
                        top_k: int) -> List[Tuple[ToolDefinition, float]]:
        """
        Stage 2: Route request to top-k relevant tools within a server.
        
        Args:
            server: Server to search within
            request: Tool request description
            top_k: Number of top tools to return
        
        Returns:
            List of (tool, similarity_score) tuples
        """
        if server.name not in self.tool_vectorizers:
            return []
        
        vectorizer = self.tool_vectorizers[server.name]
        tool_embeddings = server._tool_embeddings
        
        # Vectorize the request
        request_vector = vectorizer.transform([request])
        
        # Calculate similarities with all tools in this server
        similarities = cosine_similarity(request_vector, tool_embeddings)[0]
        
        # Get top-k tools
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [(server.tools[idx], similarities[idx]) for idx in top_indices]
    
    def get_routing_details(self, tool_request: str, top_k_servers: int = None,
                           top_k_tools: int = None) -> Dict:
        """
        Get detailed routing information for debugging/visualization.
        
        Returns a dictionary with:
        - request: Original request
        - stage1_servers: List of servers with scores
        - stage2_tools: List of tools with scores per server
        - final_tools: Final ranked list of tools
        """
        if top_k_servers is None:
            top_k_servers = config.TOP_K_SERVERS
        if top_k_tools is None:
            top_k_tools = config.TOP_K_TOOLS
        
        # Stage 1: Server routing
        relevant_servers = self._route_to_servers(tool_request, top_k_servers)
        
        # Stage 2: Tool routing
        stage2_results = {}
        all_tools = []
        
        for server, server_score in relevant_servers:
            tools_with_scores = self._route_to_tools(server, tool_request, top_k_tools)
            stage2_results[server.name] = {
                'server_score': server_score,
                'tools': [(tool.name, tool_score) for tool, tool_score in tools_with_scores]
            }
            
            # Calculate combined scores
            for tool, tool_score in tools_with_scores:
                combined_score = 0.3 * server_score + 0.7 * tool_score
                all_tools.append((tool, combined_score, server.name))
        
        # Sort and filter
        all_tools.sort(key=lambda x: x[1], reverse=True)
        final_tools = [
            {'name': tool.name, 'server': server, 'score': score}
            for tool, score, server in all_tools[:top_k_tools * top_k_servers]
            if score >= config.SIMILARITY_THRESHOLD
        ]
        
        return {
            'request': tool_request,
            'stage1_servers': [
                {'name': s.name, 'score': score} 
                for s, score in relevant_servers
            ],
            'stage2_tools': stage2_results,
            'final_tools': final_tools
        }


class StructuredRequestParser:
    """
    Parse structured tool requests from LLM.
    
    MCP-Zero uses structured requests in format:
    <tool_request>
    server: [platform/domain description]
    tool: [operation description]
    </tool_request>
    """
    
    @staticmethod
    def parse_request(text: str) -> Dict[str, str]:
        """
        Parse structured tool request from text.
        
        Returns dict with 'server' and 'tool' fields, or None if not found.
        """
        if '<tool_request>' not in text:
            return None
        
        start = text.find('<tool_request>')
        end = text.find('</tool_request>', start + len('<tool_request>'))
        if end == -1:
            return None
        request_text = text[start + len('<tool_request>'):end].strip()
        
        result = {}
        for line in request_text.split('\n'):
            line = line.strip()
            if line.startswith('server:'):
                result['server'] = line[7:].strip()
            elif line.startswith('tool:'):
                result['tool'] = line[5:].strip()
        
        return result if 'server' in result and 'tool' in result else None
    
    @staticmethod
    def format_request(server_desc: str, tool_desc: str) -> str:
        """Format a structured tool request."""
        return f"""<tool_request>
server: {server_desc}
tool: {tool_desc}
</tool_request>"""
