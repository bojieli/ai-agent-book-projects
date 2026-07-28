"""Document chunking and indexing script"""

import os
import json
import hashlib
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from config import ChunkingConfig, KnowledgeBaseConfig, KnowledgeBaseType


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DocumentChunker:
    """Document chunking with configurable strategies"""
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
        
    def chunk_text(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller segments.
        
        Args:
            text: Document text to chunk
            doc_id: Document identifier
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        if self.config.respect_paragraph_boundary:
            chunks = self._chunk_by_paragraphs(text, doc_id)
        else:
            chunks = self._chunk_by_size(text, doc_id)
        
        logger.info(f"Created {len(chunks)} chunks for document {doc_id}")
        return chunks
    
    def _chunk_by_paragraphs(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """Chunk text respecting paragraph boundaries"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # If single paragraph exceeds max size, split it
            if para_size > self.config.max_chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append(self._create_chunk(chunk_text, doc_id, len(chunks)))
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph
                sentences = self._split_into_sentences(para)
                for sent in sentences:
                    if len(sent) > self.config.max_chunk_size:
                        # Force split very long sentences
                        for i in range(0, len(sent), self.config.chunk_size):
                            sub_chunk = sent[i:i + self.config.chunk_size]
                            chunks.append(self._create_chunk(sub_chunk, doc_id, len(chunks)))
                    else:
                        chunks.append(self._create_chunk(sent, doc_id, len(chunks)))
                continue
            
            # Check if adding this paragraph exceeds chunk size
            if current_size + para_size > self.config.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(self._create_chunk(chunk_text, doc_id, len(chunks)))
                
                # Start new chunk with overlap
                if self.config.chunk_overlap > 0 and current_chunk:
                    # Keep last paragraph for overlap
                    current_chunk = [current_chunk[-1], para]
                    current_size = len(current_chunk[0]) + para_size
                else:
                    current_chunk = [para]
                    current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Save final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            if len(chunk_text) >= self.config.min_chunk_size:
                chunks.append(self._create_chunk(chunk_text, doc_id, len(chunks)))
        
        return chunks
    
    def _chunk_by_size(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """Simple size-based chunking"""
        chunks = []
        
        for i in range(0, len(text), self.config.chunk_size - self.config.chunk_overlap):
            chunk_text = text[i:i + self.config.chunk_size]
            
            if len(chunk_text) >= self.config.min_chunk_size:
                chunks.append(self._create_chunk(chunk_text, doc_id, len(chunks)))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences (simple implementation)"""
        # Simple sentence splitting for Chinese and English
        import re
        
        # Split on common sentence endings
        sentences = re.split(r'([。！？\.!?]+)', text)
        
        # Reconstruct sentences with their endings
        result = []
        # Step to the end of the list: re.split with a capturing group yields
        # [text, delim, text, delim, ..., trailing_text], so stopping at
        # len(sentences) - 1 dropped the trailing fragment whenever the text
        # did not end in terminal punctuation (and returned [] for text with
        # none at all). The strip-and-filter below still discards the empty
        # tail that re.split produces when the text does end in punctuation.
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                result.append(sentences[i] + sentences[i + 1])
            else:
                result.append(sentences[i])
        
        return [s.strip() for s in result if s.strip()]
    
    def _create_chunk(self, text: str, doc_id: str, chunk_index: int) -> Dict[str, Any]:
        """Create a chunk with metadata"""
        chunk_id = f"{doc_id}_chunk_{chunk_index}"
        
        return {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "text": text,
            "chunk_index": chunk_index,
            "char_count": len(text),
            "hash": hashlib.md5(text.encode()).hexdigest()
        }


class DocumentIndexer:
    """Index documents to knowledge base"""
    
    def __init__(self, 
                 kb_config: Optional[KnowledgeBaseConfig] = None,
                 chunking_config: Optional[ChunkingConfig] = None):
        self.kb_config = kb_config or KnowledgeBaseConfig()
        self.chunker = DocumentChunker(chunking_config)
        self.indexed_docs = {}
        
    def index_file(self, file_path: str, doc_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Index a single file.
        
        Args:
            file_path: Path to the file
            doc_id: Optional document ID
            
        Returns:
            Indexing result
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        # Generate doc_id if not provided
        if not doc_id:
            doc_id = file_path.stem
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"error": f"Error reading file: {e}"}
        
        # Chunk the document
        chunks = self.chunker.chunk_text(content, doc_id)
        
        # Index chunks
        result = self._index_chunks(chunks, doc_id, content)
        
        # Store full document
        self._store_document(doc_id, content, {"source_file": str(file_path)})
        
        return result
    
    def index_directory(self, dir_path: str, extensions: List[str] = None) -> Dict[str, Any]:
        """
        Index all files in a directory.
        
        Args:
            dir_path: Directory path
            extensions: File extensions to include (e.g., ['.txt', '.md'])
            
        Returns:
            Indexing results
        """
        dir_path = Path(dir_path)
        if not dir_path.exists():
            return {"error": f"Directory not found: {dir_path}"}
        
        extensions = extensions or ['.txt', '.md', '.json']
        results = {"indexed": [], "errors": []}
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                doc_id = f"{file_path.parent.name}/{file_path.stem}"
                result = self.index_file(str(file_path), doc_id)
                
                if "error" in result:
                    results["errors"].append({
                        "file": str(file_path),
                        "error": result["error"]
                    })
                else:
                    results["indexed"].append({
                        "file": str(file_path),
                        "doc_id": doc_id,
                        "chunks": result.get("chunks_indexed", 0)
                    })
        
        logger.info(f"Indexed {len(results['indexed'])} files, {len(results['errors'])} errors")
        return results
    
    def _index_chunks(self, chunks: List[Dict[str, Any]], doc_id: str, full_content: str) -> Dict[str, Any]:
        """Index chunks to the knowledge base"""
        if self.kb_config.type == KnowledgeBaseType.LOCAL:
            return self._index_to_local(chunks, doc_id)
        elif self.kb_config.type == KnowledgeBaseType.DIFY:
            return self._index_to_dify(chunks, doc_id, full_content)
        else:
            return {"error": f"Unsupported KB type: {self.kb_config.type}"}
    
    def _index_to_local(self, chunks: List[Dict[str, Any]], doc_id: str) -> Dict[str, Any]:
        """Index to local retrieval pipeline"""
        indexed_count = 0
        errors = []
        
        for chunk in chunks:
            try:
                # Index each chunk
                response = requests.post(
                    f"{self.kb_config.local_base_url}/index",
                    json={
                        "text": chunk["text"],
                        "doc_id": chunk["doc_id"],
                        "metadata": {
                            "chunk_id": chunk["chunk_id"],
                            "chunk_index": chunk["chunk_index"],
                            "char_count": chunk["char_count"]
                        }
                    }, timeout=30
                )
                response.raise_for_status()
                indexed_count += 1
                
            except Exception as e:
                errors.append(f"Error indexing chunk {chunk['chunk_id']}: {e}")
        
        result = {
            "doc_id": doc_id,
            "chunks_indexed": indexed_count,
            "total_chunks": len(chunks)
        }
        
        if errors:
            result["errors"] = errors
        
        return result
    
    def _index_to_dify(self, chunks: List[Dict[str, Any]], doc_id: str, full_content: str) -> Dict[str, Any]:
        """Index to Dify knowledge base"""
        if not self.kb_config.dify_api_key:
            return {"error": "Dify API key not configured"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.kb_config.dify_api_key}",
                "Content-Type": "application/json"
            }
            
            # Dify expects documents, not individual chunks
            # So we'll create segments from our chunks
            segments = []
            for chunk in chunks:
                segments.append({
                    "content": chunk["text"],
                    "keywords": [],  # Can add keywords if needed
                    "enabled": True
                })
            
            payload = {
                "name": doc_id,
                "text": full_content,
                "indexing_technique": "high_quality",  # or "economy"
                "process_rule": {
                    "mode": "custom",
                    "rules": {
                        "pre_processing_rules": [],
                        "segmentation": {
                            "separator": "\n\n",
                            "max_tokens": self.chunker.config.chunk_size // 4  # Rough token estimate
                        }
                    }
                }
            }
            
            if self.kb_config.dify_dataset_id:
                # Add to existing dataset
                response = requests.post(
                    f"{self.kb_config.dify_base_url}/datasets/{self.kb_config.dify_dataset_id}/documents",
                    headers=headers,
                    json=payload, timeout=30
                )
            else:
                # Create new document
                response = requests.post(
                    f"{self.kb_config.dify_base_url}/documents",
                    headers=headers,
                    json=payload, timeout=30
                )
            
            response.raise_for_status()
            
            return {
                "doc_id": doc_id,
                "chunks_indexed": len(chunks),
                "total_chunks": len(chunks),
                "dify_response": response.json()
            }
            
        except Exception as e:
            return {"error": f"Error indexing to Dify: {e}"}
    
    def _store_document(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Store full document locally"""
        # Store in local file for retrieval
        store_path = self.kb_config.document_store_path
        
        try:
            # Load existing store
            if os.path.exists(store_path):
                with open(store_path, 'r', encoding='utf-8') as f:
                    store = json.load(f)
            else:
                store = {}
            
            # Add document
            store[doc_id] = {
                "doc_id": doc_id,
                "content": content,
                "metadata": metadata,
                "indexed_at": datetime.now().isoformat()
            }
            
            # Save store
            with open(store_path, 'w', encoding='utf-8') as f:
                json.dump(store, f, ensure_ascii=False, indent=2)
            
            self.indexed_docs[doc_id] = True
            logger.info(f"Stored document {doc_id}")
            
        except Exception as e:
            logger.error(f"Error storing document: {e}")


def main():
    """Main function for standalone chunking and indexing"""
    import argparse
    from config import Config
    
    parser = argparse.ArgumentParser(description="Chunk and index documents")
    parser.add_argument("path", help="File or directory path to index")
    parser.add_argument("--chunk-size", type=int, default=2048, help="Chunk size in characters")
    parser.add_argument("--max-chunk-size", type=int, default=1024, help="Max chunk size")
    parser.add_argument("--overlap", type=int, default=200, help="Chunk overlap")
    parser.add_argument("--kb-type", choices=["local", "dify"], default="local", help="Knowledge base type")
    parser.add_argument("--extensions", nargs="+", default=[".txt", ".md"], help="File extensions to index")
    
    args = parser.parse_args()
    
    # Create config
    config = Config.from_env()
    config.chunking.chunk_size = args.chunk_size
    config.chunking.max_chunk_size = args.max_chunk_size
    config.chunking.chunk_overlap = args.overlap
    config.knowledge_base.type = KnowledgeBaseType(args.kb_type)
    
    # Create indexer
    indexer = DocumentIndexer(config.knowledge_base, config.chunking)
    
    # Index path
    path = Path(args.path)
    if path.is_file():
        result = indexer.index_file(str(path))
    elif path.is_dir():
        result = indexer.index_directory(str(path), args.extensions)
    else:
        print(f"Path not found: {path}")
        return
    
    # Print results
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
