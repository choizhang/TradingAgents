import chromadb
from chromadb.config import Settings
from openai import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import httpx


class FinancialSituationMemory:
    def __init__(self, name, config):
        self.config = config
        self.llm_provider = config.get("llm_provider", "openai").lower()
        self.backend_url = config.get("backend_url")
        self.proxies = config.get("proxies")
        self.llm_timeout = config.get("llm_timeout")

        if self.llm_provider == "google":
            self.embedding_model = "gemini-embedding-exp-03-07"
            # For Google embeddings, we use the direct google.generativeai client
            import google.generativeai as genai
            genai.configure(api_key=self.config.get("google_api_key"))
            # If proxies are set, rely on environment variables for genai to pick them up
            # as genai client doesn't directly take httpx.Client or proxies parameter.
            self.client = genai # Assign the genai module as the client
            self.get_embedding_func = self._get_google_embedding
        else: # Default to OpenAI or other compatible
            if self.backend_url == "http://localhost:11434/v1":
                self.embedding_model = "nomic-embed-text"
            else:
                self.embedding_model = "text-embedding-3-small"
            
            if self.proxies:
                self.client = OpenAI(base_url=self.backend_url, http_client=httpx.Client(proxies=self.proxies))
            else:
                self.client = OpenAI(base_url=self.backend_url)
            self.get_embedding_func = self._get_openai_embedding
            
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.situation_collection = self.chroma_client.create_collection(name=name)

    def _get_openai_embedding(self, text):
        """Get OpenAI embedding for a text"""
        response = self.client.embeddings.create(
            model=self.embedding_model, input=text
        )
        return response.data[0].embedding

    def _get_google_embedding(self, text):
        """Get Google embedding for a text"""
        # Use google.generativeai.embed_content directly
        response = self.client.embed_content(
            model=self.embedding_model,
            content=text,
            task_type="RETRIEVAL_DOCUMENT"
        )
        return response['embedding']

    def get_embedding(self, text):
        """Get embedding for a text using the selected client"""
        return self.get_embedding_func(text)

    def add_situations(self, situations_and_advice):
        """Add financial situations and their corresponding advice. Parameter is a list of tuples (situation, rec)"""

        situations = []
        advice = []
        ids = []
        embeddings = []

        offset = self.situation_collection.count()

        for i, (situation, recommendation) in enumerate(situations_and_advice):
            situations.append(situation)
            advice.append(recommendation)
            ids.append(str(offset + i))
            embeddings.append(self.get_embedding(situation))

        self.situation_collection.add(
            documents=situations,
            metadatas=[{"recommendation": rec} for rec in advice],
            embeddings=embeddings,
            ids=ids,
        )

    def get_memories(self, current_situation, n_matches=1):
        """Find matching recommendations using OpenAI embeddings"""
        query_embedding = self.get_embedding(current_situation)

        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )

        matched_results = []
        for i in range(len(results["documents"][0])):
            matched_results.append(
                {
                    "matched_situation": results["documents"][0][i],
                    "recommendation": results["metadatas"][0][i]["recommendation"],
                    "similarity_score": 1 - results["distances"][0][i],
                }
            )

        return matched_results


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory()

    # Example data
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # Add the example situations and recommendations
    matcher.add_situations(example_data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")
