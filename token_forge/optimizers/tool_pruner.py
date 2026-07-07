class ToolPruner:
    """
    Dynamically filters a list of tool definitions based on user query keywords.
    Avoids sending thousands of tokens of unused JSON Schema tool definitions to the LLM.
    """
    def __init__(self, mandatory_tools: list = None):
        self.mandatory_tools = mandatory_tools or []

    def optimize(self, tools_list_or_json, query: str = "", **kwargs) -> dict:
        """
        Accepts a list of tool schemas (or JSON representation) and the user's query.
        Returns a pruned list of tool schemas that are relevant to the query.
        """
        import json
        
        mandatory = kwargs.get("mandatory_tools", self.mandatory_tools)
        
        if isinstance(tools_list_or_json, str):
            try:
                tools = json.loads(tools_list_or_json)
            except json.JSONDecodeError:
                return {"text": tools_list_or_json, "tools_saved": 0}
        else:
            tools = tools_list_or_json

        if not isinstance(tools, list):
            return {"text": json.dumps(tools), "tools_saved": 0}

        if not query:
            # If no query is provided, keep all tools
            return {
                "text": json.dumps(tools),
                "original_count": len(tools),
                "final_count": len(tools),
                "tools_saved": 0,
                "tools": tools
            }

        query_lower = query.lower()
        pruned_tools = []
        
        for tool in tools:
            # Handles OpenAI / Anthropic format tools
            # Usually has name, description
            name = ""
            desc = ""
            
            # Extract tool details
            if "name" in tool:
                name = tool["name"]
                desc = tool.get("description", "")
            elif "function" in tool:
                name = tool["function"].get("name", "")
                desc = tool["function"].get("description", "")
                
            # If tool is mandatory, always keep it
            if name in mandatory:
                pruned_tools.append(tool)
                continue
                
            # Check for keyword match in query
            # Split tool name by underscores/hyphens and match
            name_parts = name.replace("_", " ").replace("-", " ").lower().split()
            matched = False
            
            # Simple keyword match
            for part in name_parts:
                if len(part) > 2 and part in query_lower:
                    matched = True
                    break
                    
            # Check in description
            if not matched and desc:
                # Look for word-level matches
                desc_words = desc.lower().split()
                for word in desc_words:
                    if len(word) > 3 and word in query_lower:
                        # Allow custom weighting
                        matched = True
                        break
                        
            if matched:
                pruned_tools.append(tool)

        # Fallback: if no tools matched, keep at least one tool or all to avoid empty state
        if not pruned_tools and tools:
            pruned_tools = tools[:1]

        saved_count = len(tools) - len(pruned_tools)
        
        return {
            "text": json.dumps(pruned_tools),
            "original_count": len(tools),
            "final_count": len(pruned_tools),
            "tools_saved": saved_count,
            "tools": pruned_tools
        }
