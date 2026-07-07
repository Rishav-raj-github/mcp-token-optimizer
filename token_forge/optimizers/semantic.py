import re
import math
from collections import Counter

class SemanticCompressor:
    """
    A lightweight semantic compressor (LLMLingua-lite) that ranks sentences/lines
    by information density and trims low-importance segments to meet a token budget.
    """
    def __init__(self, target_ratio: float = 0.6):
        self.target_ratio = target_ratio  # Default to keep 60% of information

    def _tokenize_words(self, text: str) -> list:
        # Standard cleaning
        words = re.findall(r'\b\w+\b', text.lower())
        return words

    def optimize(self, text: str, **kwargs) -> dict:
        if not text:
            return {"text": "", "ratio": 0.0}

        ratio = kwargs.get("target_ratio", self.target_ratio)
        if ratio >= 1.0:
            return {"text": text, "ratio": 1.0, "compressed": False}

        # Split by sentence-like structures (dot, question mark, exclamation, or newlines)
        # We want to preserve paragraphs if possible, so let's split by lines first, then sentences.
        lines = text.split("\n")
        
        # Build global word frequencies to evaluate rarity (TF-IDF equivalent)
        all_words = self._tokenize_words(text)
        word_counts = Counter(all_words)
        total_words = len(all_words)
        
        if total_words == 0:
            return {"text": text, "ratio": 1.0}

        # Calculate word "rarity" or information score. Rare words have higher score.
        # score = log(total_words / count)
        word_scores = {}
        for word, count in word_counts.items():
            word_scores[word] = math.log(total_words / count) + 0.1

        # We will rank units. A unit is a line or a sentence.
        # Let's split each line into sentences to score them, or score line by line.
        # Let's score line by line to keep formatting intact.
        scored_lines = []
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                scored_lines.append((index, line, 0.0))  # Blank line, low score but we might keep it
                continue
            
            line_words = self._tokenize_words(stripped)
            if not line_words:
                scored_lines.append((index, line, 0.0))
                continue
                
            # Score is the average word score of words in the line
            # Rare words drag the score up; common words keep it normal.
            # We add a length penalty so extremely short lines aren't favored.
            total_score = sum(word_scores.get(w, 0.0) for w in line_words)
            avg_score = total_score / len(line_words)
            
            # Boost lines that contain punctuation indicative of structured content (like colons, brackets)
            boost = 1.0
            if ":" in stripped: boost += 0.2
            if "class " in stripped or "def " in stripped: boost += 0.3
            
            scored_lines.append((index, line, avg_score * boost))

        # Filter out empty lines from sorting, but keep their indices
        non_empty_scored = [item for item in scored_lines if item[1].strip()]
        
        # Sort non-empty lines by score descending
        non_empty_scored.sort(key=lambda x: x[2], reverse=True)
        
        # Calculate how many lines we want to keep
        num_to_keep = max(1, int(len(non_empty_scored) * ratio))
        keep_items = non_empty_scored[:num_to_keep]
        
        # Get the set of indices to keep
        keep_indices = {item[0] for item in keep_items}
        
        # Reconstruct the text keeping original order
        final_lines = []
        for index, line, _ in scored_lines:
            if index in keep_indices:
                final_lines.append(line)
            elif not line.strip():
                # Keep original blank lines to preserve spacing if adjacent to kept lines
                final_lines.append("")
                
        # Clean consecutive empty lines
        cleaned_final_lines = []
        last_was_empty = False
        for line in final_lines:
            if not line.strip():
                if not last_was_empty:
                    cleaned_final_lines.append("")
                    last_was_empty = True
            else:
                cleaned_final_lines.append(line)
                last_was_empty = False

        compressed_text = "\n".join(cleaned_final_lines).strip()
        
        # Calculate actual savings
        orig_chars = len(text)
        comp_chars = len(compressed_text)
        saved_chars = orig_chars - comp_chars
        reduction_pct = (saved_chars / max(1, orig_chars)) * 100
        
        return {
            "text": compressed_text,
            "original_chars": orig_chars,
            "compressed_chars": comp_chars,
            "chars_saved": saved_chars,
            "savings_percentage": round(reduction_pct, 2)
        }
