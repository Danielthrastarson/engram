from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
from utils import config
from PIL import Image

class EmbeddingHandler:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingHandler, cls).__new__(cls)
            cls._instance.text_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
            # Lazy load CLIP model to save RAM if not used immediately
            cls._instance.clip_model = None 
        return cls._instance

    def _get_clip_model(self):
        if self.clip_model is None:
            # clip-ViT-B-32 works for both Image and Text 
            # We use it for images, and map text to same space if we want cross-modal search
            self.clip_model = SentenceTransformer('clip-ViT-B-32')
        return self.clip_model

    def generate_embedding(self, content: Union[str, List[str], Image.Image]) -> np.ndarray:
        """
        Generate normalized embeddings for text OR image.
        Returns numpy array.
        """
        # Image Handling
        if isinstance(content, Image.Image):
            model = self._get_clip_model()
            embeddings = model.encode(content, convert_to_numpy=True)
            
        # Text Handling
        else:
            # Default to text model
            embeddings = self.text_model.encode(content, convert_to_numpy=True)
        
        # Normalize
        if len(embeddings.shape) == 1:
            norm = np.linalg.norm(embeddings)
            if norm > 0:
                embeddings = embeddings / norm
        else:
            norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / (norm + 1e-10)
            
        return embeddings

