import shutil
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from src.embedder import JinaEmbeddingModel
from src.config import Config

class KnowledgeBaseIngestor:
    def __init__(self, data_file_name: str):
        self.data_path = Config.DATA_DIR / data_file_name
        self.chroma_db_dir = Config.CHROMA_DB_DIR
        

    def setup_directories(self):
        print("Setting up storage directories...")
        self.output_dir.mkdir(exist_ok=True)
        
        if self.chroma_db_dir.exists():
            print("Clearing existing vector store...")
            shutil.rmtree(self.chroma_db_dir)
            
        return self.chroma_db_dir

    def load_documents(self):
        print(f"Loading document from {self.data_path}...")
        if not self.data_path.exists():
            print(f"Error: Data file not found at {self.data_path.absolute()}")
            exit(1)
            
        loader = PyPDFLoader(str(self.data_path))
        return loader.load()

    def split_documents(self, docs, chunk_size: int = 1000, chunk_overlap: int = 200):
        print("Splitting text...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return text_splitter.split_documents(docs)

    def create_vector_store(self, splits):
        print("Initializing embeddings and vector store...")
        embedding_model = JinaEmbeddingModel()
        embeddings = embedding_model.embeddings_model
        
        vectorstore = Chroma.from_documents(
            documents=splits, 
            embedding=embeddings,
            persist_directory=str(self.chroma_db_dir)
        )   
        return vectorstore

    def run(self):
        print("Starting Ingestion Pipeline...")
        self.setup_directories()
        docs = self.load_documents()
        splits = self.split_documents(docs)
        self.create_vector_store(splits)
        print(f"Ingestion completed. Vector store created at {self.chroma_db_dir}")

if __name__ == "__main__":
    # Default filename for standalone execution
    ingestor = KnowledgeBaseIngestor("DH-Chapter2.pdf")
    ingestor.run()
