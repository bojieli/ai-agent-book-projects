"""
MultiEdit tool - Multiple edits to a single file in one operation
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base import BaseTool


class MultiEditTool(BaseTool):
    """Makes multiple edits to a single file in one operation"""
    
    @property
    def name(self) -> str:
        return "MultiEdit"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform multiple edits on a file
        
        - Built on top of Edit tool
        - All edits are applied in sequence, in the order they are provided
        - Each edit operates on the result of the previous edit
        - All edits must be valid for the operation to succeed - if any edit fails, none will be applied
        - The edits are atomic - either all succeed or none are applied
        """
        file_path = Path(params["file_path"]).expanduser().resolve()
        edits = params.get("edits")
        if edits is None:
            edits = []

        creating_new = False
        if not file_path.exists():
            # Defer create/write until every edit succeeds (atomic).
            if edits and edits[0]["old_string"] == "":
                creating_new = True
                try:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return {"error": f"Error creating file: {str(e)}"}
            else:
                return {"error": f"File not found: {file_path}"}
        
        try:
            if creating_new:
                content = ""
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            original_content = content
            results = []
            
            # Apply edits sequentially
            for i, edit in enumerate(edits):
                old_string = edit["old_string"]
                new_string = edit["new_string"]
                replace_all = edit.get("replace_all", False)
                
                # Empty old_string only valid when creating a new file (tools.json / Edit parity).
                if old_string == "":
                    if creating_new and i == 0:
                        content = new_string
                        results.append({"edit": i + 1, "action": "created", "success": True})
                        continue
                    return {"error": "old_string cannot be empty"}

                if old_string not in content:
                    return {
                        "error": f"Edit #{i + 1} failed: String not found",
                        "old_string": old_string[:100],
                        "completed_edits": i
                    }
                
                occurrences = content.count(old_string)
                if not replace_all and occurrences > 1:
                    return {
                        "error": f"Edit #{i + 1} failed: String appears {occurrences} times",
                        "completed_edits": i
                    }
                
                if replace_all:
                    content = content.replace(old_string, new_string)
                    replacements = occurrences
                else:
                    content = content.replace(old_string, new_string, 1)
                    replacements = 1
                
                results.append({
                    "edit": i + 1,
                    "replacements": replacements,
                    "success": True
                })
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result = {
                "file_path": str(file_path),
                "total_edits": len(edits),
                "successful_edits": len(results),
                "edit_results": results,
                "old_size": len(original_content),
                "new_size": len(content)
            }
            
            # Check for lint errors
            lint_result = self._check_lint_errors(file_path)
            if lint_result:
                result["lint_check"] = lint_result
            
            return result
            
        except Exception as e:
            return {"error": f"Error in multi-edit: {str(e)}"}
    
    def _check_lint_errors(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Check for lint errors"""
        suffix = file_path.suffix
        try:
            if suffix == ".py":
                result = subprocess.run(
                    ["python3", "-m", "py_compile", str(file_path)],
                    capture_output=True, text=True, timeout=5
                )
                return {
                    "language": "python",
                    "has_errors": result.returncode != 0,
                    "errors": result.stderr if result.returncode != 0 else None,
                    "message": "No syntax errors detected" if result.returncode == 0 else None
                }
            return None
        except:
            return None

