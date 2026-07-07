import re
import math
import json
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Token-Optimizer")

# Import our modular optimizers
# (We add try/except so that it can run even if not installed in path yet)
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
    # Local relative import fallback if executed from local directory
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

# Instantiate optimization engines
aligner = CacheAligner()
semantic_compressor = SemanticCompressor()
ast_minifier = CodeASTMinifier()
log_condenser = LogCondenser()
data_minifier = DataMinifier()
history_summarizer = ChatHistorySummarizer()
stopword_stripper = StopwordStripper()
rag_filter = RAGFilter()
xml_minifier = XMLMinifier()
semantic_cache = SemanticCache()
model_router = ModelRouter()
tool_pruner = ToolPruner()
system_minifier = SystemPromptMinifier()

@mcp.tool()
def align_prompt_cache(text: str, format_style: str = "markdown", target_block_tokens: int = 1024) -> str:
    """
    Pads prompt strings to align exactly to LLM cache block boundaries (typically 1024 tokens).
    Prevents prompt cache invalidation by ensuring identical prefix token lengths.
    
    Args:
        text: The prompt or context text to align.
        format_style: The format of padding comment (markdown, python, javascript, raw).
        target_block_tokens: The cache block size (default 1024).
    """
    res = aligner.optimize(text, format_style=format_style, target_block_tokens=target_block_tokens)
    return res["text"]

@mcp.tool()
def prune_logs(text: str, max_head_lines: int = 25, max_tail_lines: int = 25) -> str:
    """
    Cleans up stack traces, build logs, and console outputs.
    Strips redundant timestamps, hexadecimal memory addresses, duplicate errors, 
    and truncates redundant middle log entries.
    
    Args:
        text: Raw log text.
        max_head_lines: Number of starting lines to keep.
        max_tail_lines: Number of trailing lines to keep.
    """
    res = log_condenser.optimize(text, max_head_lines=max_head_lines, max_tail_lines=max_tail_lines)
    return res["text"]

@mcp.tool()
def compress_semantic_context(text: str, target_ratio: float = 0.6) -> str:
    """
    Prunes low-information sentences and grammatical fillers from a large context.
    Uses TF-IDF rarity scoring to maintain core semantic structure at a lower token cost.
    
    Args:
        text: Input text/document to compress.
        target_ratio: Ratio of original information to keep (e.g., 0.6 keeps 60%).
    """
    res = semantic_compressor.optimize(text, target_ratio=target_ratio)
    return res["text"]

@mcp.tool()
def minify_code(code: str, language: str = "python", keep_docstrings: bool = True) -> str:
    """
    Minifies source code files by keeping only class/function signatures and API blueprints.
    Replaces implementation bodies with '...' placeholders to reduce code context tokens by up to 85%.
    
    Args:
        code: Raw source code string.
        language: Programming language (python, javascript, typescript).
        keep_docstrings: Whether to preserve code docstrings/comments.
    """
    res = ast_minifier.optimize(code, language=language, keep_docstrings=keep_docstrings)
    return res["text"]

@mcp.tool()
def minify_data(data_json: str, target_format: str = "csv_or_kv") -> str:
    """
    Converts heavy structured JSON or YAML payloads into compact KV pairs or CSV strings.
    Strips away syntax braces, brackets, and quotes to save up to 70% of payload tokens.
    
    Args:
        data_json: JSON string to compress.
        target_format: Output format ('csv', 'kv', 'csv_or_kv').
    """
    res = data_minifier.optimize(data_json, target_format=target_format)
    return res["text"]

@mcp.tool()
def optimize_rag_chunks(chunks_json: str, similarity_threshold: float = 0.65, min_score: float = 0.4) -> str:
    """
    Deduplicates and filters retrieved RAG chunks.
    Removes low-relevance chunks and eliminates near-duplicate contexts.
    
    Args:
        chunks_json: A JSON array of chunks: [{"text": "...", "score": 0.8}, ...]
        similarity_threshold: Cosine/Jaccard similarity cutoff for redundancy.
        min_score: Minimum relevance score to retain a chunk.
    """
    res = rag_filter.optimize(chunks_json, similarity_threshold=similarity_threshold, min_score=min_score)
    return res["text"]

@mcp.tool()
def route_model(query: str) -> str:
    """
    Evaluates query complexity and recommends the optimal LLM tier (cheap vs flagship).
    Saves API costs by routing simple classification/lookup queries to small models.
    
    Args:
        query: Incoming user query.
    """
    res = model_router.route(query)
    return json.dumps(res, indent=2)

@mcp.tool()
def minify_system_prompt(system_prompt: str, query: str) -> str:
    """
    Prunes optional sections of system prompts that are not relevant to the current user query.
    Looks for <optional trigger="words"> blocks and removes them if the query doesn't match.
    
    Args:
        system_prompt: The template system prompt containing optional tags.
        query: The user's query to evaluate relevance.
    """
    res = system_minifier.optimize(system_prompt, query=query)
    return res["text"]

@mcp.tool()
def strip_stopwords(text: str, aggressive: bool = False) -> str:
    """
    Removes common articles, determiners, and grammatical fillers to make text telegraphic.
    
    Args:
        text: Input text.
        aggressive: Set True to also remove common prepositions and auxiliary verbs.
    """
    res = stopword_stripper.optimize(text, aggressive=aggressive)
    return res["text"]

def main():
    mcp.run()

if __name__ == "__main__":
    main()
