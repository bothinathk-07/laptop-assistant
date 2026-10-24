"""Tests for conversation state tracking in agent.py

Verifies that:
1. Message history is preserved across multiple user messages in a session (Req 1.1, 1.2)
2. FileAppGuard can render the full conversation state for the Decider (Req 4.2)
3. State text includes both conversation context and proposed action details (Req 4.2)
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pytest

from agent.decision import FileAppGuard, QUESTIONS
from decider_kit import Decider
from decider_kit.patterns.guardrails import render_messages


class FakeDecider:
    """Mock Decider that returns preset answers."""
    
    def __init__(self, answers: dict[str, float] | None = None):
        """
        Args:
            answers: Dict mapping question names to p_yes values. Example:
                {"args_grounded": 0.9, "explicit_request": 0.8, "premature": 0.1}
        """
        self.answers = answers or {}
        self.last_latency_ms = 100
        self.last_state = None
        self.last_questions = None
    
    def ask(self, state: str, questions: dict) -> dict:
        """Mock Decider.ask that returns predetermined answers."""
        self.last_state = state
        self.last_questions = questions
        
        result = {}
        for key in questions:
            p_yes = self.answers.get(key, 0.5)
            result[key] = SimpleNamespace(
                p_yes=p_yes,
                confidence=0.8,
            )
        return result


class TestConversationStatePreservation:
    """Test that message history is preserved across multiple messages in a session."""
    
    def test_render_messages_formats_all_messages(self):
        """Test that render_messages includes all messages in conversation."""
        messages = [
            {"role": "user", "content": [{"text": "List files in Documents"}]},
            {"role": "assistant", "content": [{"text": "I found 3 files..."}]},
            {"role": "user", "content": [{"text": "Delete old_report.txt"}]},
        ]
        
        rendered = render_messages(messages)
        
        # All messages should be included
        assert "List files in Documents" in rendered
        assert "I found 3 files" in rendered
        assert "Delete old_report.txt" in rendered
        
        # Should have proper role labels
        assert "user:" in rendered
        assert "assistant:" in rendered
    
    def test_render_messages_respects_last_limit(self):
        """Test that render_messages respects the 'last' parameter."""
        messages = [
            {"role": "user", "content": [{"text": f"Message {i}"}]}
            for i in range(20)
        ]
        
        rendered_last_5 = render_messages(messages, last=5)
        
        # Should include only last 5 messages
        assert "Message 19" in rendered_last_5
        assert "Message 18" in rendered_last_5
        assert "Message 0" not in rendered_last_5  # Too old
    
    def test_render_messages_handles_empty_messages(self):
        """Test that render_messages handles empty message list gracefully."""
        rendered = render_messages([])
        assert "(no conversation yet)" in rendered


class TestGuardrailStateRendering:
    """Test that FileAppGuard renders complete state for Decider evaluation."""
    
    def test_guardrail_state_includes_conversation_and_action(self):
        """Test that guardrail check includes both conversation and proposed action in state."""
        fake_decider = FakeDecider({
            "args_grounded": 0.9,
            "explicit_request": 0.9,
            "premature": 0.1,
        })
        
        guard = FileAppGuard(fake_decider)
        
        # Create a mock event with conversation history and tool call
        event = SimpleNamespace(
            tool_use={
                "name": "delete_file",
                "input": {"path": "/home/user/old_report.txt"}
            },
            agent=SimpleNamespace(
                messages=[
                    {"role": "user", "content": [{"text": "list files in Documents"}]},
                    {"role": "assistant", "content": [{"text": "I found old_report.txt in Documents"}]},
                    {"role": "user", "content": [{"text": "please delete old_report.txt"}]},
                ]
            )
        )
        
        # Trigger guardrail check
        result = guard.before_tool_call(event)
        
        # Verify state was sent to Decider
        assert fake_decider.last_state is not None
        
        # State should include conversation section
        assert "--- CONVERSATION ---" in fake_decider.last_state
        assert "list files in Documents" in fake_decider.last_state
        assert "I found old_report.txt" in fake_decider.last_state
        assert "please delete old_report.txt" in fake_decider.last_state
        
        # State should include action section
        assert "--- PROPOSED ACTION ---" in fake_decider.last_state
        assert "delete_file" in fake_decider.last_state
        assert "/home/user/old_report.txt" in fake_decider.last_state
    
    def test_guardrail_evaluates_all_questions(self):
        """Test that FileAppGuard evaluates all required questions."""
        fake_decider = FakeDecider({
            "args_grounded": 0.9,
            "explicit_request": 0.9,
            "premature": 0.1,
        })
        
        guard = FileAppGuard(fake_decider)
        
        event = SimpleNamespace(
            tool_use={
                "name": "delete_file",
                "input": {"path": "/tmp/test.txt"}
            },
            agent=SimpleNamespace(
                messages=[
                    {"role": "user", "content": [{"text": "delete /tmp/test.txt"}]}
                ]
            )
        )
        
        guard.before_tool_call(event)
        
        # Verify all three questions were asked
        assert "args_grounded" in fake_decider.last_questions
        assert "explicit_request" in fake_decider.last_questions
        assert "premature" in fake_decider.last_questions
    
    def test_guardrail_records_decision_scores(self):
        """Test that guardrail records decision scores in log."""
        fake_decider = FakeDecider({
            "args_grounded": 0.85,
            "explicit_request": 0.92,
            "premature": 0.15,
        })
        
        guard = FileAppGuard(fake_decider)
        
        event = SimpleNamespace(
            tool_use={
                "name": "delete_file",
                "input": {"path": "/tmp/test.txt"}
            },
            agent=SimpleNamespace(
                messages=[
                    {"role": "user", "content": [{"text": "delete /tmp/test.txt"}]}
                ]
            )
        )
        
        guard.before_tool_call(event)
        
        # Check log entry
        assert len(guard.log) > 0
        last_entry = guard.log[-1]
        
        # Verify scores are recorded
        assert "args_grounded" in last_entry
        assert "explicit_request" in last_entry
        assert "premature" in last_entry
        assert last_entry["args_grounded"] > 0.8
        assert last_entry["explicit_request"] > 0.9
        assert last_entry["premature"] < 0.2
    
    def test_guardrail_accesses_multiple_messages(self):
        """Test that guardrail properly accesses message history across multiple turns."""
        fake_decider = FakeDecider({
            "args_grounded": 0.9,
            "explicit_request": 0.9,
            "premature": 0.1,
        })
        
        guard = FileAppGuard(fake_decider)
        
        # Simulate multi-turn conversation
        event = SimpleNamespace(
            tool_use={
                "name": "delete_file",
                "input": {"path": "/home/user/old_report.txt"}
            },
            agent=SimpleNamespace(
                messages=[
                    {"role": "user", "content": [{"text": "What files do I have?"}]},
                    {"role": "assistant", "content": [{"text": "You have report.txt, old_report.txt, notes.txt"}]},
                    {"role": "user", "content": [{"text": "Can I delete old_report.txt?"}]},
                    {"role": "assistant", "content": [{"text": "Yes, you can delete it if you don't need it."}]},
                    {"role": "user", "content": [{"text": "OK, delete old_report.txt now"}]},
                ]
            )
        )
        
        guard.before_tool_call(event)
        
        # All messages should be in the state sent to Decider
        state = fake_decider.last_state
        assert "What files do I have?" in state
        assert "report.txt" in state
        assert "Can I delete old_report.txt?" in state
        assert "OK, delete old_report.txt now" in state


class TestMessageHistoryAcrossSessions:
    """Test that message history is maintained per session (conceptual test)."""
    
    def test_guardrail_event_has_agent_messages(self):
        """Test that guardrail event object provides access to agent.messages."""
        # This is a structural test to verify the event contract
        event = SimpleNamespace(
            tool_use={"name": "test_tool", "input": {}},
            agent=SimpleNamespace(
                messages=[
                    {"role": "user", "content": [{"text": "test"}]}
                ]
            )
        )
        
        # FileAppGuard should be able to access this structure
        fake_decider = FakeDecider()
        guard = FileAppGuard(fake_decider)
        
        # This should not raise an exception
        try:
            messages = event.agent.messages
            rendered = render_messages(messages)
            assert "test" in rendered
        except (AttributeError, KeyError) as e:
            pytest.fail(f"Failed to access event.agent.messages: {e}")


class TestStateTextQuality:
    """Test that state text for Decider is well-formed and readable."""
    
    def test_state_text_has_clear_section_markers(self):
        """Test that state text has clear section markers for Decider."""
        fake_decider = FakeDecider()
        guard = FileAppGuard(fake_decider)
        
        event = SimpleNamespace(
            tool_use={
                "name": "delete_file",
                "input": {"path": "/tmp/file.txt"}
            },
            agent=SimpleNamespace(
                messages=[
                    {"role": "user", "content": [{"text": "delete /tmp/file.txt"}]}
                ]
            )
        )
        
        guard.before_tool_call(event)
        state = fake_decider.last_state
        
        # State should have clear structure
        assert "--- CONVERSATION ---" in state
        assert "--- PROPOSED ACTION ---" in state
        assert state.index("--- CONVERSATION ---") < state.index("--- PROPOSED ACTION ---")
    
    def test_state_text_includes_context_description(self):
        """Test that state text includes a description of the context."""
        fake_decider = FakeDecider()
        guard = FileAppGuard(fake_decider)
        
        event = SimpleNamespace(
            tool_use={
                "name": "delete_file",
                "input": {"path": "/tmp/file.txt"}
            },
            agent=SimpleNamespace(
                messages=[
                    {"role": "user", "content": [{"text": "delete /tmp/file.txt"}]}
                ]
            )
        )
        
        guard.before_tool_call(event)
        state = fake_decider.last_state
        
        # State should start with descriptive text
        assert "conversation" in state.lower()
        assert "laptop" in state.lower() or "assistant" in state.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
