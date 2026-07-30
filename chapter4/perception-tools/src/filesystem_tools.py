"""File-system perception tools and tightly scoped mutation helpers.

Read operations retain their historical behavior.  Move, copy, and delete are
available only beneath the directory named by ``PERCEPTION_MUTATION_ROOT``.
They reject absolute paths, traversal, symlinks, and the private quarantine
directory.  Delete and overwrite are implemented as reversible quarantine
moves so the experiment never has to destroy user data.
"""
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

from dotenv import load_dotenv
from mcp.types import TextContent

from base import ActionResponse, validate_file_path


load_dotenv()


MUTATION_ROOT_ENV = "PERCEPTION_MUTATION_ROOT"
QUARANTINE_DIRECTORY = ".perception-trash"


def _mutation_error(operation: str, exc: Exception) -> TextContent:
    action_response = ActionResponse(
        success=False,
        message=f"Filesystem {operation} failed: {exc}",
        metadata={
            "operation": operation,
            "error_type": type(exc).__name__,
            "mutation_root_env": MUTATION_ROOT_ENV,
        },
    )
    return TextContent(
        type="text",
        text=json.dumps(action_response.model_dump()),
    )


def _mutation_root() -> Path:
    configured = os.getenv(MUTATION_ROOT_ENV, "").strip()
    if not configured:
        raise PermissionError(
            f"{MUTATION_ROOT_ENV} must name an explicit experiment workspace"
        )
    root = Path(configured).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Mutation root is not a directory: {root}")
    return root


