import ast
import re

class CodeASTMinifier:
    """
    Minifies source code files by extracting definitions (class/method signatures)
    and replacing method bodies with placeholders. Removes comments and empty lines.
    Supports Python AST-based pruning and regex-based JavaScript/TypeScript pruning.
    """
    def __init__(self, keep_docstrings: bool = True):
        self.keep_docstrings = keep_docstrings

    def optimize(self, text: str, **kwargs) -> dict:
        if not text:
            return {"text": "", "language": "unknown"}
            
        language = kwargs.get("language", "python").lower()
        keep_docs = kwargs.get("keep_docstrings", self.keep_docstrings)
        
        # Simple auto-detect if not specified
        if "language" not in kwargs:
            if "def " in text or "class " in text and ":" in text:
                language = "python"
            elif "function" in text or "const " in text or "import " in text:
                language = "javascript"

        if language == "python":
            minified_code = self._minify_python(text, keep_docs)
        elif language in ["javascript", "typescript", "js", "ts"]:
            minified_code = self._minify_js(text)
        else:
            # Fallback to simple comment & empty line stripper
            minified_code = self._strip_comments_generic(text)

        orig_len = len(text)
        min_len = len(minified_code)
        saved = orig_len - min_len
        
        return {
            "text": minified_code,
            "language": language,
            "original_chars": orig_len,
            "minified_chars": min_len,
            "reduction_percentage": round((saved / max(1, orig_len)) * 100, 2)
        }

    def _minify_python(self, code: str, keep_docstrings: bool) -> str:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fallback if syntactically invalid Python
            return self._strip_comments_generic(code)

        class DefPruner(ast.NodeTransformer):
            def __init__(self, keep_docs):
                self.keep_docs = keep_docs

            def visit_FunctionDef(self, node):
                # Clean up function body
                has_doc = (
                    self.keep_docs and
                    node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                )
                
                doc_expr = node.body[0] if has_doc else None
                
                # Replace body with just '...' or 'pass'
                placeholder = ast.Expr(value=ast.Constant(value=Ellipsis))
                
                if doc_expr:
                    node.body = [doc_expr, placeholder]
                else:
                    node.body = [placeholder]
                
                return node

            def visit_AsyncFunctionDef(self, node):
                return self.visit_FunctionDef(node)

        # Prune functions
        pruner = DefPruner(keep_docstrings)
        pruned_tree = pruner.visit(tree)
        ast.fix_missing_locations(pruned_tree)
        
        # Convert AST back to code (available in Python 3.9+)
        try:
            minified = ast.unparse(pruned_tree)
        except Exception:
            # Fallback: simple walk and formatting
            return self._strip_comments_generic(code)
            
        return minified

    def _minify_js(self, code: str) -> str:
        # Simple regex-based class/function outline extractor for JS/TS
        lines = code.split("\n")
        outline = []
        
        # Look for imports, class headers, method signatures, exports
        import_pattern = re.compile(r'^(import|export)\s+.*')
        class_pattern = re.compile(r'^\s*(class\s+\w+)')
        func_pattern = re.compile(r'^\s*(async\s+)?(function\s+\w+\(|const\s+\w+\s*=\s*(\(.*?\)|async\s*\(.*?\))\s*=>|(\w+)\(.*?\)\s*\{)')
        
        for line in lines:
            stripped = line.strip()
            # Keep imports
            if import_pattern.match(stripped):
                outline.append(line)
            # Keep class definitions
            elif class_pattern.match(stripped):
                outline.append(line)
            # Keep functions / methods
            elif func_pattern.match(stripped):
                # Append line and append a placeholder closing
                indent = len(line) - len(stripped)
                outline.append(line)
                outline.append(" " * indent + "  // ... [implementation hidden]")
                outline.append(" " * indent + "}")
                
        if not outline:
            return self._strip_comments_generic(code)
            
        return "\n".join(outline)

    def _strip_comments_generic(self, text: str) -> str:
        # Strip single-line comments (# and //) and multi-line comments (/* */)
        # and remove extra empty lines
        text_no_comments = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        
        lines = text_no_comments.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            
            # Inline comment stripping (basic)
            if " //" in line:
                line = line.split(" //")[0]
            elif " #" in line:
                line = line.split(" #")[0]
                
            if line.strip():
                cleaned_lines.append(line)
                
        return "\n".join(cleaned_lines)
