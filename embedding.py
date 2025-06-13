"""
Embedding and indexing module for Arabic text.
"""
import os
import numpy as np
import faiss
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

class ArabicEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize the Arabic text embedder.
        
        Args:
            model_name: Name of the embedding model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of texts using the sentence transformer model.
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            Array of embeddings
        """
        return self.model.encode(texts, show_progress_bar=True)
    
    def create_index(self, texts: List[str]) -> None:
        """
        Create a FAISS index from the text chunks.
        
        Args:
            texts: List of text chunks to index
        """
        self.chunks = texts
        embeddings = self.embed_texts(texts)
        
        # Get embedding dimension
        dimension = embeddings.shape[1]
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        
        # Add embeddings to the index
        self.index.add(embeddings.astype('float32'))
        
        print(f"Created index with {len(texts)} chunks")
    
    def save_index(self, index_path: str, chunks_path: str) -> None:
        """
        Save the FAISS index and chunks to disk.
        
        Args:
            index_path: Path to save the index
            chunks_path: Path to save the chunks
        """
        if self.index is None:
            raise ValueError("Index has not been created yet")
        
        # Save the index
        faiss.write_index(self.index, index_path)
        
        # Save the chunks
        with open(chunks_path, 'w', encoding='utf-8') as f:
            for chunk in self.chunks:
                f.write(chunk + "\n===CHUNK_SEPARATOR===\n")
        
        print(f"Saved index to {index_path} and chunks to {chunks_path}")
    
    def load_index(self, index_path: str, chunks_path: str) -> None:
        """
        Load the FAISS index and chunks from disk.
        
        Args:
            index_path: Path to the saved index
            chunks_path: Path to the saved chunks
        """
        # Load the index
        self.index = faiss.read_index(index_path)
        
        # Load the chunks
        with open(chunks_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.chunks = content.split("\n===CHUNK_SEPARATOR===\n")
            # Remove the last empty chunk if it exists
            if self.chunks[-1] == '':
                self.chunks = self.chunks[:-1]
        
        print(f"Loaded index with {len(self.chunks)} chunks")