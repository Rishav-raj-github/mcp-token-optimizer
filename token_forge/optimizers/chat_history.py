import json

class ChatHistorySummarizer:
    """
    Manages sliding window dialogue history and older message summarization.
    Keeps the most recent N turns fully intact to maintain local conversational context,
    while condensing/rolling up older turns to avoid context-length inflation.
    """
    def __init__(self, keep_turns: int = 4, max_tokens: int = 4000):
        self.keep_turns = keep_turns
        self.max_tokens = max_tokens

    def optimize(self, messages_json_or_list, **kwargs) -> dict:
        """
        Accepts either a JSON string of messages or a python list of dicts.
        Returns optimized list of messages and summaries.
        """
        keep_n = kwargs.get("keep_turns", self.keep_turns)
        
        # Parse if json
        if isinstance(messages_json_or_list, str):
            try:
                messages = json.loads(messages_json_or_list)
            except json.JSONDecodeError:
                # Fallback if text is not json
                return {"text": messages_json_or_list, "ratio": 1.0}
        else:
            messages = messages_json_or_list

        if not isinstance(messages, list) or len(messages) == 0:
            return {"text": json.dumps(messages), "original_turns": 0, "final_turns": 0}

        orig_turns = len(messages)
        
        # If message history is shorter than sliding window, keep it all
        if len(messages) <= keep_n:
            return {
                "text": json.dumps(messages),
                "original_turns": orig_turns,
                "final_turns": orig_turns,
                "summarized": False
            }

        # Divide into old messages and recent messages
        recent_messages = messages[-keep_n:]
        old_messages = messages[:-keep_n]
        
        # Create a compressed summary of older messages.
        # In a real app, this calls an LLM. Here, we simulate a smart semantic summary:
        # We extract user intents and brief agent actions from the old messages.
        summary_bullets = []
        for i, msg in enumerate(old_messages):
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            
            # Simple summarization: grab first line or sentence
            clean_content = content.replace("\n", " ").strip()
            first_sentence = clean_content.split(". ")[0]
            if len(first_sentence) > 80:
                first_sentence = first_sentence[:80] + "..."
            
            # Append turn summaries
            summary_bullets.append(f"{role}: {first_sentence}")

        summary_text = (
            "--- [System Rolled-up History Summary] ---\n"
            + "\n".join(summary_bullets)
            + "\n-----------------------------------------"
        )
        
        # Construct the final message list
        rolled_message = {
            "role": "system",
            "content": f"Summary of previous discussion:\n{summary_text}"
        }
        
        optimized_messages = [rolled_message] + recent_messages
        
        return {
            "text": json.dumps(optimized_messages),
            "original_turns": orig_turns,
            "final_turns": len(optimized_messages),
            "summarized": True,
            "summary_chars": len(summary_text)
        }
