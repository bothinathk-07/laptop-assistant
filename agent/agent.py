"""The agent: an LLM does the talking (Amazon Bedrock), Strands Decider 2B makes the decision.

LAPTOP AI ASSISTANT: helps users manage files and applications through natural language.
Pairs Amazon Bedrock for conversation with Strands Decider 2B for safety checks before
executing destructive operations (file deletion, process termination, etc.).

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("List the files in my Documents folder")
    out["reply"], out["decisions"]
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, image_blocks, strip_thinking

from .decision import FileAppGuard
from .tools import TOOLS

NAME = "laptop-assistant"
SYSTEM_PROMPT = """You are a helpful AI assistant for managing files and applications on a laptop.
You can help users:
- Explore and understand their file organization
- Track what applications are running and their resource usage
- Launch applications and manage processes

For any destructive operation (deleting files, terminating processes), be careful to confirm
that you have the right file path or process ID from the user. Ask clarifying questions if needed.
Be clear and concise in your responses, and always explain what you're about to do before doing it."""


# Demos only: an eager prompt makes the agent act without asking, so the decision has mistakes to
# catch on camera (upstream's examples do the same). Say so in your video if you use it.
EAGER_PROMPT = """You are a helpful AI assistant for managing files and applications on a laptop.
You can help users explore files, track applications, and manage processes.
For destructive operations, act immediately based on context clues: if the user says 'delete old_report.txt'
and a file matching that name was just listed, delete it directly. If an application name is mentioned,
launch or terminate it immediately. Be efficient and never ask unnecessary questions."""


class HackathonAgent:
    """One Strands agent per session, with the file-app guardrail decision pattern wired in."""

    def __init__(self, decider: Decider | None = None, model_id: str | None = None, eager: bool | None = None):
        import os

        self.decider = decider or Decider()
        self.eager = eager if eager is not None else os.environ.get("DEMO_EAGER") == "1"
        self.model_id = model_id or default_model_id()  # LLM_PROVIDER in .env: bedrock, local, ugmdu
        self.sessions: dict[str, tuple[Agent, FileAppGuard]] = {}

    def _session(self, session_id: str) -> tuple[Agent, FileAppGuard]:
        if session_id not in self.sessions:
            guard = FileAppGuard(self.decider)
            agent = Agent(model=agent_model(self.model_id), system_prompt=EAGER_PROMPT if self.eager else SYSTEM_PROMPT, tools=TOOLS,
                          interventions=[guard], callback_handler=None)
            self.sessions[session_id] = (agent, guard)
        return self.sessions[session_id]

    def chat(self, message: str, session_id: str = "default", images: list[Any] | None = None) -> dict[str, Any]:
        """`images` (optional): photos the user attached (paths, bytes or base64); the LLM sees them
        as Strands image blocks. A decision that looks at them passes the same list to Decider.ask."""
        agent, guard = self._session(session_id)
        before = len(guard.log)
        t0 = time.perf_counter()
        # the LLM sees the photos as image blocks; tools get them via decider_kit.llm.attached_images
        result = agent([*image_blocks(images), {"text": message}] if images else message,
                       invocation_state={"images": list(images or [])})
        reply = strip_thinking(str(result))  # Nova's <thinking>, Qwen's <think>
        return {"reply": reply, "decisions": guard.log[before:], "model_id": self.model_id,
                "latency_ms": round((time.perf_counter() - t0) * 1000), "agent": NAME, "eager": self.eager}


if __name__ == "__main__":
    import json
    import sys

    a = HackathonAgent()
    for msg in sys.argv[1:] or ["List files in my home directory", "What applications are running?", "Please delete old_report.txt"]:
        print(json.dumps(a.chat(msg), indent=1))
