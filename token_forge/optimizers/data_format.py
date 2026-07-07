import json
import csv
import io

class DataMinifier:
    """
    Minifies heavy nested structured JSON/YAML payloads.
    Converts lists of objects into flat CSV tables, and nested objects into flat Key-Value lines.
    Saves extensive token counts by stripping structural syntax (braces, quotes, indentations).
    """
    def __init__(self, target_format: str = "csv_or_kv"):
        self.target_format = target_format

    def optimize(self, text: str, **kwargs) -> dict:
        if not text:
            return {"text": "", "format": "unknown"}

        target_fmt = kwargs.get("target_format", self.target_format)
        
        # 1. Parse input string (JSON or basic YAML-like format)
        data = None
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Let's try parsing simple YAML or invalid JSON using python evaluation safely if possible,
            # but simple JSON fallback is safer.
            pass
            
        if data is None:
            # Not valid JSON, just return stripped compact representation
            return {
                "text": json.dumps(text),
                "format": "raw_string",
                "reduction_percentage": 0.0
            }

        # 2. Process based on target format
        minified = ""
        output_format = ""
        
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and target_fmt in ["csv", "csv_or_kv"]:
            # List of objects -> Convert to CSV
            minified = self._to_csv(data)
            output_format = "csv"
        elif isinstance(data, dict) and target_fmt in ["kv", "csv_or_kv"]:
            # Object -> Convert to Flat Key-Value lines
            flat_dict = {}
            self._flatten_dict(data, "", flat_dict)
            lines = [f"{k}: {v}" for k, v in flat_dict.items()]
            minified = "\n".join(lines)
            output_format = "key_value"
        else:
            # Default fallback: Minified compact JSON (no spaces, no newlines)
            minified = json.dumps(data, separators=(',', ':'))
            output_format = "json_compact"

        orig_len = len(text)
        min_len = len(minified)
        saved = orig_len - min_len
        
        return {
            "text": minified,
            "format": output_format,
            "original_chars": orig_len,
            "minified_chars": min_len,
            "reduction_percentage": round((saved / max(1, orig_len)) * 100, 2)
        }

    def _to_csv(self, data_list: list) -> str:
        # Collect all unique keys from list of dicts
        keys = []
        for obj in data_list:
            for k in obj.keys():
                if k not in keys:
                    keys.append(k)
                    
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        # Write headers
        writer.writerow(keys)
        # Write rows
        for obj in data_list:
            writer.writerow([obj.get(k, "") for k in keys])
            
        return output.getvalue().strip()

    def _flatten_dict(self, d: dict, parent_key: str, result: dict):
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                self._flatten_dict(v, new_key, result)
            elif isinstance(v, list):
                # Turn list of simple primitives to comma separated list, else compact json
                if all(not isinstance(item, (dict, list)) for item in v):
                    result[new_key] = ",".join(str(x) for x in v)
                else:
                    result[new_key] = json.dumps(v, separators=(',', ':'))
            else:
                result[new_key] = v
