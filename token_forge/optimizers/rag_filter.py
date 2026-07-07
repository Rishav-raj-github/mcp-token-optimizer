class RAGFilter:
    """
    Deduplicates and filters retrieved RAG documents.
    Eliminates chunks that overlap heavily (using Jaccard similarity),
    merges overlapping segments, and filters out low-relevance blocks.
    """
    def __init__(self, similarity_threshold: float = 0.65, min_score: float = 0.4):
        self.similarity_threshold = similarity_threshold
        self.min_score = min_score

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

    def optimize(self, chunks_json_or_list, **kwargs) -> dict:
        """
        Accepts a JSON string representing a list of chunks, or a list of dicts:
        [{"text": "...", "score": 0.8}, ...]
        Returns the optimized, deduplicated list of chunks.
        """
        import json
        
        sim_threshold = kwargs.get("similarity_threshold", self.similarity_threshold)
        min_sc = kwargs.get("min_score", self.min_score)

        if isinstance(chunks_json_or_list, str):
            try:
                chunks = json.loads(chunks_json_or_list)
            except json.JSONDecodeError:
                # Fallback if text is not json, treat as single chunk
                return {"text": chunks_json_or_list, "chunks_saved": 0}
        else:
            chunks = chunks_json_or_list

        if not isinstance(chunks, list):
            return {"text": json.dumps(chunks), "chunks_saved": 0}

        original_count = len(chunks)
        
        # 1. Filter out low score chunks
        filtered_chunks = [c for c in chunks if c.get("score", 1.0) >= min_sc]
        
        # Sort by score descending to keep the highest quality chunks
        filtered_chunks.sort(key=lambda x: x.get("score", 1.0), reverse=True)
        
        # 2. Deduplicate using Jaccard similarity
        unique_chunks = []
        for chunk in filtered_chunks:
            text = chunk.get("text", "")
            if not text:
                continue
                
            # Check if this text is a subset of any already accepted chunk
            # or shares too much similarity
            is_redundant = False
            for accepted in unique_chunks:
                accepted_text = accepted.get("text", "")
                
                # Check subset
                if text in accepted_text:
                    is_redundant = True
                    break
                    
                # Check similarity
                sim = self._jaccard_similarity(text, accepted_text)
                if sim > sim_threshold:
                    is_redundant = True
                    break
                    
            if not is_redundant:
                unique_chunks.append(chunk)

        chunks_saved = original_count - len(unique_chunks)
        
        # Final output format: either JSON array or a concatenated text block
        result_text = "\n\n".join([c.get("text", "") for c in unique_chunks])
        
        return {
            "text": result_text,
            "original_chunks_count": original_count,
            "final_chunks_count": len(unique_chunks),
            "chunks_saved": chunks_saved,
            "chunks_list": unique_chunks
        }
