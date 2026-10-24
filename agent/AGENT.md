# Use case

- **Pitch:** a laptop AI assistant that helps users manage files and applications through natural language conversation, with safety guardrails that prevent accidental destructive actions.
- **Who it is for:** laptop owners who want to manage their files, track application usage, and control running processes without remembering complex commands or accidentally damaging their system.
- **Features:**
  - file tracking and organization feedback through natural language conversation;
  - application management with process monitoring and control;
  - every destructive action (file deletion, file moves, process termination) is checked before it runs, and low-confidence cases require human confirmation;
  - fast read-only operations (file enumeration, process listing) execute without guardrail overhead;
  - deployed on Amazon Bedrock AgentCore Runtime.
- **The decision handed to Strands Decider 2B:** before a destructive file or application operation, is it grounded in the conversation (no guessed paths/PIDs) and explicitly requested by the user (not just a question)? (`#guardrails`)
- **Why a decision model:** the guardrail check runs on every destructive action, so it must be fast, cheap and private, and it must return calibrated confidence scores the code can branch on.
- **Amazon Bedrock:** the conversation and tool use (Amazon Nova Pro by default).
