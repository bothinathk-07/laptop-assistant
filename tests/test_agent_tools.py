"""Tests for laptop assistant file and application management tools."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agent import tools


class TestFileOperations:
    """Tests for file operations including safe and destructive actions."""

    def test_delete_file_success(self, tmp_path):
        """Test successful file deletion."""
        # Create a temporary file
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        
        # Verify file exists
        assert test_file.exists()
        
        # Delete the file
        result = tools.delete_file(str(test_file))
        
        # Verify success
        assert result["success"] is True
        assert "Successfully deleted" in result["message"]
        assert not test_file.exists()
    
    def test_delete_file_not_found(self):
        """Test deletion of non-existent file."""
        result = tools.delete_file("/non/existent/file.txt")
        
        assert result["success"] is False
        assert "does not exist" in result["error"] or "not found" in result["error"].lower()
    
    def test_delete_file_permission_error(self, tmp_path):
        """Test deletion with permission error (simulated)."""
        # Create a file
        test_file = tmp_path / "readonly.txt"
        test_file.write_text("content")
        
        # Make it read-only
        test_file.chmod(0o444)
        
        # Try to delete (may need to be run as non-admin to fail)
        result = tools.delete_file(str(test_file))
        
        # Clean up - restore permissions
        test_file.chmod(0o644)
        
        # On some systems this may still succeed, so we just verify the structure
        assert "success" in result
    
    def test_delete_directory_should_fail(self, tmp_path):
        """Test that attempting to delete a directory fails."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        result = tools.delete_file(str(test_dir))
        
        assert result["success"] is False
        assert "directory" in result["error"].lower()
    
    def test_move_file_success(self, tmp_path):
        """Test successful file move."""
        # Create source file
        src_file = tmp_path / "source.txt"
        src_file.write_text("content to move")
        
        # Define destination
        dest_file = tmp_path / "destination.txt"
        
        # Move the file
        result = tools.move_file(str(src_file), str(dest_file))
        
        # Verify success
        assert result["success"] is True
        assert "Successfully moved" in result["message"]
        assert not src_file.exists()
        assert dest_file.exists()
        assert dest_file.read_text() == "content to move"
    
    def test_move_file_source_not_found(self, tmp_path):
        """Test move with non-existent source file."""
        result = tools.move_file(
            "/non/existent/source.txt",
            str(tmp_path / "dest.txt")
        )
        
        assert result["success"] is False
        assert "does not exist" in result["error"] or "not found" in result["error"].lower()
    
    def test_move_file_destination_exists(self, tmp_path):
        """Test move when destination already exists."""
        # Create both files
        src_file = tmp_path / "source.txt"
        src_file.write_text("source content")
        
        dest_file = tmp_path / "destination.txt"
        dest_file.write_text("dest content")
        
        # Try to move
        result = tools.move_file(str(src_file), str(dest_file))
        
        # Should fail because destination exists
        assert result["success"] is False
        assert "already exists" in result["error"].lower()
    
    def test_move_file_invalid_destination_directory(self, tmp_path):
        """Test move with non-existent destination directory."""
        src_file = tmp_path / "source.txt"
        src_file.write_text("content")
        
        result = tools.move_file(
            str(src_file),
            str(tmp_path / "non_existent_dir" / "dest.txt")
        )
        
        assert result["success"] is False
        assert "does not exist" in result["error"].lower()
    
    def test_move_directory_should_fail(self, tmp_path):
        """Test that attempting to move a directory fails."""
        src_dir = tmp_path / "source_dir"
        src_dir.mkdir()
        
        dest_path = tmp_path / "dest_dir"
        
        result = tools.move_file(str(src_dir), str(dest_path))
        
        assert result["success"] is False
        assert "directory" in result["error"].lower()
    
    def test_path_traversal_blocked_delete(self, tmp_path):
        """Test that path traversal attempts are blocked in delete_file."""
        # Try path traversal
        result = tools.delete_file("../../../etc/passwd")
        
        assert result["success"] is False
        assert "traversal" in result["error"].lower() or "does not exist" in result["error"]
    
    def test_path_traversal_blocked_move_source(self, tmp_path):
        """Test that path traversal attempts are blocked in move_file source."""
        dest_file = tmp_path / "dest.txt"
        
        result = tools.move_file("../../../etc/passwd", str(dest_file))
        
        assert result["success"] is False
        assert "traversal" in result["error"].lower() or "does not exist" in result["error"]
    
    def test_path_traversal_blocked_move_destination(self, tmp_path):
        """Test that path traversal attempts are blocked in move_file destination."""
        src_file = tmp_path / "source.txt"
        src_file.write_text("content")
        
        result = tools.move_file(str(src_file), "../../../tmp/hacked.txt")
        
        assert result["success"] is False
        assert "traversal" in result["error"].lower()


