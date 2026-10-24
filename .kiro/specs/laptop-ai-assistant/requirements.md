# Requirements Document

## Introduction

The Laptop AI Assistant is a hackathon submission agent that helps users manage files, track application usage, and control laptop applications through natural language conversation. The agent uses Strands Decider 2B for guardrail checks before executing potentially unsafe file or application operations, paired with Amazon Bedrock for natural language understanding and conversation. This ensures users can safely manage their laptop environment without accidentally executing destructive actions.

## Glossary

- **Agent**: The Laptop AI Assistant system that processes user requests and executes file and application management operations
- **User**: A laptop owner who interacts with the Agent through natural language chat to manage files and applications
- **File_Operation**: Any action that reads, modifies, moves, or deletes files on the laptop filesystem
- **App_Operation**: Any action that launches, monitors, or terminates applications running on the laptop
- **Guardrail_Check**: A safety verification performed by Strands Decider 2B before executing a File_Operation or App_Operation
- **Safe_Action**: An operation that reads information without modifying system state
- **Destructive_Action**: An operation that modifies or deletes files, or terminates running applications
- **Decider**: The Strands Decider 2B model that evaluates whether requested operations are safe and explicitly intended
- **LLM**: The Amazon Bedrock large language model that handles conversation and tool selection
- **Confidence_Score**: A probability value between 0 and 1 returned by the Decider indicating certainty in the safety assessment
- **Low_Confidence_Threshold**: A Confidence_Score below 0.65 that triggers human confirmation

## Requirements

### Requirement 1: Natural Language Conversation

**User Story:** As a User, I want to chat with the Agent in natural language about my files and applications, so that I can manage my laptop without remembering complex commands

#### Acceptance Criteria

1. WHEN the User sends a message in natural language, THE Agent SHALL interpret the request using the LLM
2. THE Agent SHALL maintain conversation context across multiple messages within a session
3. WHEN the User's request requires information gathering, THE Agent SHALL respond with relevant file or application information
4. THE Agent SHALL format responses in a clear and user-friendly manner

### Requirement 2: File Tracking and Feedback

**User Story:** As a User, I want the Agent to track files in specified directories, so that I can understand what files exist and receive feedback about my file organization

#### Acceptance Criteria

1. WHEN the User requests file tracking for a directory path, THE Agent SHALL enumerate files in that directory
2. THE Agent SHALL provide information about file names, sizes, and modification dates
3. WHEN the User requests feedback on file organization, THE Agent SHALL analyze file structure and provide recommendations
4. THE Agent SHALL limit file enumeration to paths the User explicitly specifies

### Requirement 3: Application Management

**User Story:** As a User, I want the Agent to help me manage running applications, so that I can monitor and control what is running on my laptop

#### Acceptance Criteria

1. WHEN the User requests information about running applications, THE Agent SHALL list active processes
2. THE Agent SHALL provide application names and resource usage information
3. WHEN the User requests application control actions, THE Agent SHALL recognize launch and termination commands
4. THE Agent SHALL distinguish between information requests and control actions

### Requirement 4: Guardrail Safety Checks

**User Story:** As a User, I want destructive operations to be checked for safety before execution, so that I do not accidentally delete important files or terminate critical applications

#### Acceptance Criteria

1. WHEN the Agent identifies a Destructive_Action request, THE Agent SHALL perform a Guardrail_Check before execution
2. THE Guardrail_Check SHALL pass the conversation state and proposed action to the Decider
3. THE Decider SHALL evaluate whether the action is explicitly requested and grounded in the conversation
4. THE Guardrail_Check SHALL complete within 2000 milliseconds
5. WHEN the Decider returns a Confidence_Score above 0.65 and indicates the action is safe, THE Agent SHALL proceed with execution
6. WHEN the Decider returns a Confidence_Score below the Low_Confidence_Threshold, THE Agent SHALL request User confirmation before proceeding

