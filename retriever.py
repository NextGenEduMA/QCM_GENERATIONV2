"""
Retriever module for finding relevant Arabic text chunks.
"""
import numpy as np
from typing import List, Dict, Any
from .embedding import ArabicEmbedder

class ArabicRetriever:
    def __init__(self, embedder: ArabicEmbedder, top_k: int = 3):
        """
        Initialize the Arabic text retriever.
        
        Args:
            embedder: An initialized ArabicEmbedder instance
            top_k: Number of top chunks to retrieve
        """
        self.embedder = embedder
        self.top_k = top_k
    
    def retrieve(self, query: str) -> List[str]:
        """
        Retrieve the most relevant chunks for a query.
        
        Args:
            query: Query text
            
        Returns:
            List of relevant text chunks
        """
        if self.embedder.index is None:
            raise ValueError("Index has not been created yet")
        
        # Embed the query
        query_embedding = self.embedder.model.encode([query])
        
        # Search the index
        k = min(self.top_k, len(self.embedder.chunks))
        distances, indices = self.embedder.index.search(query_embedding.astype('float32'), k)
        
        # Get the relevant chunks
        relevant_chunks = [self.embedder.chunks[idx] for idx in indices[0]]
        
        return relevant_chunks