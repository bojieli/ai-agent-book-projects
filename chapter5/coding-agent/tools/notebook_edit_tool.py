"""
NotebookEdit tool - Edit Jupyter notebook cells
"""

import json
from pathlib import Path
from typing import Dict, Any
from .base import BaseTool


class NotebookEditTool(BaseTool):
    """Completely replaces the contents of a specific cell in a Jupyter notebook"""
    
    @property
    def name(self) -> str:
        return "NotebookEdit"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Edit Jupyter notebook cell
        
        - Completely replaces the contents of a specific cell
        - The notebook_path parameter must be an absolute path
        - Use edit_mode=insert to add a new cell
        - Use edit_mode=delete to delete a cell
        - Use edit_mode=replace to replace cell contents (default)
        """
        notebook_path = Path(params["notebook_path"]).expanduser().resolve()
        cell_id = params.get("cell_id")
        new_source = params.get("new_source")
        cell_type = params.get("cell_type", "code")
        edit_mode = params.get("edit_mode", "replace")
        
        if not notebook_path.exists():
            return {"error": f"Notebook not found: {notebook_path}"}
        
        try:
            # Load notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            cells = notebook.get('cells', [])
            
            if edit_mode == "insert":
                if new_source is None:
                    return {"error": "new_source required for insert mode"}
                # Insert new cell
                new_cell = {
                    "cell_type": cell_type,
                    "metadata": {},
                    # nbformat stores source as a list of lines that KEEP their
                    # trailing '\n'; readers rebuild the cell with ''.join(source).
                    "source": new_source.splitlines(keepends=True)
                }
                
                if cell_type == "code":
                    new_cell["outputs"] = []
                    new_cell["execution_count"] = None
                
                # Find insertion point
                if cell_id:
                    # Insert after cell with given ID
                    for i, cell in enumerate(cells):
                        if cell.get('id') == cell_id:
                            cells.insert(i + 1, new_cell)
                            break
                    else:
                        return {"error": f"Cell with ID {cell_id} not found"}
                else:
                    # Insert at beginning
                    cells.insert(0, new_cell)
                
                action = "inserted"
                
            elif edit_mode == "delete":
                # Delete cell
                if cell_id:
                    for i, cell in enumerate(cells):
                        if cell.get('id') == cell_id:
                            cells.pop(i)
                            break
                    else:
                        return {"error": f"Cell with ID {cell_id} not found"}
                else:
                    return {"error": "cell_id required for delete mode"}
                
                action = "deleted"
                
            else:  # replace
                if new_source is None:
                    return {"error": "new_source required for replace mode"}
                # Replace cell contents
                if cell_id:
                    for cell in cells:
                        if cell.get('id') == cell_id:
                            cell["source"] = new_source.splitlines(keepends=True)
                            if cell_type:
                                cell["cell_type"] = cell_type
                            break
                    else:
                        return {"error": f"Cell with ID {cell_id} not found"}
                else:
                    return {"error": "cell_id required for replace mode"}
                
                action = "replaced"
            
            # Update notebook
            notebook["cells"] = cells
            
            # Write back
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=1, ensure_ascii=False)
            
            return {
                "notebook_path": str(notebook_path),
                "action": action,
                "total_cells": len(cells)
            }
            
        except json.JSONDecodeError:
            return {"error": "Invalid Jupyter notebook format"}
        except Exception as e:
            return {"error": f"Error editing notebook: {str(e)}"}

