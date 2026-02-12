import sys
from pathlib import Path
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from src.embedder import JinaEmbeddingModel
from src.config import Config

class RAGQueryEngine:
    def __init__(self):
        self.output_dir = Config.OUTPUT_DIR
        self.chroma_db_dir = self.output_dir / "chroma_db"
        self.vectorstore = None
        self.retriever = None
        self.chain = None
        self.prompt = None
        self.llm = None
        
        # Load components on init
        self._load_vector_store()
        self._setup_rag_components()

    def _load_vector_store(self):
        print("Loading vector store...")
        if not self.chroma_db_dir.exists():
            print(f"Error: Vector store not found at {self.chroma_db_dir}. Please run ingestion first.")
            sys.exit(1)
            
        embedding_model = JinaEmbeddingModel()
        embeddings = embedding_model.embeddings_model
        
        self.vectorstore = Chroma(
            persist_directory=str(self.chroma_db_dir),
            embedding_function=embeddings
        )

    def _setup_rag_components(self):
        self.retriever = self.vectorstore.as_retriever()
        # Using Llama-3.3-70B via Groq - free, fast, and excellent for RAG
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=512,
            api_key=Config.GROQ_API_KEY
        )
        
        template = """
                    You are a helpful assistant. Use the following context to answer the question.
                    If the answer is not in the context, say "I don't know".
                    Include source citations or page numbers in your answer.

                    Context: {context}
                    Question: {question}
                    Answer:
                    """
        self.prompt = ChatPromptTemplate.from_template(template)

    def run_query(self, query_text: str):
        # Retrieval
        docs = self.retriever.invoke(query_text)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        # Augmentation & Generation
        chain = (
            {"context": lambda x: context_text, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        answer = chain.invoke(query_text)
        
        # Citations - only if answer is found (not "I don't know")
        citations = []
        if "i don't know" not in answer.lower():
            for doc in docs:
                source = doc.metadata.get('source', 'Unknown')
                # Clean source path to just filename
                if source != 'Unknown':
                     source = Path(source).name
                     
                page = doc.metadata.get('page', -1)
                
                # PyPDFLoader usually uses 0-indexed pages
                citation_text = f"{source}"
                if isinstance(page, int) and page >= 0:
                     citation_text += f" (Page {page + 1})"
                     
                citations.append(citation_text)
        
        return {
            "query": query_text,
            "answer": answer,
            "citations": list(set(citations))
        }

    @staticmethod
    def format_result(result):
        output = f"Question: {result['query']}\n"
        output += f"Answer: {result['answer']}\n"
        if result.get('citations'):
            output += f"Sources: {', '.join(result['citations'])}\n"
        output += "-" * 120 + "\n"
        return output

def main():
    engine = RAGQueryEngine()
    print("RAG System Ready. Type 'exit' to quit.")
    
    while True:
        try:
            q = input("\nQuery: ")
            if q.lower() in ('exit', 'quit'):
                break
            if not q.strip():
                continue
                
            res = engine.run_query(q)
            print("\n" + RAGQueryEngine.format_result(res))
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
