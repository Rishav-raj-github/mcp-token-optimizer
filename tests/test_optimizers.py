import pytest
import json

from token_forge.optimizers.cache_aligner import CacheAligner
from token_forge.optimizers.semantic import SemanticCompressor
from token_forge.optimizers.code_ast import CodeASTMinifier
from token_forge.optimizers.logs import LogCondenser
from token_forge.optimizers.data_format import DataMinifier
from token_forge.optimizers.stopwords import StopwordStripper
from token_forge.optimizers.system_prompt import SystemPromptMinifier

def test_cache_aligner():
    aligner = CacheAligner(target_block_tokens=1024)
    text = "Hello world, this is a test prompt."
    res = aligner.optimize(text, format_style="markdown")
    assert "text" in res
    assert "CACHE_PAD" in res["text"]
    assert res["aligned_tokens"] % 1024 == 0

def test_semantic_compressor():
    compressor = SemanticCompressor(target_ratio=0.5)
    text = "The quick brown fox jumps over the lazy dog.\nImportant text here.\nUnrelated sentence that should be pruned."
    res = compressor.optimize(text)
    assert len(res["text"]) < len(text)
    assert res["savings_percentage"] > 0

def test_code_ast_minifier():
    minifier = CodeASTMinifier()
    code = """
def process_data(x):
    # This is a comment
    print("Beginning execution")
    y = x * 2
    return y
"""
    res = minifier.optimize(code, language="python")
    assert "..." in res["text"] or "pass" in res["text"] or "Ellipsis" in res["text"]
    assert "Beginning execution" not in res["text"]

def test_log_condenser():
    condenser = LogCondenser(max_head_lines=2, max_tail_lines=2)
    logs = "\n".join([f"2026-07-07T12:00:00.000Z [INFO] Line {i}" for i in range(15)])
    res = condenser.optimize(logs)
    assert "[TS]" in res["text"]
    assert "TRUNCATED" in res["text"]
    assert len(res["text"].split("\n")) < len(logs.split("\n"))

def test_data_minifier():
    minifier = DataMinifier()
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    res = minifier.optimize(json.dumps(data), target_format="csv")
    assert res["format"] == "csv"
    assert "Alice" in res["text"]
    assert "id,name" in res["text"]

def test_stopword_stripper():
    stripper = StopwordStripper()
    text = "This is indeed a very simple and direct message."
    res = stripper.optimize(text, aggressive=True)
    assert "indeed" not in res["text"]
    assert len(res["text"]) < len(text)

def test_system_prompt_minifier():
    minifier = SystemPromptMinifier()
    prompt = """
Instructions:
<optional trigger="chart,graph">
Plot data using svg lines.
</optional>
Always respond in JSON.
"""
    # No trigger word
    res_no_trigger = minifier.optimize(prompt, query="Hello world")
    assert "Plot data using svg" not in res_no_trigger["text"]
    
    # Trigger word in query
    res_trigger = minifier.optimize(prompt, query="Render a chart please")
    assert "Plot data using svg" in res_trigger["text"]

# End of test suite: verifies prompt minification matches expectations.
