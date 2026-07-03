import re
import math
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Token-Optimizer")

@mcp.tool()
def prune_context(text: str, focus_keywords: str = "", max_chars: int = 4000) -> str:
    """
    Prunes verbose logs, stack traces, or document content to minimize token usage.
    Strips redundant timestamps, boilerplate headers, duplicate lines, and preserves focus areas.
    """
    if not text:
        return ""
        
    lines = text.split("\n")
    unique_lines = []
    seen = set()
    
    # 1. Remove exact duplicate lines to save tokens
    for line in lines:
        cleaned = line.strip()
        if cleaned not in seen:
            seen.add(cleaned)
            unique_lines.append(line)
            
    # 2. Filter lines using simple regex rules (e.g., standard timestamp-heavy log headers)
    # Replaces long timestamps like "2026-07-03T17:28:46.123456+05:30 [INFO] ..." with "[INFO] ..."
    processed_lines = []
    timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)?\s*')
    
    for line in unique_lines:
        line_clean = timestamp_pattern.sub("", line)
        processed_lines.append(line_clean)
        
    # 3. Focus keyword prioritization: if focus keywords are given, select lines containing them
    if focus_keywords:
        keywords = [kw.strip().lower() for kw in focus_keywords.split(",") if kw.strip()]
        prioritized = []
        context_window = 1  # lines of context around matches
        
        for i, line in enumerate(processed_lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                # Grab context lines
                start = max(0, i - context_window)
                end = min(len(processed_lines), i + context_window + 1)
                for idx in range(start, end):
                    if processed_lines[idx] not in prioritized:
                        prioritized.append(processed_lines[idx])
        result = "\n".join(prioritized)
    else:
        # Default behavior: rank lines by length and preserve structure (head/tail logic for logs)
        if len(processed_lines) > 50:
            head = processed_lines[:20]
            tail = processed_lines[-20:]
            result = "\n".join(head) + "\n\n... [TRUNCATED REDUNDANT MIDDLE LOGS TO SAVE TOKENS] ...\n\n" + "\n".join(tail)
        else:
            result = "\n".join(processed_lines)
            
    # Enforce hard length limit
    if len(result) > max_chars:
        result = result[:max_chars] + "\n... [TRUNCATED DUE TO SIZE LIMIT] ..."
        
    return result

@mcp.tool()
def align_prompt_cache(text: str, target_block_tokens: int = 1024, chars_per_token: float = 4.0) -> dict:
    """
    Pads or slices context strings to align them exactly to LLM prompt cache block boundaries (typically 1024 tokens).
    Prevents cache invalidation by ensuring prefix token count remains static across dynamic queries.
    """
    if not text:
        return {"aligned_text": "", "original_tokens": 0, "padded_tokens": 0, "padding_chars_added": 0}
        
    # Estimate current token count
    char_len = len(text)
    estimated_tokens = max(1, int(char_len / chars_per_token))
    
    # Calculate next block boundary
    blocks_needed = math.ceil(estimated_tokens / target_block_tokens)
    target_tokens = blocks_needed * target_block_tokens
    
    tokens_to_pad = target_tokens - estimated_tokens
    chars_to_pad = int(tokens_to_pad * chars_per_token)
    
    # Pad using safe comment/whitespace spacing
    padding = "\n" + " " * (chars_to_pad - 1)
    aligned_text = text + padding
    
    return {
        "aligned_text": aligned_text,
        "original_estimated_tokens": estimated_tokens,
        "aligned_estimated_tokens": target_tokens,
        "padding_chars_added": chars_to_pad
    }

if __name__ == "__main__":
    mcp.run()
