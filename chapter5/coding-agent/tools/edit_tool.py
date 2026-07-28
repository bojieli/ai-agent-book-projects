"""
Edit tool - File editing with search and replace
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from .base import BaseTool


class EditTool(BaseTool):
    """Performs exact string replacements in files"""
    
    @property
    def name(self) -> str:
        return "Edit"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Edit file using search and replace
        
        - You must use Read tool at least once before editing
        - Ensure you preserve exact indentation (tabs/spaces)
        - The edit will FAIL if old_string is not unique in the file
        - Use replace_all to change every instance of old_string
        """
        file_path = Path(params["file_path"]).expanduser().resolve()
        old_string = params["old_string"]
        new_string = params["new_string"]
        replace_all = params.get("replace_all", False)
        
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        # Empty old_string matches between every character; replace_all would insert everywhere.
        if old_string == "":
            return {"error": "old_string cannot be empty"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if old_string exists
            if old_string not in content:
                return {"error": f"String not found in file: {old_string[:100]}..."}
            
            # Count occurrences
            occurrences = content.count(old_string)
            
            # Check uniqueness if not replace_all
            if not replace_all and occurrences > 1:
                return {
                    "error": f"String appears {occurrences} times in file. Use replace_all=true or provide more context to make it unique."
                }
            
            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                replacements = occurrences
            else:
                new_content = content.replace(old_string, new_string, 1)
                replacements = 1
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            result = {
                "file_path": str(file_path),
                "replacements": replacements,
                "old_length": len(content),
                "new_length": len(new_content)
            }
            
            # Check for lint errors
            lint_result = self._check_lint_errors(file_path)
            if lint_result:
                result["lint_check"] = lint_result
            
            return result
            
        except Exception as e:
            return {"error": f"Error editing file: {str(e)}"}
    
    def _check_lint_errors(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Check for lint errors after file modification"""
        suffix = file_path.suffix
        
        try:
            if suffix == ".py":
                result = subprocess.run(
                    ["python3", "-m", "py_compile", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    return {
                        "language": "python",
                        "has_errors": True,
                        "errors": result.stderr
                    }
                else:
                    return {
                        "language": "python",
                        "has_errors": False,
                        "message": "No syntax errors detected"
                    }
            
            elif suffix in [".js", ".jsx", ".ts", ".tsx"]:
                result = subprocess.run(
                    ["node", "--check", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    return {
                        "language": "javascript/typescript",
                        "has_errors": True,
                        "errors": result.stderr
                    }
                else:
                    return {
                        "language": "javascript/typescript",
                        "has_errors": False,
                        "message": "No syntax errors detected"
                    }
            
            return None
            
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            return {"error": "Lint check timed out"}
        except Exception:
            return None

