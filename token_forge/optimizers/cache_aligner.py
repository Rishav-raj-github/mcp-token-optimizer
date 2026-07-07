import math
import tiktoken

class CacheAligner:
    """
    Pads a context string with comments to align it exactly with 1024-token cache boundaries.
    Prevents cache invalidation by keeping the prefix token counts identical across dynamic queries.
    Uses character-efficient '. ' sequences within comments to achieve exact token counts.
    """
    def __init__(self, target_block_tokens: int = 1024, format_style: str = "markdown", tokenizer_name: str = "cl100k_base"):
        self.target_block_tokens = target_block_tokens
        self.format_style = format_style
        try:
            self.encoder = tiktoken.get_encoding(tokenizer_name)
        except Exception:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def estimate_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text, disallowed_special=()))

    def optimize(self, text: str, **kwargs) -> dict:
        if not text:
            return {
                "text": "",
                "original_tokens": 0,
                "aligned_tokens": 0,
                "padding_tokens": 0,
                "padding_chars_added": 0
            }

        style = kwargs.get("format_style", self.format_style)
        block_size = kwargs.get("target_block_tokens", self.target_block_tokens)
        
        current_tokens = self.estimate_tokens(text)
        
        # Determine next multiple of block_size
        blocks_needed = math.ceil(current_tokens / block_size)
        target_tokens = blocks_needed * block_size
        
        # If we are already aligned, do nothing
        if current_tokens == target_tokens:
            return {
                "text": text,
                "original_tokens": current_tokens,
                "aligned_tokens": current_tokens,
                "padding_tokens": 0,
                "padding_chars_added": 0
            }
            
        # Target to pad:
        padding_tokens_needed = target_tokens - current_tokens
        
        # Define wrapper prefix and suffix based on format style
        if style == "markdown":
            prefix = "\n<!-- CACHE_PAD "
            suffix = "-->"
        elif style in ["python", "yaml", "ini"]:
            prefix = "\n# CACHE_PAD "
            suffix = ""
        elif style in ["js", "javascript", "ts", "json", "c", "cpp"]:
            prefix = "\n// CACHE_PAD "
            suffix = ""
        else:
            prefix = "\n"
            suffix = ""

        # Measure how many tokens the wrapper itself takes
        wrapper_text = prefix + suffix
        wrapper_tokens = self.estimate_tokens(text + wrapper_text) - current_tokens
        
        # If the wrapper itself pushes us past target_tokens, we must align to the next block
        if wrapper_tokens >= padding_tokens_needed:
            target_tokens += block_size
            padding_tokens_needed = target_tokens - current_tokens
            
        # Number of dot-space elements to fill inside the wrapper
        fill_tokens_needed = padding_tokens_needed - wrapper_tokens
        
        # Iteratively construct and calibrate to hit the exact token target
        # (Usually fill_tokens_needed repeats of ". " is exactly fill_tokens_needed tokens)
        best_repeat = max(0, fill_tokens_needed)
        
        # Calibrate with a small adjustment loop to ensure exact token boundary
        for _ in range(5):
            pad_fill = ". " * best_repeat
            candidate_text = text + prefix + pad_fill + suffix
            cand_tokens = self.estimate_tokens(candidate_text)
            
            diff = target_tokens - cand_tokens
            if diff == 0:
                break
            elif diff > 0:
                best_repeat += diff  # Add more tokens
            else:
                best_repeat += diff  # Reduce tokens (diff is negative)

        final_pad = prefix + (". " * best_repeat) + suffix
        aligned_text = text + final_pad
        final_tokens = self.estimate_tokens(aligned_text)
        
        return {
            "text": aligned_text,
            "original_tokens": current_tokens,
            "aligned_tokens": final_tokens,
            "padding_tokens": final_tokens - current_tokens,
            "padding_chars_added": len(final_pad)
        }
