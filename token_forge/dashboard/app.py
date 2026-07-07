import os
import uvicorn
import tiktoken
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Setup FastAPI App
app = FastAPI(title="TokenForge Dashboard", description="Real-time LLM Token Optimization Simulator")

# Configure templates path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Import optimizers
try:
    from token_forge.optimizers.cache_aligner import CacheAligner
    from token_forge.optimizers.semantic import SemanticCompressor
    from token_forge.optimizers.code_ast import CodeASTMinifier
    from token_forge.optimizers.logs import LogCondenser
    from token_forge.optimizers.data_format import DataMinifier
    from token_forge.optimizers.chat_history import ChatHistorySummarizer
    from token_forge.optimizers.stopwords import StopwordStripper
    from token_forge.optimizers.rag_filter import RAGFilter
    from token_forge.optimizers.xml_minifier import XMLMinifier
    from token_forge.optimizers.semantic_cache import SemanticCache
    from token_forge.optimizers.model_router import ModelRouter
    from token_forge.optimizers.tool_pruner import ToolPruner
    from token_forge.optimizers.system_prompt import SystemPromptMinifier
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(BASE_DIR)))
    from token_forge.optimizers.cache_aligner import CacheAligner
    from token_forge.optimizers.semantic import SemanticCompressor
    from token_forge.optimizers.code_ast import CodeASTMinifier
    from token_forge.optimizers.logs import LogCondenser
    from token_forge.optimizers.data_format import DataMinifier
    from token_forge.optimizers.chat_history import ChatHistorySummarizer
    from token_forge.optimizers.stopwords import StopwordStripper
    from token_forge.optimizers.rag_filter import RAGFilter
    from token_forge.optimizers.xml_minifier import XMLMinifier
    from token_forge.optimizers.semantic_cache import SemanticCache
    from token_forge.optimizers.model_router import ModelRouter
    from token_forge.optimizers.tool_pruner import ToolPruner
    from token_forge.optimizers.system_prompt import SystemPromptMinifier

# Instantiate optimizers
aligner = CacheAligner()
semantic_compressor = SemanticCompressor()
ast_minifier = CodeASTMinifier()
log_condenser = LogCondenser()
data_minifier = DataMinifier()
history_summarizer = ChatHistorySummarizer()
stopword_stripper = StopwordStripper()
rag_filter = RAGFilter()
xml_minifier = XMLMinifier()
s_cache = SemanticCache()
m_router = ModelRouter()
t_pruner = ToolPruner()
sys_minifier = SystemPromptMinifier()

# Initialize some mock cache items for demonstration
s_cache.set("What are the system requirements for installation?", "The system requirements are Python 3.10+ and a minimum of 4GB RAM.")
s_cache.set("How do I configure the model context protocol server?", "To configure the MCP server, add it to your claude_desktop_config.json with command python and path to mcp_server.py.")

# Encoder mappings for token comparison
encoders = {
    "GPT-4 / Claude (cl100k_base)": tiktoken.get_encoding("cl100k_base"),
    "GPT-4o / o1 (o200k_base)": tiktoken.get_encoding("o200k_base"),
    "Llama 3 (Approximate)": tiktoken.get_encoding("cl100k_base")  # Llama 3 has a larger vocab, cl100k is a good surrogate for mock comparison
}

def estimate_all_tokens(text: str) -> dict:
    if not text:
        return {k: 0 for k in encoders.keys()}
    
    results = {}
    for name, encoder in encoders.items():
        try:
            results[name] = len(encoder.encode(text, disallowed_special=()))
        except Exception:
            results[name] = len(text) // 4
    return results

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/optimize")
async def optimize_endpoint(payload: dict):
    text = payload.get("text", "")
    optimizer_type = payload.get("optimizer", "logs")
    config = payload.get("config", {})

    if not text:
        return JSONResponse(status_code=400, content={"error": "Text payload is empty"})

    result = {}
    
    # Select and run optimizer
    if optimizer_type == "logs":
        head = int(config.get("max_head_lines", 25))
        tail = int(config.get("max_tail_lines", 25))
        result = log_condenser.optimize(text, max_head_lines=head, max_tail_lines=tail)
        
    elif optimizer_type == "semantic":
        ratio = float(config.get("target_ratio", 0.6))
        result = semantic_compressor.optimize(text, target_ratio=ratio)
        
    elif optimizer_type == "cache_align":
        fmt = config.get("format_style", "markdown")
        block = int(config.get("target_block_tokens", 1024))
        result = aligner.optimize(text, format_style=fmt, target_block_tokens=block)
        
    elif optimizer_type == "code_ast":
        lang = config.get("language", "python")
        keep_docs = bool(config.get("keep_docstrings", True))
        result = ast_minifier.optimize(text, language=lang, keep_docstrings=keep_docs)
        
    elif optimizer_type == "data":
        fmt = config.get("target_format", "csv_or_kv")
        result = data_minifier.optimize(text, target_format=fmt)
        
    elif optimizer_type == "chat_history":
        turns = int(config.get("keep_turns", 4))
        result = history_summarizer.optimize(text, keep_turns=turns)
        
    elif optimizer_type == "stopwords":
        agg = bool(config.get("aggressive", False))
        result = stopword_stripper.optimize(text, aggressive=agg)
        
    elif optimizer_type == "rag":
        thresh = float(config.get("similarity_threshold", 0.65))
        min_sc = float(config.get("min_score", 0.4))
        result = rag_filter.optimize(text, similarity_threshold=thresh, min_score=min_sc)
        
    elif optimizer_type == "xml":
        result = xml_minifier.optimize(text)
        
    elif optimizer_type == "semantic_cache":
        # First query cache
        thresh = float(config.get("threshold", 0.85))
        result = s_cache.optimize(text, threshold=thresh)
        
    elif optimizer_type == "model_router":
        result = m_router.optimize(text)
        
    elif optimizer_type == "tool_pruner":
        query = config.get("query", "")
        # Mandatory tools
        mand = [t.strip() for t in config.get("mandatory_tools", "").split(",") if t.strip()]
        result = t_pruner.optimize(text, query=query, mandatory_tools=mand)
        
    elif optimizer_type == "system_prompt":
        query = config.get("query", "")
        result = sys_minifier.optimize(text, query=query)
        
    else:
        return JSONResponse(status_code=400, content={"error": f"Unknown optimizer: {optimizer_type}"})

    # Estimate tokens before and after across all encoders
    original_text = text
    optimized_text = result.get("text", text)
    
    orig_tokens = estimate_all_tokens(original_text)
    opt_tokens = estimate_all_tokens(optimized_text)
    
    savings = {}
    for k in orig_tokens.keys():
        before = orig_tokens[k]
        after = opt_tokens[k]
        diff = before - after
        pct = (diff / max(1, before)) * 100
        savings[k] = {
            "before": before,
            "after": after,
            "saved": diff,
            "percentage": round(pct, 2)
        }

    # Add token metrics to response
    response_data = {
        "optimizer": optimizer_type,
        "original_chars": len(original_text),
        "optimized_chars": len(optimized_text),
        "char_savings_percentage": round(((len(original_text) - len(optimized_text)) / max(1, len(original_text))) * 100, 2),
        "token_metrics": savings,
        "optimized_text": optimized_text,
        "details": {k: v for k, v in result.items() if k != "text"}
    }
    
    return JSONResponse(content=response_data)

def main():
    print("Starting TokenForge Web Dashboard on http://localhost:8000")
    uvicorn.run("token_forge.dashboard.app:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
