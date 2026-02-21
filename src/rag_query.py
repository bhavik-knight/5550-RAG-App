import sys
from pathlib import Path
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from src.embedder import JinaEmbeddingModel
from src.config import Config
from src.security import SecurityLayer, POLICY_BLOCK, LLMTimeoutError
from src.evaluation import RAGEvaluator
from langchain_openai import ChatOpenAI

class RAGQueryEngine:
    def __init__(self):
        self.chroma_db_dir = Config.CHROMA_DB_DIR
        self.vectorstore = None
        self.retriever = None
        self.chain = None
        self.prompt = None
        self.llm = None
        self.security = SecurityLayer()
        self.evaluator = RAGEvaluator(llm=None) # Will update after LLM setup
        
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
        
        # Switching to OpenRouter (OpenAI-compatible)
        self.llm = ChatOpenAI(
            model="liquid/lfm-2.5-1.2b-instruct:free",
            temperature=0.1,
            max_tokens=512,
            openai_api_key=Config.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://mcda.smu.ca", # Optional referer
                "X-Title": "MCDA RAG Assignment"
            }
        )
        
        # Also update evaluator's LLM to use OpenRouter
        self.evaluator.llm = self.llm
        
        # System Prompt from Config
        system_prompt = Config.HARDENED_SYSTEM_PROMPT
        
        template = f"""
                    {{system_prompt}}

                    Context: {{context}}
                    Question: {{question}}
                    Answer:
                    """
        self.prompt = ChatPromptTemplate.from_template(template.format(system_prompt=system_prompt, context="{context}", question="{question}"))

    def run_query(self, query_text: str, skip_faithfulness: bool = False):
        # STEP 1: Run Input Guardrails (Length, PII, Off-Topic, Injection Sanitization)
        sec_results = self.security.process_input(query_text)
        if sec_results["errors"]:
            self.evaluator.log_event(sec_results["errors"][0])
            return {
                "query": query_text,
                "answer": self.security.get_refusal(sec_results["errors"][0]),
                "guardrails_triggered": sec_results["errors"],
                "error_code": sec_results["errors"][0],
                "chunks": [],
                "eval": {"faithfulness": "N/A", "relevance": 0.0}
            }

        # STEP 2: Retrieve chunks from ChromaDB and apply Instruction-Data Separation delimiters
        docs = self.retriever.invoke(query_text)
        context_text = self.security.output.wrap_context(docs)
        
        # STEP 3: Check Retrieval Confidence
        rel_metrics = self.evaluator.calculate_retrieval_relevance(docs)
        if not self.security.output.validate_retrieval_confidence(docs):
            self.evaluator.log_event("RETRIEVAL_EMPTY")
            return {
                "query": query_text,
                "answer": self.security.get_refusal("RETRIEVAL_EMPTY"),
                "guardrails_triggered": ["RETRIEVAL_EMPTY"],
                "error_code": "RETRIEVAL_EMPTY",
                "chunks": [doc.page_content for doc in docs],
                "eval": {"faithfulness": "N/A", "relevance": rel_metrics["avg_relevance"]}
            }

        # STEP 4: Query the LLM with the hardened System Prompt (wrapped in 30s timeout)
        try:
            # Re-creating the chain to ensure it's fresh
            chain = (
                {"context": lambda x: context_text, "question": RunnablePassthrough()}
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
            
            # Application of 30s timeout via ExecutionLimits
            answer = self.security.limits.run_with_timeout(
                chain.invoke, 
                Config.LLM_TIMEOUT_SECONDS, 
                query_text
            )
        except LLMTimeoutError:
            self.evaluator.log_event("LLM_TIMEOUT")
            return {
                "query": query_text,
                "answer": self.security.get_refusal("LLM_TIMEOUT"),
                "guardrails_triggered": ["LLM_TIMEOUT"],
                "error_code": "LLM_TIMEOUT",
                "chunks": [doc.page_content for doc in docs],
                "eval": {"faithfulness": "N/A", "relevance": rel_metrics["avg_relevance"]}
            }
        except Exception as e:
            if "429" in str(e):
                raise # Let main.py handle retry
            self.evaluator.log_event("LLM_ERROR")
            return {
                "query": query_text,
                "answer": f"Technical Error: {e}",
                "guardrails_triggered": ["LLM_ERROR"],
                "error_code": "LLM_ERROR",
                "chunks": [doc.page_content for doc in docs],
                "eval": {"faithfulness": "N/A", "relevance": rel_metrics["avg_relevance"]}
            }

        # STEP 5: Run Output Guardrails (Length, Output Validation for leaked instructions)
        out_sec = self.security.process_output(answer)
        if out_sec["errors"]:
             self.evaluator.log_event(POLICY_BLOCK)
             return {
                "query": query_text,
                "answer": self.security.get_refusal(POLICY_BLOCK),
                "guardrails_triggered": out_sec["errors"],
                "error_code": POLICY_BLOCK,
                "chunks": [doc.page_content for doc in docs],
                "eval": {"faithfulness": "N/A", "relevance": rel_metrics["avg_relevance"]}
            }
        
        # STEP 6: Run the Faithfulness/Evaluation signals on the final output
        faithfulness = "Skipped"
        if not skip_faithfulness:
            faithfulness = self.evaluator.check_faithfulness(query_text, answer, context_text)
        
        self.evaluator.log_event(None) # Successful full run
        
        # Citations
        citations = []
        if "i don't know" not in answer.lower():
            for doc in docs:
                source = doc.metadata.get('source', 'Unknown')
                if source != 'Unknown':
                     source = Path(source).name
                page = doc.metadata.get('page', -1)
                citation_text = f"{source} (Page {page + 1})" if page >= 0 else source
                citations.append(citation_text)
        
        return {
            "query": query_text,
            "answer": answer,
            "guardrails_triggered": [],
            "error_code": "None",
            "chunks": [doc.page_content for doc in docs],
            "citations": list(set(citations)),
            "eval": {"faithfulness": faithfulness, "relevance": rel_metrics["avg_relevance"]}
        }

    @staticmethod
    def format_result(result):
        output = f"Question: {result['query']}\n"
        output += f"Answer: {result['answer']}\n"
        if result.get('eval'):
            output += f"Faithfulness/Eval Score: {result['eval']['faithfulness']} (Relevance: {result['eval']['relevance']:.2f})\n"
        if result.get('citations'):
            output += f"Sources: {', '.join(result['citations'])}\n"
        output += "-" * 120 + "\n"
        return output

if __name__ == "__main__":
    # Standard testing block
    engine = RAGQueryEngine()
    print(engine.run_query("What are the road rules?"))