def _relative_parts(value: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Path must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute():
        raise PermissionError("Absolute paths are not allowed for filesystem mutations")
    if ".." in path.parts:
        raise PermissionError("Parent traversal is not allowed for filesystem mutations")
    parts = tuple(part for part in path.parts if part not in {"", "."})
    if not parts:
        raise PermissionError("The mutation workspace root itself cannot be changed")
    if parts[0] == QUARANTINE_DIRECTORY:
        raise PermissionError("The filesystem quarantine is managed by the server")
    return parts


def _inside_root(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_mutation_path(
    root: Path,
    value: str,
    *,
    must_exist: bool,
) -> Path:
    parts = _relative_parts(value)
    unresolved = root.joinpath(*parts)
    if must_exist:
        resolved = unresolved.resolve(strict=True)
    else:
        parent = unresolved.parent.resolve(strict=True)
        if not parent.is_dir():
            raise NotADirectoryError(f"Destination parent is not a directory: {parent}")
        resolved = parent / unresolved.name
    if not _inside_root(root, resolved):
        raise PermissionError("Resolved path escapes the configured mutation root")
    if unresolved.is_symlink() or (resolved.exists() and resolved.is_symlink()):
        raise PermissionError("Symbolic links are not allowed for filesystem mutations")
    return resolved


def _assert_no_symlinks(path: Path) -> None:
    if path.is_symlink():
        raise PermissionError(f"Symbolic links are not allowed: {path}")
    if path.is_dir():
        for item in path.rglob("*"):
            if item.is_symlink():
                raise PermissionError(f"Symbolic links are not allowed: {item}")


def _fingerprint(path: Path) -> dict:
    """Return a deterministic content receipt for one file or directory."""
    digest = hashlib.sha256()
    total_bytes = 0
    entries = 0
    if path.is_file():
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                total_bytes += len(block)
        entries = 1
        kind = "file"
    elif path.is_dir():
        kind = "directory"
        for item in sorted(path.rglob("*"), key=lambda candidate: candidate.as_posix()):
            if item.is_symlink():
                raise PermissionError(f"Symbolic links are not allowed: {item}")
            relative = item.relative_to(path).as_posix()
            item_kind = "directory" if item.is_dir() else "file"
            digest.update(f"{item_kind}\0{relative}\0".encode("utf-8"))
            entries += 1
            if item.is_file():
                with item.open("rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
                        total_bytes += len(block)
    else:
        raise ValueError(f"Unsupported filesystem object: {path}")
    return {
        "kind": kind,
        "sha256": digest.hexdigest(),
        "bytes": total_bytes,
        "entries": entries,
    }


def _quarantine(root: Path, path: Path) -> Path:
    trash = root / QUARANTINE_DIRECTORY
    trash.mkdir(mode=0o700, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = trash / f"{stamp}-{uuid.uuid4().hex}-{path.name}"
    path.rename(destination)
    return destination


async def move_path(
    source_path: str,
    destination_path: str,
    overwrite: bool = False,
) -> TextContent:
    """Move a file/directory inside the explicit mutation workspace."""
    operation = "move"
    quarantined_destination = None
    try:
        root = _mutation_root()
        source = _resolve_mutation_path(root, source_path, must_exist=True)
        destination = _resolve_mutation_path(root, destination_path, must_exist=False)
        if source == destination:
            raise ValueError("Source and destination must be different")
        _assert_no_symlinks(source)
        before = _fingerprint(source)
        if destination.exists():
            if not overwrite:
                raise FileExistsError(f"Destination already exists: {destination_path}")
            _assert_no_symlinks(destination)
            quarantined_destination = _quarantine(root, destination)
        try:
            source.rename(destination)
        except Exception:
            if quarantined_destination and not destination.exists():
                quarantined_destination.rename(destination)
            raise
        after = _fingerprint(destination)
        if before != after or source.exists():
            raise RuntimeError("Post-move verification failed")
        response = ActionResponse(
            success=True,
            message={
                "operation": operation,
                "source": source_path,
                "destination": destination_path,
                "source_exists_after": source.exists(),
                "destination_fingerprint": after,
                "replaced_path_quarantine": (
                    str(quarantined_destination.relative_to(root))
                    if quarantined_destination else None
                ),
            },
            metadata={
                "mutation_root": str(root),
                "pre_operation_fingerprint": before,
                "verification": "source absent and destination fingerprint matches",
            },
        )
        return TextContent(type="text", text=json.dumps(response.model_dump()))
    except Exception as exc:
        logging.error("Filesystem move error: %s", traceback.format_exc())
        return _mutation_error(operation, exc)


async def copy_path(
    source_path: str,
    destination_path: str,
    overwrite: bool = False,
) -> TextContent:
    """Copy a file/directory inside the explicit mutation workspace."""
    operation = "copy"
    quarantined_destination = None
    try:
        root = _mutation_root()
        source = _resolve_mutation_path(root, source_path, must_exist=True)
        destination = _resolve_mutation_path(root, destination_path, must_exist=False)
        if source == destination:
            raise ValueError("Source and destination must be different")
        _assert_no_symlinks(source)
        before = _fingerprint(source)
        if destination.exists():
            if not overwrite:
                raise FileExistsError(f"Destination already exists: {destination_path}")
            _assert_no_symlinks(destination)
            quarantined_destination = _quarantine(root, destination)
        try:
            if source.is_dir():
                shutil.copytree(source, destination, symlinks=False)
            else:
                shutil.copy2(source, destination)
        except Exception:
            if destination.exists():
                if destination.is_dir():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()
            if quarantined_destination:
                quarantined_destination.rename(destination)
            raise
        after = _fingerprint(destination)
        if before != after or not source.exists():
            raise RuntimeError("Post-copy verification failed")
        response = ActionResponse(
            success=True,
            message={
                "operation": operation,
                "source": source_path,
                "destination": destination_path,
                "source_exists_after": source.exists(),
                "destination_fingerprint": after,
                "replaced_path_quarantine": (
                    str(quarantined_destination.relative_to(root))
                    if quarantined_destination else None
                ),
            },
            metadata={
                "mutation_root": str(root),
                "pre_operation_fingerprint": before,
                "verification": "source retained and destination fingerprint matches",
            },
        )
        return TextContent(type="text", text=json.dumps(response.model_dump()))
    except Exception as exc:
        logging.error("Filesystem copy error: %s", traceback.format_exc())
        return _mutation_error(operation, exc)


async def delete_path(path: str) -> TextContent:
    """Remove a path from the workspace by moving it to private quarantine."""
    operation = "delete"
    try:
        root = _mutation_root()
        target = _resolve_mutation_path(root, path, must_exist=True)
        _assert_no_symlinks(target)
        before = _fingerprint(target)
        quarantine = _quarantine(root, target)
        after = _fingerprint(quarantine)
        if target.exists() or before != after:
            raise RuntimeError("Post-delete verification failed")
        response = ActionResponse(
            success=True,
            message={
                "operation": operation,
                "path": path,
                "path_exists_after": target.exists(),
                "quarantine_path": str(quarantine.relative_to(root)),
                "reversible": True,
                "quarantine_fingerprint": after,
            },
            metadata={
                "mutation_root": str(root),
                "pre_operation_fingerprint": before,
                "verification": "original path absent and quarantine fingerprint matches",
            },
        )
        return TextContent(type="text", text=json.dumps(response.model_dump()))
    except Exception as exc:
        logging.error("Filesystem delete error: %s", traceback.format_exc())
        return _mutation_error(operation, exc)


async def read_file(
    file_path: str,
    encoding: str = "utf-8",
    max_length: int = 50000
) -> Union[str, TextContent]:
    """
    Read a file and return its contents.
    
    Args:
        file_path: Path to the file
        encoding: File encoding (default: utf-8)
        max_length: Maximum number of characters to return
        
    Returns:
        TextContent with file contents
    """
    try:
        path = validate_file_path(file_path)
        
        logging.info(f"📖 Reading file: {path}")
        
        with open(path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        
        if max_length < 0:
            max_length = len(content)
        truncated = len(content) > max_length
        if truncated:
            content = content[:max_length]
        
        result = {
            "file_path": str(path),
            "content": content,
            "size_bytes": path.stat().st_size,
            "truncated": truncated,
            "encoding": encoding
        }
        
        logging.info(f"✅ Successfully read file ({len(content)} characters)")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"file_path": str(path)}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"File reading failed: {str(e)}"
        logging.error(f"File read error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "file_read_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def grep_search(
    pattern: str,
    directory: str,
    file_pattern: str = "*",
    recursive: bool = True,
    case_sensitive: bool = False,
    max_results: int = 100
) -> Union[str, TextContent]:
    """
    Search for a pattern in files using grep-like functionality.
    
    Args:
        pattern: Regular expression pattern to search for
        directory: Directory to search in
        file_pattern: File pattern to match (e.g., "*.py")
        recursive: Whether to search recursively
        case_sensitive: Whether search is case-sensitive
        max_results: Maximum number of results to return
        
    Returns:
        TextContent with search results
    """
    try:
        dir_path = Path(directory).expanduser().resolve()
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")
        
        logging.info(f"🔍 Searching for pattern '{pattern}' in {dir_path}")
        
        results = []
        if max_results <= 0:
            action_response = ActionResponse(
                success=True,
                message={
                    "pattern": pattern,
                    "results": results,
                    "total_found": 0,
                    "truncated": False,
                },
                metadata={
                    "directory": str(dir_path),
                    "file_pattern": file_pattern,
                    "recursive": recursive,
                },
            )
            return TextContent(
                type="text",
                text=json.dumps(action_response.model_dump()),
            )

        flags = re.IGNORECASE if not case_sensitive else 0
        regex = re.compile(pattern, flags)

        if recursive:
            files = dir_path.rglob(file_pattern)
        else:
            files = dir_path.glob(file_pattern)

        for file_path in files:
            if not file_path.is_file():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append({
                                "file": str(file_path.relative_to(dir_path)),
                                "line_number": line_num,
                                "line": line.strip(),
                                "absolute_path": str(file_path)
                            })

                            if len(results) >= max_results:
                                break

                if len(results) >= max_results:
                    break

            except Exception as e:
                logging.warning(f"Error reading {file_path}: {e}")
                continue

        logging.info(f"✅ Found {len(results)} matches")

        action_response = ActionResponse(
            success=True,
            message={
                "pattern": pattern,
                "results": results,
                "total_found": len(results),
                "truncated": len(results) >= max_results
            },

            metadata={
                "directory": str(dir_path),
                "file_pattern": file_pattern,
                "recursive": recursive
            }
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Grep search failed: {str(e)}"
        logging.error(f"Grep error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "grep_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )


async def summarize_text(
    text: str,
    max_length: int = 500,
    use_llm: bool = True
) -> Union[str, TextContent]:
    """
    Summarize long text content.
    
    Args:
        text: Text to summarize
        max_length: Target summary length
        use_llm: Whether to use LLM for summarization (if available)
        
    Returns:
        TextContent with summary
    """
    try:
        logging.info(f"📝 Summarizing text ({len(text)} characters)")
        
        if use_llm:
            # TODO: Integrate with LLM API for better summarization
            # For now, use simple extraction
            summary = "LLM summarization not yet implemented. Using simple extraction."
            method = "placeholder"
        else:
            # Simple extractive summarization: first N sentences
            sentences = re.split(r'[.!?]+', text)
            summary = ""
            for sentence in sentences:
                if len(summary) + len(sentence) > max_length:
                    break
                summary += sentence.strip() + ". "
            method = "extractive"
        
        if not summary or summary == "LLM summarization not yet implemented. Using simple extraction.":
            # Fallback: just truncate
            summary = text[:max_length] + "..." if len(text) > max_length else text
            method = "truncation"
        
        result = {
            "original_length": len(text),
            "summary_length": len(summary),
            "summary": summary,
            "method": method,
            "compression_ratio": len(summary) / len(text) if len(text) > 0 else 0
        }
        
        logging.info(f"✅ Generated summary ({len(summary)} characters)")
        
        action_response = ActionResponse(
            success=True,
            message=result,
            metadata={"method": method}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
        
    except Exception as e:
        error_msg = f"Text summarization failed: {str(e)}"
        logging.error(f"Summarization error: {traceback.format_exc()}")
        
        action_response = ActionResponse(
            success=False,
            message=error_msg,
            metadata={"error_type": "summarization_error"}
        )
        
        return TextContent(
            type="text",
            text=json.dumps(action_response.model_dump())
        )
