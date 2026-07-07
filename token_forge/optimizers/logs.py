import re

class LogCondenser:
    """
    Condenses verbose logs and stack traces.
    Strips redundant timestamps, hexadecimal memory addresses, repetitive log headers,
    deduplicates identical lines, and keeps only the top/bottom context for large logs.
    """
    def __init__(self, max_head_lines: int = 25, max_tail_lines: int = 25):
        self.max_head_lines = max_head_lines
        self.max_tail_lines = max_tail_lines

    def optimize(self, text: str, **kwargs) -> dict:
        if not text:
            return {"text": ""}

        head_limit = kwargs.get("max_head_lines", self.max_head_lines)
        tail_limit = kwargs.get("max_tail_lines", self.max_tail_lines)
        
        lines = text.split("\n")
        
        # 1. Remove duplicate adjacent lines (common in error loops)
        deduplicated = []
        last_line = None
        dup_count = 0
        for line in lines:
            cleaned = line.strip()
            if cleaned == last_line:
                dup_count += 1
                continue
            else:
                if dup_count > 0:
                    deduplicated.append(f"... [repeated {dup_count} times] ...")
                    dup_count = 0
                deduplicated.append(line)
                last_line = cleaned
        if dup_count > 0:
            deduplicated.append(f"... [repeated {dup_count} times] ...")

        # 2. Regular expressions to replace long timestamps and memory addresses
        # ISO-8601, RFC 3339 timestamps (e.g., 2026-07-07T21:11:35.123Z)
        timestamp_regex = re.compile(
            r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)?\b'
        )
        # Standard server log timestamps (e.g., [Jul 07 21:11:35], 07/07/26 21:11:35)
        syslog_regex = re.compile(
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b'
        )
        # Hexadecimal memory addresses (e.g., 0x7ffd2a10b3df)
        hex_regex = re.compile(r'\b0x[0-9a-fA-F]{8,16}\b')
        
        condensed_lines = []
        for line in deduplicated:
            # Replace timestamps with compact token
            line = timestamp_regex.sub("[TS]", line)
            line = syslog_regex.sub("[TS]", line)
            # Replace hex addresses
            line = hex_regex.sub("[HEX]", line)
            condensed_lines.append(line)

        # 3. Head & Tail logic: if log file is huge, keep beginning and end, collapse the middle
        total_lines = len(condensed_lines)
        if total_lines > (head_limit + tail_limit + 5):
            head = condensed_lines[:head_limit]
            tail = condensed_lines[-tail_limit:]
            middle_summary = [
                "",
                f"... [TRUNCATED {total_lines - head_limit - tail_limit} REDUNDANT LOG LINES TO SAVE TOKENS] ...",
                ""
            ]
            result_lines = head + middle_summary + tail
        else:
            result_lines = condensed_lines

        condensed_text = "\n".join(result_lines).strip()
        
        orig_len = len(text)
        cond_len = len(condensed_text)
        saved = orig_len - cond_len
        
        return {
            "text": condensed_text,
            "original_lines": len(lines),
            "condensed_lines": len(result_lines),
            "original_chars": orig_len,
            "condensed_chars": cond_len,
            "reduction_percentage": round((saved / max(1, orig_len)) * 100, 2)
        }
