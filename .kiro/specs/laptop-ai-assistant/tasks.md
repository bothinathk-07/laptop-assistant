# Implementation Plan: Laptop AI Assistant

## Overview

This implementation plan creates a hackathon submission agent that helps users manage files and applications on their laptop through natural language conversation. The agent uses Strands Decider 2B for guardrail checks (tagged `#guardrails`) before executing destructive operations, paired with Amazon Bedrock for natural language understanding. The implementation follows the hackathon kit structure with all required components: decision.py, tools.py, agent.py, eval_cases.jsonl, and demo_script.yaml.

## Tasks

- [x] 1. Set up agent core structure and decision pattern module
  - [x] 1.1 Create decision.py with reusable guardrail pattern
    - Define PATTERN_TAG as "guardrails"
    - Define QUESTIONS dictionary with three typed Decider questions (args_grounded, explicit_request, premature)
    - Implement FileAppGuard intervention handler with before_tool_call logic
    - Add docstring labeled "REUSABLE DECISION PATTERN:" describing the pattern and reusability
    - Remove IS_KIT_EXAMPLE flag if present
    - _Requirements: 6.3, 6.4, 8.2, 8.3, 8.4, 4.1, 4.2, 4.5, 4.6_

  - [ ]* 1.2 Write property test for decision module generality
    - **Property 15: Decision Module Generality**
    - **Validates: Requirements 8.5**
    - Test that arbitrary state strings and action dictionaries are accepted without hardcoded tool dependencies

- [x] 2. Implement file operations tools
  - [x] 2.1 Create file enumeration and information tools in tools.py
    - Implement @tool enumerate_directory(path: str) returning list of FileInfo
    - Implement @tool get_file_info(path: str) returning single FileInfo with name, size, modified_at
    - Add path validation to prevent path traversal attacks
    - Mark tools as Safe_Action operations
    - _Requirements: 2.1, 2.2, 2.4, 5.1_

  - [ ]* 2.2 Write property tests for file operations
    - **Property 2: File Enumeration Completeness**
    - **Validates: Requirements 2.1**
    - **Property 3: File Information Completeness**
    - **Validates: Requirements 2.2**
    - **Property 4: Path Boundary Enforcement**
    - **Validates: Requirements 2.4**
    - Test with generated directory structures (minimum 100 iterations)

  - [x] 2.3 Implement destructive file operations
    - Implement @tool delete_file(path: str) with Result return type
    - Implement @tool move_file(src: str, dest: str) with Result return type
    - Mark tools as Destructive_Action operations
    - Add error handling for PermissionError, FileNotFoundError
    - _Requirements: 4.1_

- [ ] 3. Implement application management tools
  - [x] 3.1 Create process information tools using psutil
    - Implement @tool list_processes() returning list of ProcessInfo (pid, name, cpu_percent, memory_mb, status)
    - Implement @tool get_process_info(pid: int) returning single ProcessInfo
    - Mark tools as Safe_Action operations
    - _Requirements: 3.1, 3.2, 5.1_

  - [ ]* 3.2 Write property test for process information
    - **Property 5: Process Information Completeness**
    - **Validates: Requirements 3.2**
    - Test that all ProcessInfo entries have non-null name and resource usage fields

  - [x] 3.3 Implement application control operations
    - Implement @tool launch_application(name: str) as Destructive_Action
    - Implement @tool terminate_process(pid: int) as Destructive_Action
    - Add configurable block list for system-critical processes
    - Add error handling with timeout support
    - _Requirements: 3.3, 3.4, 4.1_

- [x] 4. Checkpoint - Ensure all tools and decision module work independently
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Integrate guardrail decision into agent conversation loop
  - [x] 5.1 Wire FileAppGuard intervention handler into HackathonAgent
    - Create HackathonAgent class in agent.py with chat(message, session_id) method
    - Build Strands Agent with file and app tools using decider_kit.llm.agent_model
    - Register FileAppGuard handler to intercept tool calls
    - Implement decision logic: check action classification, invoke Decider for Destructive_Actions
    - _Requirements: 4.1, 4.2, 6.1, 6.2_

  - [x] 5.2 Implement confidence-based decision routing
    - Add logic for high confidence (≥ 0.65) proceed verdict
    - Add logic for low confidence (< 0.65) confirm verdict with user approval request
    - Add logic for guide verdict with denial explanation
    - Return decisions list with probabilities, verdict, and decider_ms timing
    - _Requirements: 4.5, 4.6, 7.1, 7.2, 7.3, 7.4_

  - [ ]* 5.3 Write property tests for guardrail invocation
    - **Property 6: Guardrail Invocation for Destructive Actions**
    - **Validates: Requirements 4.1**
    - **Property 7: Guardrail Context Completeness**
    - **Validates: Requirements 4.2**
    - **Property 11: Safe Actions Bypass Guardrails**
    - **Validates: Requirements 5.2**
    - Test with mock tool calls classified as Safe_Action and Destructive_Action

  - [ ]* 5.4 Write property tests for decision verdicts
    - **Property 8: High Confidence Proceed**
    - **Validates: Requirements 4.5**
    - **Property 9: Low Confidence Confirmation**
    - **Validates: Requirements 4.6, 7.1**
    - Test with generated guardrail results with varied confidence scores (minimum 100 iterations)

