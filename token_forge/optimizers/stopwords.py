import re

class StopwordStripper:
    """
    Strips non-essential grammatical filler words (articles, determiners, simple prepositions, auxiliary verbs)
    while maintaining overall text coherence. LLMs are highly capable of understanding "telegraphic" text.
    """
    def __init__(self):
        # A list of non-essential filler words that can be safely removed from large prompts
        self.fillers = {
            "a", "an", "the", "indeed", "hereby", "furthermore", "nonetheless",
            "moreover", "whilst", "therefore", "thus", "hence", "namely"
        }

    def optimize(self, text: str, **kwargs) -> dict:
        if not text:
            return {"text": "", "savings_percentage": 0.0}

        aggressive = kwargs.get("aggressive", False)
        
        # If aggressive is enabled, we remove a wider list of auxiliary verbs and prepositions
        fill_list = self.fillers.copy()
        if aggressive:
            additional_fillers = {
                "is", "are", "was", "were", "been", "being", "have", "has", "had",
                "do", "does", "did", "of", "to", "in", "for", "with", "on", "at", "by", "from"
            }
            fill_list.update(additional_fillers)

        # Split text into words while keeping punctuation
        tokens = re.split(r'(\s+|\b)', text)
        
        cleaned_tokens = []
        words_removed = 0
        
        for tok in tokens:
            stripped = tok.strip()
            # If the token is a word and in our filler list, skip it
            if stripped.lower() in fill_list:
                words_removed += 1
                # If there's an adjacent space, we don't write it
                continue
            cleaned_tokens.append(tok)

        # Join tokens and normalize spaces
        cleaned_text = "".join(cleaned_tokens)
        cleaned_text = re.sub(r' +', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n +', '\n', cleaned_text)
        cleaned_text = cleaned_text.replace(" \n", "\n").strip()

        orig_len = len(text)
        new_len = len(cleaned_text)
        saved = orig_len - new_len
        
        return {
            "text": cleaned_text,
            "words_removed": words_removed,
            "original_chars": orig_len,
            "cleaned_chars": new_len,
            "savings_percentage": round((saved / max(1, orig_len)) * 100, 2)
        }
