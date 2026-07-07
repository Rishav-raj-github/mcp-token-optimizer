import re

class SystemPromptMinifier:
    """
    Minifies large static system prompts based on context relevance.
    Supports tagged optional blocks like `<optional trigger="chart,plot">...</optional>`
    which are dynamically removed unless the user query triggers the keywords.
    """
    def __init__(self):
        pass

    def optimize(self, system_prompt: str, query: str = "", **kwargs) -> dict:
        if not system_prompt:
            return {"text": "", "savings_percentage": 0.0}

        if not query:
            # Strip comments/whitespace but keep all structural content
            minified = self._strip_prompt_boilerplate(system_prompt)
            return {
                "text": minified,
                "original_chars": len(system_prompt),
                "minified_chars": len(minified),
                "savings_percentage": round(((len(system_prompt) - len(minified)) / max(1, len(system_prompt))) * 100, 2)
            }

        query_lower = query.lower()
        
        # 1. Parse tag patterns like: <optional trigger="chart,graph,plot">...</optional>
        # If none of the trigger words are in the query, strip the block entirely.
        # Otherwise, strip only the tags but keep the content.
        
        pattern = re.compile(r'<optional\s+trigger="([^"]+)"\s*>(.*?)</optional>', re.DOTALL)
        
        def replace_optional(match):
            triggers_str = match.group(1)
            content = match.group(2)
            
            triggers = [t.strip().lower() for t in triggers_str.split(",") if t.strip()]
            
            # Check if any trigger word is in user query
            if any(trigger in query_lower for trigger in triggers):
                # Keep content, remove outer tags
                return content
            else:
                # Remove entire block
                return ""

        minified = pattern.sub(replace_optional, system_prompt)
        
        # 2. Strip comments and double lines
        minified = self._strip_prompt_boilerplate(minified)
        
        orig_len = len(system_prompt)
        min_len = len(minified)
        saved = orig_len - min_len
        
        return {
            "text": minified,
            "original_chars": orig_len,
            "minified_chars": min_len,
            "savings_percentage": round((saved / max(1, orig_len)) * 100, 2)
        }

    def _strip_prompt_boilerplate(self, prompt: str) -> str:
        # Strip system prompt developer comments (lines starting with # or // inside instruction prompts)
        lines = prompt.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("//") or stripped.startswith("# COMMENT:"):
                continue
            cleaned_lines.append(line)
            
        result = "\n".join(cleaned_lines)
        # Collapse multiple empty lines
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()
