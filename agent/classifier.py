"""Action classification for laptop assistant guardrail pattern.

This module classifies file and application operations into Safe_Action (read-only) and
Destructive_Action (modifying) categories. Safe actions bypass guardrail checks and execute
directly, while destructive actions trigger Strands Decider 2B evaluation before execution.

Built with the AWS User Group Madurai Strands Decider hackathon kit
"""

from __future__ import annotations

from typing import Literal

ActionType = Literal["Safe_Action", "Destructive_Action"]

# Safe operations that only read information without modifying system state
SAFE_ACTIONS = {
    "enumerate_directory",
    "get_file_info",
    "list_processes",
    "get_process_info",
}

# Destructive operations that modify or delete files, or terminate running applications
DESTRUCTIVE_ACTIONS = {
    "delete_file",
    "move_file",
    "terminate_process",
    "launch_application",
}


def classify_action(tool_name: str) -> ActionType:
    """Classify a tool as Safe_Action or Destructive_Action.
    
    Safe actions are read-only operations that do not modify system state. They execute
    without guardrail checks for fast information retrieval.
    
    Destructive actions modify or delete files, or control running applications. They
    trigger guardrail evaluation by Strands Decider 2B before execution.
    
    Args:
        tool_name: The name of the tool to classify
        
    Returns:
        "Safe_Action" if the tool is read-only, "Destructive_Action" if it modifies state.
        Unknown tools are treated as destructive for safety.
        
    Examples:
        >>> classify_action("enumerate_directory")
        'Safe_Action'
        >>> classify_action("delete_file")
        'Destructive_Action'
        >>> classify_action("unknown_tool")
        'Destructive_Action'
    """
    if tool_name in SAFE_ACTIONS:
        return "Safe_Action"
    elif tool_name in DESTRUCTIVE_ACTIONS:
        return "Destructive_Action"
    else:
        # Unknown tools treated as destructive for safety
        return "Destructive_Action"