- [x] 6. Implement conversation context management
  - [x] 6.1 Add conversation state tracking in agent.py
    - Maintain message history within session using session_id
    - Format conversation context for guardrail state rendering
    - Implement state text generation that includes conversation + proposed action
    - _Requirements: 1.1, 1.2, 4.2_

  - [ ]* 6.2 Write property test for context preservation
    - **Property 1: Context Preservation Across Messages**
    - **Validates: Requirements 1.2**
    - Test with generated message sequences that agent processes message N with access to messages 1 through N-1

  - [x] 6.3 Implement user-friendly response formatting
    - Format file and process information clearly in agent responses
    - Format confirmation requests with confidence scores and action details
    - Format denial explanations with reasons and guidance
    - _Requirements: 1.4, 10.1, 10.3, 10.4_

  - [ ]* 6.4 Write property tests for response content
    - **Property 13: Confirmation Includes Confidence Score**
    - **Validates: Requirements 7.2**
    - **Property 14: Rejection Cancels Execution**
    - **Validates: Requirements 7.4**
    - **Property 17: Denial Includes Explanation**
    - **Validates: Requirements 10.1**
    - **Property 18: Confirmation Includes Action Details**
    - **Validates: Requirements 10.3**

- [x] 7. Create evaluation cases for benchmarking
  - [x] 7.1 Write eval_cases.jsonl with tune and test splits
    - Create explicit delete/terminate requests with grounded arguments
    - Create ambiguous requests requiring confirmation
    - Create safe information requests (list files, show processes)
    - Create ungrounded requests with invented file paths
    - Create questions about actions rather than instructions
    - Format each case with state (conversation + proposed action) and expected_answers
    - Split cases into tune and test sets
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 7.2 Write property test for evaluation case structure
    - **Property 16: Evaluation Case Structure**
    - **Validates: Requirements 9.2, 9.3**
    - Verify each entry contains both "state" and "expected_answers" fields

- [x] 8. Create demo script and agent description
  - [x] 8.1 Write demo_script.yaml with conversation turns
    - Create scenario demonstrating file tracking
    - Create scenario demonstrating safe process listing
    - Create scenario demonstrating guardrail blocking ambiguous delete
    - Create scenario demonstrating low-confidence confirmation flow
    - Create scenario demonstrating successful destructive action after explicit request
    - Add neutral narration lines for video recording
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 7.1_

  - [x] 8.2 Update AGENT.md with laptop assistant use case
    - Describe the problem: laptop management through natural language
    - Describe the target user: laptop owners
    - Describe the features: file tracking, app management, safety guardrails
    - Describe the Strands Decider 2B decision pattern
    - _Requirements: 6.3, 8.1_

- [x] 9. Checkpoint - Integration testing and end-to-end validation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Final integration and testing tasks
  - [x] 10.1 Add action classifier for Safe_Action vs Destructive_Action
    - Define SAFE_ACTIONS set (enumerate_directory, get_file_info, list_processes, get_process_info)
    - Define DESTRUCTIVE_ACTIONS set (delete_file, move_file, terminate_process, launch_application)
    - Implement classify_action function returning ActionType
    - _Requirements: 5.1_

  - [ ]* 10.2 Write property tests for action classification
    - **Property 10: Safe Action Classification**
    - **Validates: Requirements 5.1**
    - **Property 12: Safe Action State Invariant**
    - **Validates: Requirements 5.4**
    - Test that Safe_Action operations do not modify filesystem or process state

  - [x] 10.3 Add NAME constant and finalize agent.py contract
    - Define NAME = "laptop-assistant" in agent.py
    - Ensure chat() returns dict with reply, decisions, model_id, latency_ms
    - Verify decisions list contains probabilities (0..1), verdict, and decider_ms
    - Test constructor accepts eager parameter for demos
    - _Requirements: 6.1, 6.2_

  - [ ]* 10.4 Write integration tests for LLM interpretation
    - Test natural language interpretation of file requests (Req 1.1, 1.3)
    - Test intent classification (information vs control) (Req 3.4)
    - Test with 1-3 representative examples per behavior

- [x] 11. Finalize deployment configuration
  - [x] 11.1 Update features.yaml for AgentCore deployment
    - Set agent_name to laptop-assistant
    - Set llm_provider to bedrock
    - Set model_id using environment variable BEDROCK_MODEL_ID
    - Add pattern_tag: guardrails
    - _Requirements: 6.3, 6.5_

  - [x] 11.2 Verify hackathon kit contracts
    - Confirm decision.py has PATTERN_TAG and QUESTIONS exported
    - Confirm decision.py docstring starts with "REUSABLE DECISION PATTERN:"
    - Confirm agent.py has NAME and HackathonAgent class
    - Confirm eval_cases.jsonl uses same state layout as runtime wiring
    - Keep AWS User Group Madurai credit lines in generated files
    - _Requirements: 8.2, 8.3, 8.4, 9.1_

- [x] 12. Final checkpoint - Complete submission verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The agent uses Python with psutil for cross-platform compatibility
- Strands Decider 2B handles guardrail decisions with the #guardrails pattern tag
- Amazon Bedrock handles conversation and natural language understanding
- All LLM calls go through decider_kit.llm.agent_model (never direct boto3 calls)
- Property tests use minimum 100 iterations with generated test data
- Integration tests use 1-3 representative examples
- Low confidence threshold is 0.65 for all Destructive_Actions
- Guardrail checks must complete within 2000ms
- Safe operations must complete within 3000ms
- Built with the AWS User Group Madurai Strands Decider hackathon kit

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "8.2", "11.1"] },
    { "id": 1, "tasks": ["1.2", "2.1", "3.1", "10.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "3.2", "3.3", "10.2"] },
    { "id": 3, "tasks": ["5.1", "6.1", "7.1"] },
    { "id": 4, "tasks": ["5.2", "5.3", "6.2", "6.3", "7.2"] },
    { "id": 5, "tasks": ["5.4", "6.4", "8.1", "11.2"] },
    { "id": 6, "tasks": ["10.3", "10.4"] }
  ]
}
```
