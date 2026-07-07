import re

class XMLMinifier:
    """
    Condenses structural XML/HTML blocks (frequently used in Claude prompts).
    Shortens verbose tags (e.g., <document> to <doc>), removes redundant tag attributes,
    and strips whitespaces between adjacent tags.
    """
    def __init__(self):
        # Maps common long tag names to short ones
        self.tag_mapping = {
            "documents": "docs",
            "document": "doc",
            "search_results": "results",
            "search_result": "result",
            "conversation_history": "chat",
            "message": "msg",
            "instruction": "inst",
            "context": "ctx",
            "explanation": "expl",
            "thought_process": "thought"
        }

    def optimize(self, text: str, **kwargs) -> dict:
        if not text:
            return {"text": "", "savings_percentage": 0.0}

        mapping = kwargs.get("tag_mapping", self.tag_mapping)
        
        compressed = text
        
        # 1. Shorten tags using regex
        for long_tag, short_tag in mapping.items():
            # Opening tags (handles attributes: <tag attr="val">)
            compressed = re.sub(
                rf'<{long_tag}(\s+[^>]*?)?>',
                lambda m: f'<{short_tag}{m.group(1) if m.group(1) else ""}>',
                compressed
            )
            # Closing tags
            compressed = re.sub(rf'</{long_tag}>', f'</{short_tag}>', compressed)

        # 2. Strip unnecessary spaces between closing and opening tags
        # e.g., </doc>   <doc> -> </doc><doc>
        compressed = re.sub(r'>\s+<', '><', compressed)
        
        # 3. Strip redundant attributes that do not help semantic reasoning
        # (e.g., namespace attributes xmlns="...")
        compressed = re.sub(r'\s+xmlns(:\w+)?="[^"]*"', '', compressed)

        orig_len = len(text)
        comp_len = len(compressed)
        saved = orig_len - comp_len
        
        return {
            "text": compressed,
            "original_chars": orig_len,
            "minified_chars": comp_len,
            "savings_percentage": round((saved / max(1, orig_len)) * 100, 2)
        }
