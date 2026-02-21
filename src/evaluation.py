import logging
import json
from src.config import Config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class RAGEvaluator:
    def __init__(self, llm=None):
        self.llm = llm # Passed from RAGQueryEngine
        self.stats = {
            "total_queries": 0,
            "guardrails_triggered": {},
            "faithfulness_scores": [],
            "relevance_scores": []
        }

    def check_faithfulness(self, query: str, answer: str, context: str):
        """
        Uses LLM to evaluate if the answer is faithful to the retrieved context.
        Returns 1.0 (Yes), 0.0 (No), or "N/A".
        """
        if not answer or not context or "sorry" in answer.lower() or "i don't know" in answer.lower():
            return "N/A"

        prompt = ChatPromptTemplate.from_template("""
        You are an evaluator for a RAG system. 
        Your task is to determine if the provided Answer is faithful to the Given Context.
        
        Rules:
        1. Answer 'Yes' if the answer is strictly supported by the context.
        2. Answer 'No' if the answer contains information not present in the context (hallucinations).
        3. Do not use your own knowledge; only use the Given Context.
        
        Given Context: {context}
        Query: {query}
        Answer: {answer}
        
        Faithful (Yes/No):""")
        
        # LLM-based verification
        if self.llm:
            try:
                chain = prompt | self.llm | StrOutputParser()
                result = chain.invoke({"context": context, "query": query, "answer": answer}).strip()
            except Exception as e:
                logging.warning(f"Evaluation LLM failed: {e}. Using heuristic fallback.")
                result = self._heuristic_faithfulness(answer, context)
        else:
            result = self._heuristic_faithfulness(answer, context)
        
        score = 1.0 if "yes" in result.lower() else 0.0
        self.stats["faithfulness_scores"].append(score)
        return score

    def _heuristic_faithfulness(self, answer: str, context: str) -> float:
        """Fallback heuristic when LLM is unavailable."""
        if any(ref in answer.lower() for ref in ["sorry", "refuse", "authorized", "don't have enough information"]):
            return 1.0 
        return 1.0 if len(context) > 100 else 0.0

    def calculate_retrieval_relevance(self, chunks: list, threshold: float = None) -> dict:
        """
        Calculates relevance metrics based on chunk similarity scores.
        """
        if threshold is None:
            threshold = Config.RETRIEVAL_CONFIDENCE_THRESHOLD
            
        scores = []
        for chunk in chunks:
            if isinstance(chunk, tuple) and len(chunk) > 1:
                scores.append(chunk[1])
            elif hasattr(chunk, 'metadata') and 'score' in chunk.metadata:
                scores.append(chunk.metadata['score'])
            else:
                # Fallback if no scores found (e.g. basic retriever)
                scores.append(1.0)
                
        avg_score = sum(scores) / len(scores) if scores else 0.0
        top_score = scores[0] if scores else 0.0
        
        self.stats["relevance_scores"].append(avg_score)
        
        return {
            "avg_relevance": avg_score,
            "top_score": top_score,
            "below_threshold": top_score < threshold
        }

    def log_event(self, event_type: str = None):
        """Logs security or evaluation events for the summary dashboard."""
        self.stats["total_queries"] += 1
        if event_type:
            self.stats["guardrails_triggered"][event_type] = self.stats["guardrails_triggered"].get(event_type, 0) + 1

    def generate_eval_summary(self) -> str:
        """Prints a summary dashboard of RAG performance and security."""
        avg_faithfulness = sum(self.stats["faithfulness_scores"]) / len(self.stats["faithfulness_scores"]) if self.stats["faithfulness_scores"] else 0
        avg_relevance = sum(self.stats["relevance_scores"]) / len(self.stats["relevance_scores"]) if self.stats["relevance_scores"] else 0
        
        summary = "\n" + "="*50 + "\n"
        summary += "RAG SYSTEM EVALUATION SUMMARY\n"
        summary += "="*50 + "\n"
        summary += f"Total Queries:         {self.stats['total_queries']}\n"
        summary += f"Avg Faithfulness:      {avg_faithfulness:.2f}\n"
        summary += f"Avg Retrieval Score:   {avg_relevance:.2f}\n"
        summary += "-"*50 + "\n"
        summary += "GUARDRAILS TRIGGERED:\n"
        for g_type, count in self.stats["guardrails_triggered"].items():
            summary += f" - {g_type:20}: {count}\n"
        summary += "="*50 + "\n"
        return summary
