from langchain_community.embeddings import JinaEmbeddings
from src.config import Config

class JinaEmbeddingModel:
    def __init__(self, api_key: str = None, model_name: str = "jina-embeddings-v4"):
        """
        Initialize the Jina Embeddings model.
        
        Args:
            api_key (str, optional): The Jina API key. If not provided, it will be read from JINA_API_KEY env var.
            model_name (str, optional): The name of the Jina model to use. Defaults to "jina-embeddings-v4".
        """
        self.api_key = api_key or Config.JINA_API_KEY
        
        if not self.api_key:
            raise ValueError("JINA_API_KEY must be provided or set in environment variables.")
            
        self.model_name = model_name
        self._model = self._create_embeddings_model(model_name)

    def _create_embeddings_model(self, model_name: str) -> JinaEmbeddings:
        """Create and return the JinaEmbeddings instance."""
        try:
            return JinaEmbeddings(
                jina_api_key=self.api_key,
                model_name=model_name
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Jina Embeddings: {e}")

    @property
    def embeddings_model(self) -> JinaEmbeddings:
        """Return the initialized embedding model."""
        return self._model
    
    @embeddings_model.setter
    def embeddings_model(self, model_name: str):
        """Set the embedding model."""
        self._model = self._create_embeddings_model(model_name)
