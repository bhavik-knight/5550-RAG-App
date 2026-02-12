
from src.rag_query import RAGQueryEngine
from src.ingest import KnowledgeBaseIngestor
import src.config as config


def main(mode='automated'):
    """Main function to run the RAG application in the specified mode."""
    
    if mode == "ingest":
        # Using the hardcoded filename as per current project structure
        ingestor = KnowledgeBaseIngestor("DH-Chapter2.pdf")
        ingestor.run()
    elif mode == "query":
        try:
            engine = RAGQueryEngine()
            run_interactive(engine)
        except Exception as e:
            print(f"Failed to load vector store: {e}. Please run with --mode ingest first.")
    elif mode == "automated":
        try:
            engine = RAGQueryEngine()
            run_automated_execution(engine)
        except Exception as e:
            print(f"Failed to load vector store: {e}. Please run with --mode ingest first.")


def run_automated_execution(engine):
    print("Running automated queries...")
    queries = [
        "What is Crosswalk guards?",
        "How is the weather today?",
        "What to do if moving through an intersection with a green signal?",
        "What to do when approached by an emergency vehicle?"
    ]
    
    output_dir = config.Config.OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    results_path = output_dir / "results.txt"
    
    with open(results_path, "w") as f:
        for q in queries:

            res = engine.run_query(q)
            formatted = RAGQueryEngine.format_result(res)
            f.write(formatted)
            print(formatted)
            
    print(f"Results saved to {results_path}")

def run_interactive(engine):
    print("Starting Interactive RAG System. Type 'exit' to quit.")
    
    while True:
        try:
            q = input("\nEnter your question: ")
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