### Requirement 5: Fast Read-Only Operations

**User Story:** As a User, I want safe read-only operations to execute quickly without extra confirmation, so that I can efficiently explore my files and application status

#### Acceptance Criteria

1. THE Agent SHALL classify file and application information requests as Safe_Action operations
2. WHEN an operation is classified as a Safe_Action, THE Agent SHALL execute it without a Guardrail_Check
3. THE Agent SHALL complete Safe_Action operations within 3000 milliseconds
4. THE Agent SHALL never modify system state during a Safe_Action

### Requirement 6: Hackathon Technical Requirements

**User Story:** As a developer evaluating the Agent for the hackathon, I want the Agent to use Strands Decider 2B for guardrail decisions paired with Amazon Bedrock for conversation, so that the submission meets hackathon requirements

#### Acceptance Criteria

1. THE Agent SHALL use Strands Decider 2B for all Guardrail_Check operations
2. THE Agent SHALL use Amazon Bedrock for natural language understanding and conversation
3. THE Agent SHALL label the guardrail pattern as a reusable decision pattern with the tag guardrails
4. THE Agent SHALL expose the Decider questions and option descriptions in the decision module
5. WHEN deployed to AWS, THE Agent SHALL run on Amazon Bedrock AgentCore Runtime

### Requirement 7: Low-Confidence Handling

**User Story:** As a developer evaluating the Agent for the hackathon, I want the Agent to handle low-confidence decisions explicitly, so that the submission demonstrates responsible AI safety practices

#### Acceptance Criteria

1. WHEN the Decider returns a Confidence_Score below the Low_Confidence_Threshold for a Destructive_Action, THE Agent SHALL request explicit User confirmation
2. THE Agent SHALL report the Confidence_Score to the User when requesting confirmation
3. THE Agent SHALL allow the User to approve or reject the action after reviewing the low-confidence warning
4. WHEN the User rejects a low-confidence action, THE Agent SHALL cancel the operation and explain the cancellation

### Requirement 8: Reusable Decision Pattern

**User Story:** As a developer building the Agent, I want the decision logic separated from conversation logic, so that the guardrail pattern can be reused in other agents

#### Acceptance Criteria

1. THE Agent SHALL implement the guardrail decision in a separate decision module
2. THE decision module SHALL define PATTERN_TAG as guardrails
3. THE decision module SHALL define QUESTIONS containing the typed Decider questions
4. THE decision module SHALL provide a docstring labeled REUSABLE DECISION PATTERN describing the pattern and its usage
5. THE decision module SHALL accept arbitrary state text and proposed actions without coupling to specific file or application tool implementations

### Requirement 9: Benchmark Evaluation Cases

**User Story:** As a developer benchmarking the Agent, I want evaluation cases defined for guardrail decisions, so that I can measure accuracy against an LLM baseline

#### Acceptance Criteria

1. THE Agent SHALL provide evaluation cases in eval_cases.jsonl format
2. EACH evaluation case SHALL contain a state field with conversation and proposed action context
3. EACH evaluation case SHALL contain expected answers for the Decider questions
4. THE evaluation cases SHALL include examples of explicitly requested destructive actions, ambiguous requests, and safe information requests
5. THE evaluation cases SHALL be split into tune and test sets

### Requirement 10: Clear Guardrail Feedback

**User Story:** As a User, I want clear feedback when an action is blocked by guardrails, so that I understand why my request was not executed and how to rephrase it if needed

#### Acceptance Criteria

1. WHEN a Destructive_Action is denied by the Guardrail_Check, THE Agent SHALL explain why the action was blocked
2. THE Agent SHALL quote the specific phrase from the conversation that caused the denial when the request is ambiguous
3. WHEN a User confirmation is required, THE Agent SHALL present the proposed action and ask for explicit approval
4. THE Agent SHALL provide guidance on how to phrase requests clearly for future interactions
