import time
import tiktoken

class TokenForgePipeline:
    """
    Orchestrates multiple token optimization stages in series.
    Provides detailed statistics on token/character reduction after each stage.
    """
    def __init__(self, default_tokenizer: str = "cl100k_base"):
        self.stages = []
        self.default_tokenizer = default_tokenizer
        try:
            self.encoder = tiktoken.get_encoding(default_tokenizer)
        except Exception:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def add_stage(self, name: str, optimizer_instance) -> "TokenForgePipeline":
        """Adds an optimization stage to the pipeline."""
        self.stages.append((name, optimizer_instance))
        return self

    def estimate_tokens(self, text: str) -> int:
        """Estimates the token count of a string using tiktoken."""
        if not text:
            return 0
        return len(self.encoder.encode(text, disallowed_special=()))

    def run(self, text: str, **kwargs) -> dict:
        """
        Executes the pipeline of token optimization stages on the input text.
        Returns a dict containing the final optimized text and stage-by-stage metrics.
        """
        start_time = time.time()
        current_text = text
        
        initial_chars = len(text)
        initial_tokens = self.estimate_tokens(text)
        
        metrics = []
        
        for name, optimizer in self.stages:
            stage_start_chars = len(current_text)
            stage_start_tokens = self.estimate_tokens(current_text)
            
            # Run the optimizer
            # Some optimizers may accept custom parameters via kwargs, or we call their optimize() method
            try:
                # Most optimizers will have an .optimize(text) method
                if hasattr(optimizer, "optimize"):
                    optimized_res = optimizer.optimize(current_text, **kwargs)
                else:
                    # Fallback if it's a callable
                    optimized_res = optimizer(current_text)
                
                # Support dictionary return or raw string
                if isinstance(optimized_res, dict):
                    current_text = optimized_res.get("text", current_text)
                    stage_metadata = {k: v for k, v in optimized_res.items() if k != "text"}
                else:
                    current_text = optimized_res
                    stage_metadata = {}
            except Exception as e:
                current_text = current_text
                stage_metadata = {"error": str(e)}
                
            stage_end_chars = len(current_text)
            stage_end_tokens = self.estimate_tokens(current_text)
            
            saved_tokens = stage_start_tokens - stage_end_tokens
            reduction_pct = (saved_tokens / max(1, stage_start_tokens)) * 100
            
            metrics.append({
                "stage": name,
                "input_chars": stage_start_chars,
                "output_chars": stage_end_chars,
                "input_tokens": stage_start_tokens,
                "output_tokens": stage_end_tokens,
                "saved_tokens": saved_tokens,
                "reduction_percentage": round(reduction_pct, 2),
                **stage_metadata
            })
            
        final_chars = len(current_text)
        final_tokens = self.estimate_tokens(current_text)
        total_saved_tokens = initial_tokens - final_tokens
        total_reduction_pct = (total_saved_tokens / max(1, initial_tokens)) * 100
        
        return {
            "original_text": text,
            "optimized_text": current_text,
            "initial_chars": initial_chars,
            "final_chars": final_chars,
            "initial_tokens": initial_tokens,
            "final_tokens": final_tokens,
            "total_saved_tokens": total_saved_tokens,
            "total_reduction_percentage": round(total_reduction_pct, 2),
            "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            "stages_metrics": metrics
        }