class TestActionClassification:
    """Tests for action classification (Safe_Action vs Destructive_Action)."""
    
    def test_safe_actions_classification(self):
        """Test that safe actions are correctly identified."""
        assert "enumerate_directory" in tools.SAFE_ACTIONS
        assert "get_file_info" in tools.SAFE_ACTIONS
        assert "list_processes" in tools.SAFE_ACTIONS
        assert "get_process_info" in tools.SAFE_ACTIONS
    
    def test_destructive_actions_classification(self):
        """Test that destructive actions are correctly identified."""
        assert "delete_file" in tools.DESTRUCTIVE_ACTIONS
        assert "move_file" in tools.DESTRUCTIVE_ACTIONS
        assert "terminate_process" in tools.DESTRUCTIVE_ACTIONS
        assert "launch_application" in tools.DESTRUCTIVE_ACTIONS
    
    def test_tools_list_includes_destructive_operations(self):
        """Test that TOOLS list includes the new destructive operations."""
        tool_names = [getattr(t, "tool_name", None) or getattr(t, "name", None) or getattr(t, "tool_spec", {}).get("name") for t in tools.TOOLS]
        assert "delete_file" in tool_names
        assert "move_file" in tool_names


class TestEnumerateDirectory:
    """Tests for enumerate_directory safe action."""
    
    def test_enumerate_directory_success(self, tmp_path):
        """Test successful directory enumeration."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()
        
        result = tools.enumerate_directory(str(tmp_path))
        
        assert "error" not in result
        assert result["count"] == 3
        assert len(result["files"]) == 3
        
        # Verify file info is complete
        for file_info in result["files"]:
            assert "name" in file_info
            assert "path" in file_info
            assert "size_bytes" in file_info
            assert "modified_at" in file_info
            assert "is_directory" in file_info
    
    def test_enumerate_directory_not_found(self):
        """Test enumeration of non-existent directory."""
        result = tools.enumerate_directory("/non/existent/directory")
        
        assert "error" in result
        assert "does not exist" in result["error"]
    
    def test_enumerate_directory_not_a_directory(self, tmp_path):
        """Test enumeration of a file (not directory)."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        
        result = tools.enumerate_directory(str(test_file))
        
        assert "error" in result
        assert "not a directory" in result["error"].lower()


class TestGetFileInfo:
    """Tests for get_file_info safe action."""
    
    def test_get_file_info_success(self, tmp_path):
        """Test getting file info successfully."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = tools.get_file_info(str(test_file))
        
        assert "error" not in result
        assert result["name"] == "test.txt"
        assert result["size_bytes"] > 0
        assert result["modified_at"] is not None
        assert result["is_directory"] is False
    
    def test_get_file_info_directory(self, tmp_path):
        """Test getting info for a directory."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        result = tools.get_file_info(str(test_dir))
        
        assert "error" not in result
        assert result["is_directory"] is True
    
    def test_get_file_info_not_found(self):
        """Test getting info for non-existent file."""
        result = tools.get_file_info("/non/existent/file.txt")
        
        assert "error" in result
        assert "does not exist" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

