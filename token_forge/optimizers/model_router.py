class ModelRouter:
    """
    Intelligently routes incoming queries to the optimal LLM based on task complexity.
    Routes simple tasks (classification, greetings, basic data extraction) to cheap, fast models,
    and reserves expensive flagship models for complex tasks (refactoring, mathematical proofs, logic reasoning).
    """
    def __init__(self):
        # Keywords indicating complex reasoning tasks
        self.complex_indicators = {
            "optimize", "refactor", "debug", "architect", "explain the difference",
            "mathematical", "proof", "derivation", "write code", "implement", "design",
            "concurrency", "deadlock", "race condition", "algorithm", "complex"
        }

    def route(self, query: str) -> dict:
        if not query:
            return {"recommended_tier": "cheap", "reason": "Empty query", "model_suggestions": ["gpt-4o-mini", "gemini-1.5-flash", "claude-3-haiku"]}

        query_lower = query.lower()
        
        # 1. Analyze length
        word_count = len(query_lower.split())
        
        # 2. Check for complex indicators
        hits = [kw for kw in self.complex_indicators if kw in query_lower]
        
        # 3. Simple scoring model
        complexity_score = len(hits) * 2.0
        if word_count > 150:
            complexity_score += 1.5  # long prompts suggest higher complexity
            
        # If code blocks or JSON formatting is requested
        if "```" in query:
            complexity_score += 3.0
        if "json" in query_lower or "xml" in query_lower:
            complexity_score += 1.0

        if complexity_score >= 4.0:
            tier = "flagship"
            reason = f"Detected complex instructions / patterns (complexity score {complexity_score}): {', '.join(hits)}"
            suggestions = ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro"]
        else:
            tier = "cheap"
            reason = f"Simple conversational or direct lookup task (complexity score {complexity_score})"
            suggestions = ["gemini-1.5-flash", "gpt-4o-mini", "claude-3-haiku"]

        return {
            "query": query,
            "complexity_score": complexity_score,
            "recommended_tier": tier,
            "reason": reason,
            "model_suggestions": suggestions
        }

    def optimize(self, text: str, **kwargs) -> dict:
        # Compatibility wrapper
        res = self.route(text)
        return {
            "text": text,
            "recommended_tier": res["recommended_tier"],
            "model_suggestions": res["model_suggestions"],
            "routing_reason": res["reason"]
        }
