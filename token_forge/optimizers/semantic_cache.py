class SemanticCache:
    """
    Stores previous queries and their responses.
    Uses TF-IDF/Jaccard similarity to determine if a incoming query is a semantic match.
    If yes, returns the cached response, saving 100% of tokens.
    """
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.cache = []  # list of dicts: {"query": "...", "response": "..."}

    def _get_words(self, text: str) -> set:
        import re
        return set(re.findall(r'\b\w+\b', text.lower()))

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        words1 = self._get_words(text1)
        words2 = self._get_words(text2)
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    def set(self, query: str, response: str):
        """Caches a query-response pair."""
        if not query or not response:
            return
        # Avoid caching duplicate queries
        for item in self.cache:
            if item["query"] == query:
                item["response"] = response
                return
        self.cache.append({"query": query, "response": response})

    def get(self, query: str, **kwargs) -> dict:
        """
        Checks the cache for a semantic hit.
        Returns a dict indicating if it was a hit and the cached response.
        """
        if not query:
            return {"hit": False, "response": None}

        thresh = kwargs.get("threshold", self.threshold)
        
        best_match = None
        best_score = -1.0
        
        for item in self.cache:
            score = self._jaccard_similarity(query, item["query"])
            if score > best_score:
                best_score = score
                best_match = item
                
        if best_score >= thresh and best_match:
            return {
                "hit": True,
                "response": best_match["response"],
                "similarity_score": round(best_score, 3),
                "saved_tokens_percentage": 100.0
            }
            
        return {
            "hit": False,
            "response": None,
            "best_score": round(best_score, 3) if best_score > 0 else 0.0
        }

    def optimize(self, text: str, **kwargs) -> dict:
        # Interface compatibility with the pipeline
        # (Usually, a cache acts as a bypass, but we return its status here)
        res = self.get(text, **kwargs)
        if res["hit"]:
            return {
                "text": res["response"],
                "cached": True,
                "similarity_score": res["similarity_score"]
            }
        return {
            "text": text,
            "cached": False
        }
