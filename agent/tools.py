"""Laptop AI Assistant tools: file and application management with guardrail safety checks.

Safe_Action tools (enumerate_directory, get_file_info, list_processes, get_process_info) execute without guardrail checks.
Destructive_Action tools (delete_file, move_file, terminate_process, launch_application) require guardrail evaluation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
from strands import tool


@dataclass
class FileInfo:
    """File metadata returned by file operations."""
    name: str
    path: str
    size_bytes: int
    modified_at: str  # ISO 8601 format
    is_directory: bool


@dataclass
class ProcessInfo:
    """Process information returned by process operations."""
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    status: str


def validate_path(path: str) -> tuple[bool, str, Path]:
    """
    Validate a file path to prevent path traversal attacks.
    
    Returns:
        (is_valid, error_message, resolved_path)
    """
    try:
        # Resolve to absolute path
        resolved = Path(path).resolve()
        
        # Check if path exists
        if not resolved.exists():
            return False, f"Path does not exist: {path}", resolved
        
        # Security check: detect path traversal attempts
        # Ensure resolved path doesn't escape via symlinks or .. sequences
        try:
            # Check if the path contains suspicious patterns
            path_str = str(resolved)
            if ".." in Path(path).parts:
                return False, f"Path traversal detected: {path}", resolved
        except (ValueError, OSError):
            return False, f"Invalid path: {path}", resolved
            
        return True, "", resolved
        
    except (OSError, ValueError, RuntimeError) as e:
        return False, f"Invalid path: {e}", Path()


@tool
def enumerate_directory(path: str) -> dict[str, Any]:
    """List all files and directories in the specified path (Safe_Action)."""
    is_valid, error_msg, resolved_path = validate_path(path)
    
    if not is_valid:
        return {"error": error_msg}
    
    if not resolved_path.is_dir():
        return {"error": f"Path is not a directory: {path}"}
    
    try:
        files: list[dict] = []
        for entry in resolved_path.iterdir():
            try:
                stat = entry.stat()
                file_info = FileInfo(
                    name=entry.name,
                    path=str(entry),
                    size_bytes=stat.st_size,
                    modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    is_directory=entry.is_dir()
                )
                files.append(asdict(file_info))
            except (OSError, PermissionError):
                # Skip files we can't read
                continue
        
        return {
            "directory": str(resolved_path),
            "files": files,
            "count": len(files)
        }
        
    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except OSError as e:
        return {"error": f"Could not read directory: {e}"}


@tool
def get_file_info(path: str) -> dict[str, Any]:
    """Get detailed information about a specific file or directory (Safe_Action)."""
    is_valid, error_msg, resolved_path = validate_path(path)
    
    if not is_valid:
        return {"error": error_msg}
    
    try:
        stat = resolved_path.stat()
        file_info = FileInfo(
            name=resolved_path.name,
            path=str(resolved_path),
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            is_directory=resolved_path.is_dir()
        )
        return asdict(file_info)
        
    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except OSError as e:
        return {"error": f"Could not read file info: {e}"}


@tool
def list_processes() -> dict[str, Any]:
    """List all running processes with their resource usage information (Safe_Action)."""
    try:
        processes: list[dict] = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
            try:
                info = proc.info
                process_info = ProcessInfo(
                    pid=info['pid'],
                    name=info['name'] or "Unknown",
                    cpu_percent=info['cpu_percent'] or 0.0,
                    memory_mb=round(info['memory_info'].rss / 1024 / 1024, 2) if info['memory_info'] else 0.0,
                    status=info['status'] or "unknown"
                )
                processes.append(asdict(process_info))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Skip processes that disappeared or we can't access
                continue
        
        return {
            "processes": processes,
            "count": len(processes)
        }
        
    except Exception as e:
        return {"error": f"Failed to list processes: {str(e)}"}


@tool
def get_process_info(pid: int) -> dict[str, Any]:
    """Get detailed information about a specific process by its PID (Safe_Action)."""
    try:
        proc = psutil.Process(pid)
        with proc.oneshot():
            process_info = ProcessInfo(
                pid=proc.pid,
                name=proc.name(),
                cpu_percent=proc.cpu_percent(interval=0.1),
                memory_mb=round(proc.memory_info().rss / 1024 / 1024, 2),
                status=proc.status()
            )
            return asdict(process_info)
            
    except psutil.NoSuchProcess:
        return {"error": f"No process found with PID {pid}"}
    except psutil.AccessDenied:
        return {"error": f"Access denied to process {pid}"}
    except Exception as e:
        return {"error": f"Failed to get process info: {str(e)}"}


@tool
def launch_application(name: str) -> dict[str, Any]:
    """Launch an application by name (Destructive_Action).
    
    Args:
        name: The application name to launch
        
    Returns:
        Dict with launch status or error message
    """
    import subprocess
    import platform
    
    try:
        system = platform.system()
        
        if system == "Windows":
            # Windows: use start command
            result = subprocess.Popen(
                ["cmd", "/c", "start", "", name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            # Give it a moment to launch
            try:
                result.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Process started successfully and is still running
                pass
            
            return {
                "status": "launched",
                "application": name,
                "message": f"Application '{name}' launch initiated"
            }
            
        elif system == "Darwin":
            # macOS: use open command
            result = subprocess.Popen(
                ["open", "-a", name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            result.wait(timeout=2)
            
            if result.returncode == 0:
                return {
                    "status": "launched",
                    "application": name,
                    "message": f"Application '{name}' launched successfully"
                }
            else:
                stderr = result.stderr.read().decode() if result.stderr else ""
                return {"error": f"Failed to launch '{name}': {stderr}"}
            
        else:
            # Linux: try xdg-open or direct execution
            try:
                result = subprocess.Popen(
                    ["xdg-open", name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                result.wait(timeout=2)
                return {
                    "status": "launched",
                    "application": name,
                    "message": f"Application '{name}' launch initiated"
                }
            except FileNotFoundError:
                # xdg-open not available, try direct execution
                result = subprocess.Popen(
                    [name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                return {
                    "status": "launched",
                "application": name,
                    "message": f"Application '{name}' launch initiated"
                }
        
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout launching application '{name}'"}
    except FileNotFoundError:
        return {"error": f"Application '{name}' not found"}
    except PermissionError:
        return {"error": f"Permission denied to launch '{name}'"}
    except Exception as e:
        return {"error": f"Failed to launch application: {str(e)}"}


# Configurable block list for system-critical processes
# These processes cannot be terminated even with user confirmation
SYSTEM_CRITICAL_PROCESSES = {
    # Windows system processes
    "System", "csrss.exe", "wininit.exe", "services.exe", "lsass.exe", 
    "winlogon.exe", "smss.exe", "svchost.exe",
    # macOS system processes
    "kernel_task", "launchd", "WindowServer", "loginwindow",
    # Linux system processes
    "systemd", "init", "kthreadd", "Xorg", "gdm", "lightdm",
    # Common across platforms
    "pid1", "kernel"
}


def is_system_critical(process_name: str, pid: int) -> bool:
    """Check if a process is system-critical and should not be terminated.
    
    Args:
        process_name: The name of the process
        pid: The process ID
        
    Returns:
        True if process is system-critical, False otherwise
    """
    # PID 0 and 1 are always critical
    if pid <= 1:
        return True
    
    # Check against known critical process names
    process_name_lower = process_name.lower()
    for critical in SYSTEM_CRITICAL_PROCESSES:
        if critical.lower() in process_name_lower:
            return True
    
    return False


@tool
def terminate_process(pid: int) -> dict[str, Any]:
    """Terminate a process by PID (Destructive_Action).
    
    Args:
        pid: The process ID to terminate
        
    Returns:
        Dict with termination status or error message
    """
    try:
        # Check if process exists and get its name
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
        except psutil.NoSuchProcess:
            return {"error": f"No process found with PID {pid}"}
        except psutil.AccessDenied:
            return {"error": f"Access denied to process {pid}"}
        
        # Check if process is system-critical
        if is_system_critical(process_name, pid):
            return {
                "error": f"Cannot terminate system-critical process '{process_name}' (PID {pid})",
                "reason": "Process is on the system-critical block list"
            }
        
        # Attempt graceful termination first
        try:
            proc.terminate()
            # Wait up to 3 seconds for graceful termination
            proc.wait(timeout=3)
            
            return {
                "status": "terminated",
                "pid": pid,
                "process_name": process_name,
                "method": "graceful",
                "message": f"Process '{process_name}' (PID {pid}) terminated successfully"
            }
            
        except psutil.TimeoutExpired:
            # Graceful termination timed out, force kill
            proc.kill()
            proc.wait(timeout=2)
            
            return {
                "status": "terminated",
                "pid": pid,
                "process_name": process_name,
                "method": "forced",
                "message": f"Process '{process_name}' (PID {pid}) force-killed after graceful termination timeout"
            }
        
    except psutil.NoSuchProcess:
        return {"error": f"Process {pid} no longer exists"}
    except psutil.AccessDenied:
        return {"error": f"Permission denied to terminate process {pid}. Try running with administrator/root privileges."}
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout terminating process {pid}"}
    except Exception as e:
        return {"error": f"Failed to terminate process: {str(e)}"}


@tool
def delete_file(path: str) -> dict[str, Any]:
    """Delete a file at the specified path (Destructive_Action).
    
    Args:
        path: The path to the file to delete
        
    Returns:
        Dict with success status or error message
    """
    is_valid, error_msg, resolved_path = validate_path(path)
    
    if not is_valid:
        return {"error": error_msg, "success": False}
    
    if resolved_path.is_dir():
        return {"error": f"Path is a directory, not a file: {path}", "success": False}
    
    try:
        resolved_path.unlink()
        return {
            "success": True,
            "message": f"Successfully deleted file: {path}",
            "path": str(resolved_path)
        }
        
    except PermissionError:
        return {"error": f"Permission denied: {path}", "success": False}
    except FileNotFoundError:
        return {"error": f"File not found: {path}", "success": False}
    except OSError as e:
        return {"error": f"Failed to delete file: {e}", "success": False}


@tool
def move_file(src: str, dest: str) -> dict[str, Any]:
    """Move a file from source path to destination path (Destructive_Action).
    
    Args:
        src: The source file path to move
        dest: The destination file path
        
    Returns:
        Dict with success status or error message
    """
    # Validate source path
    is_valid_src, error_msg_src, resolved_src = validate_path(src)
    
    if not is_valid_src:
        return {"error": f"Source path error: {error_msg_src}", "success": False}
    
    if resolved_src.is_dir():
        return {"error": f"Source path is a directory, not a file: {src}", "success": False}
    
    # Validate and resolve destination path (may not exist yet)
    try:
        # For destination, we need to validate the parent directory exists
        dest_path = Path(dest).resolve()
        
        # Check for path traversal in destination
        if ".." in Path(dest).parts:
            return {"error": f"Path traversal detected in destination: {dest}", "success": False}
        
        # Ensure parent directory exists
        if not dest_path.parent.exists():
            return {"error": f"Destination directory does not exist: {dest_path.parent}", "success": False}
        
    except (OSError, ValueError, RuntimeError) as e:
        return {"error": f"Invalid destination path: {e}", "success": False}
    
    try:
        # Check if destination already exists
        if dest_path.exists():
            return {
                "error": f"Destination file already exists: {dest}",
                "success": False
            }
        
        # Perform the move operation
        resolved_src.rename(dest_path)
        
        return {
            "success": True,
            "message": f"Successfully moved file from {src} to {dest}",
            "source": str(resolved_src),
            "destination": str(dest_path)
        }
        
    except PermissionError:
        return {"error": f"Permission denied when moving file", "success": False}
    except FileNotFoundError:
        return {"error": f"Source file not found: {src}", "success": False}
    except OSError as e:
        return {"error": f"Failed to move file: {e}", "success": False}


# Action classification for guardrail system
SAFE_ACTIONS = {
    "enumerate_directory",
    "get_file_info",
    "list_processes",
    "get_process_info"
}

DESTRUCTIVE_ACTIONS = {
    "delete_file",
    "move_file",
    "terminate_process",
    "launch_application"
}

TOOLS = [
    enumerate_directory, 
    get_file_info, 
    list_processes, 
    get_process_info,
    delete_file,
    move_file,
    terminate_process,
    launch_application
]
