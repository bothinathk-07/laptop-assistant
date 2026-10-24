"""Unit tests for action classifier.

Tests the classification of file and application operations into Safe_Action and
Destructive_Action categories per the design document specification.
"""

import pytest

from agent.classifier import DESTRUCTIVE_ACTIONS, SAFE_ACTIONS, ActionType, classify_action


class TestActionClassifier:
    """Test suite for action classification."""

    def test_safe_actions_classified_correctly(self):
        """Test that all defined safe actions are classified as Safe_Action."""
        for tool_name in SAFE_ACTIONS:
            result = classify_action(tool_name)
            assert result == "Safe_Action", f"{tool_name} should be classified as Safe_Action"

    def test_destructive_actions_classified_correctly(self):
        """Test that all defined destructive actions are classified as Destructive_Action."""
        for tool_name in DESTRUCTIVE_ACTIONS:
            result = classify_action(tool_name)
            assert result == "Destructive_Action", f"{tool_name} should be classified as Destructive_Action"

    def test_enumerate_directory_is_safe(self):
        """Test that enumerate_directory is classified as Safe_Action."""
        assert classify_action("enumerate_directory") == "Safe_Action"

    def test_get_file_info_is_safe(self):
        """Test that get_file_info is classified as Safe_Action."""
        assert classify_action("get_file_info") == "Safe_Action"

    def test_list_processes_is_safe(self):
        """Test that list_processes is classified as Safe_Action."""
        assert classify_action("list_processes") == "Safe_Action"

    def test_get_process_info_is_safe(self):
        """Test that get_process_info is classified as Safe_Action."""
        assert classify_action("get_process_info") == "Safe_Action"

    def test_delete_file_is_destructive(self):
        """Test that delete_file is classified as Destructive_Action."""
        assert classify_action("delete_file") == "Destructive_Action"

    def test_move_file_is_destructive(self):
        """Test that move_file is classified as Destructive_Action."""
        assert classify_action("move_file") == "Destructive_Action"

    def test_terminate_process_is_destructive(self):
        """Test that terminate_process is classified as Destructive_Action."""
        assert classify_action("terminate_process") == "Destructive_Action"

    def test_launch_application_is_destructive(self):
        """Test that launch_application is classified as Destructive_Action."""
        assert classify_action("launch_application") == "Destructive_Action"

    def test_unknown_tool_treated_as_destructive(self):
        """Test that unknown tools are classified as Destructive_Action for safety."""
        unknown_tools = [
            "unknown_tool",
            "random_operation",
            "undefined_action",
            "",
            "some_new_tool",
        ]
        for tool_name in unknown_tools:
            result = classify_action(tool_name)
            assert result == "Destructive_Action", f"Unknown tool '{tool_name}' should default to Destructive_Action"

    def test_safe_and_destructive_sets_are_disjoint(self):
        """Test that SAFE_ACTIONS and DESTRUCTIVE_ACTIONS have no overlap."""
        overlap = SAFE_ACTIONS.intersection(DESTRUCTIVE_ACTIONS)
        assert len(overlap) == 0, f"SAFE_ACTIONS and DESTRUCTIVE_ACTIONS must be disjoint, found overlap: {overlap}"

    def test_safe_actions_contain_all_specified_tools(self):
        """Test that SAFE_ACTIONS contains exactly the four specified tools from requirements."""
        expected = {
            "enumerate_directory",
            "get_file_info",
            "list_processes",
            "get_process_info",
        }
        assert SAFE_ACTIONS == expected, f"SAFE_ACTIONS should contain exactly {expected}"

    def test_destructive_actions_contain_all_specified_tools(self):
        """Test that DESTRUCTIVE_ACTIONS contains exactly the four specified tools from requirements."""
        expected = {
            "delete_file",
            "move_file",
            "terminate_process",
            "launch_application",
        }
        assert DESTRUCTIVE_ACTIONS == expected, f"DESTRUCTIVE_ACTIONS should contain exactly {expected}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
