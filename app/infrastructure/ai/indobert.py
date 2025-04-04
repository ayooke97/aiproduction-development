import os
import numpy as np
from typing import List, Any, Dict, Optional
from app.core.logging import get_logger
from app.core.exceptions import DependencyNotFoundError

logger = get_logger(__name__)


class IndoBERTClient:
    """Client for generating embeddings using IndoBERT model."""
    
    def __init__(self, use_gpu: bool = True):
        """
        Initialize the IndoBERT embeddings model.
        
        Args:
            use_gpu: Whether to use GPU if available
        """
        self.model = None
        self.tokenizer = None
        self.device = None
        self.is_available = False
        
        try:
            # Try importing required packages
            import torch
            from transformers import AutoTokenizer, AutoModel
            
            # Suppress warnings
            import warnings
            warnings.filterwarnings("ignore")
            
            # Set environment variables to suppress warnings
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            
            # Load IndoBERT tokenizer and model
            model_name = "indolem/indobert-base-uncased"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            
            # Move model to GPU if available and requested
            if use_gpu and torch.cuda.is_available():
                self.device = torch.device("cuda")
                logger.info("Using GPU for IndoBERT model")
            else:
                self.device = torch.device("cpu")
                logger.info("Using CPU for IndoBERT model")
            
            self.model.to(self.device)
            self.is_available = True
            logger.info("IndoBERT model loaded successfully")
        except ImportError as e:
            logger.warning(f"IndoBERT dependencies not available: {str(e)}")
            self.is_available = False
        except Exception as e:
            logger.error(f"Error loading IndoBERT model: {str(e)}")
            self.is_available = False
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embeddings as lists of floats
        """
        if not self.is_available:
            logger.warning("IndoBERT is not available, returning empty embeddings")
            return [[0.0] * 768] * len(texts)  # Return dummy embeddings
        
        try:
            import torch
            
            embeddings = []
            
            # Process texts in batches
            batch_size = 8  # Adjust based on available memory
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_embeddings = self._get_batch_embeddings(batch_texts)
                embeddings.extend(batch_embeddings)
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return [[0.0] * 768] * len(texts)  # Return dummy embeddings
    
    def _get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: Batch of texts to generate embeddings for
            
        Returns:
            List of embeddings
        """
        import torch
        
        # Tokenize texts
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )
        
        # Move inputs to the correct device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # Use mean of last hidden states as embeddings
        embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        
        # Convert to list of lists
        return [embedding.tolist() for embedding in embeddings]
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        # Avoid division by zero
        if norm1 == 0 or norm2 == 0:
            return 0
            
        similarity = dot_product / (norm1 * norm2)
        
        # Ensure the result is between 0 and 1
        return float(max(0, min(1, similarity)))
    
    def rank_documents(
        self, 
        query: str, 
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank documents by relevance to a query.
        
        Args:
            query: The query text
            documents: List of documents
            
        Returns:
            Documents sorted by relevance
        """
        if not self.is_available or not documents:
            logger.warning("IndoBERT unavailable or no documents to rank")
            return documents
        
        try:
            # Generate query embedding
            query_embedding = self.get_embeddings([query])[0]
            
            # Generate document embeddings and calculate similarity
            for doc in documents:
                content = doc.get("content", "")
                # Use first 1000 chars for efficiency
                doc_text = content[:1000] if content else ""
                
                if doc_text:
                    doc_embedding = self.get_embeddings([doc_text])[0]
                    similarity = self.calculate_similarity(query_embedding, doc_embedding)
                    doc["relevance_score"] = similarity
                else:
                    doc["relevance_score"] = 0.0
            
            # Sort by relevance score
            sorted_docs = sorted(
                documents, 
                key=lambda x: x.get("relevance_score", 0), 
                reverse=True
            )
            
            return sorted_docs
        except Exception as e:
            logger.error(f"Error ranking documents: {str(e)}")
            return documents