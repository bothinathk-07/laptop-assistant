"""REUSABLE DECISION PATTERN: file and app operation guardrail  (#guardrails)

What it does
    Before the laptop assistant runs a tool that modifies files or applications (delete, move,
    terminate, launch), Strands Decider 2B checks the call against the conversation:
    - are the arguments grounded in what the user said or in earlier tool results (no invented
      file paths or process IDs)?
    - does the user clearly ask for this action now, rather than asking about it?
    - is it premature (should the assistant confirm first)?
    Grounded and requested calls run; otherwise the agent is sent back to ask (`Guide`), or a
    human confirms (`Confirm`) when the decider is unsure.

Typed questions and options
    args_grounded (noul), explicit_request (noul), premature (noul); see QUESTIONS below.

Wiring
    `FileAppGuard` is a Strands `InterventionHandler`; agent/agent.py passes it to the Agent:
        Agent(..., interventions=[FileAppGuard(decider)])
    It only inspects tools in DESTRUCTIVE_TOOLS; read-only tools run untouched. If the agent
    retries a call that was just sent back, unchanged, the retry is denied (Strands requires
    guide handlers to converge).

How to reuse it
    Copy this file, change DESTRUCTIVE_TOOLS to your irreversible operations, and reword the
    three questions for your domain. The pattern is domain-agnostic: it accepts arbitrary
    conversation state and proposed actions without coupling to specific tool implementations.
    Thresholds and decision logic are in `before_tool_call`. This same pattern works for
    databases, cloud resources, or any domain where operations need grounding checks.

Built with the AWS User Group Madurai Strands Decider hackathon kit
"""

from __future__ import annotations

import json
from typing import Any

from strands.interventions import Confirm, Deny, Guide, InterventionHandler, Proceed

from decider_kit import Decider
from decider_kit.patterns.guardrails import render_messages

PATTERN_TAG = "#guardrails"
DESTRUCTIVE_TOOLS = {"delete_file", "move_file", "terminate_process", "launch_application"}

QUESTIONS = {
    "args_grounded": Decider.noul(
        "Are all arguments in the proposed action stated by the user or returned by an earlier operation?",
        {"true": "every argument comes from the user's words or a prior tool result",
         "false": "an argument was guessed or invented"}),
    "explicit_request": Decider.noul(
        "Is the user's latest message an instruction to perform this action now, rather than a question about it?",
        {"true": "an instruction such as 'delete file.txt' or 'kill that process'",
         "false": "a question ('can I...?', 'what happens if...?'), a complaint, or exploration"}),
    "premature": Decider.noul(
        "Should the assistant confirm details with the user before taking this action?",
        {"true": "something is ambiguous or unconfirmed; ask first",
         "false": "everything needed is confirmed"}),
}


class FileAppGuard(InterventionHandler):
    name = "file-app-guard"

    def __init__(self, decider: Decider, yes: float = 0.5, unsure_band: tuple[float, float] = (0.35, 0.65)):
        self.decider, self.yes, self.unsure_band = decider, yes, unsure_band
        self.log: list[dict[str, Any]] = []
        self._guided: set[str] = set()  # calls already sent back; a retry of the same call is denied

    def before_invocation(self, event, **kwargs):
        self._guided.clear()  # a new user message: guided calls may now be justified
        return Proceed()

    def before_tool_call(self, event, **kwargs):
        name = event.tool_use["name"]
        if name not in DESTRUCTIVE_TOOLS:
            return Proceed()
        
        args = event.tool_use.get("input") or {}
        sig = f"{name}:{json.dumps(args, sort_keys=True)}"
        
        if sig in self._guided:  # Guide must converge: the same call again, unchanged, is refused
            self.log.append({
                "pattern": PATTERN_TAG,
                "tool": name,
                "args": args,
                "verdict": "deny",
                "reason": "retried a guided call"
            })
            return Deny(reason="This exact action was already rejected. Ask the user for the missing details instead.")
        
        # Render conversation state and proposed action for Decider
        state = (
            "A conversation between a user and an AI assistant that manages files and applications, "
            "then a tool call the assistant wants to make.\n\n"
            f"--- CONVERSATION ---\n{render_messages(event.agent.messages)}\n\n"
            f"--- PROPOSED ACTION ---\ntool: {name}\narguments: {json.dumps(args)}"
        )
        
        a = self.decider.ask(state, QUESTIONS)
        g, e, p = (a[k].p_yes or 0.0 for k in ("args_grounded", "explicit_request", "premature"))
        confidence = a["args_grounded"].confidence or 0.0
        
        rec = {
            "pattern": PATTERN_TAG,
            "tool": name,
            "args": args,
            "args_grounded": round(g, 3),
            "explicit_request": round(e, 3),
            "premature": round(p, 3),
            "confidence": round(confidence, 3),
            "decider_ms": round(self.decider.last_latency_ms or 0)
        }
        
        lo, hi = self.unsure_band
        
        # Decision thresholds per design document
        if g < self.yes:
            rec["verdict"] = "guide"
            rec["reason"] = "arguments not grounded"
            action = Guide(feedback="Do not guess file paths or process IDs. Ask the user or list them first.")
        elif e < self.yes:
            rec["verdict"] = "guide"
            rec["reason"] = "not an explicit request"
            action = Guide(feedback="The user has not asked for this action. Answer their question instead.")
        elif confidence < 0.65:  # Low confidence threshold from design
            rec["verdict"] = "confirm"
            rec["reason"] = "low confidence"
            action = Confirm(
                prompt=f"Approve {name} {json.dumps(args)}? (confidence: {confidence:.2f})",
                response="yes"
            )
        elif p > self.yes:
            rec["verdict"] = "guide"
            rec["reason"] = "premature action"
            action = Guide(feedback="Confirm the details with the user before taking this action.")
        else:
            rec["verdict"] = "proceed"
            action = Proceed()
        
        if rec["verdict"] == "guide":
            self._guided.add(sig)
        
        self.log.append(rec)
        return action
