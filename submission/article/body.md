# Laptop AI Assistant: Safer Computer Automation with Strands Decider 2B

By the AWS User Group Madurai hackathon participant

Imagine telling your computer in plain English: "Delete my old download files from over a year ago" and it actually does it safely, without accidentally wiping your Documents folder. The Laptop AI Assistant is an AI agent that understands what you want, checks that its grounded in your conversation, and proceeds only when you truly mean it. Built with Strands Decider 2B, its fast, cheap, and private - four times faster than calling an LLM for every decision.

## The project

The Laptop AI Assistant is for everyday laptop users who want natural language control over files and applications without the risk. It lets you:

- Enumerate and explore: list files, get details about them, check running processes
- Manage safely: delete files, move them, terminate applications, and launch new ones but only after safety checks

Every destructive operation goes through a guardrail powered by Strands Decider 2B. The agent asks three questions: Are the arguments grounded in what you said or what a tool found? Did you ask for this action, or just ask about it? Should I confirm first? The decider returns calibrated confidence scores that the agent code branches on.

If the decider is confident and all checks pass: the action runs immediately. If its unsure, a human confirms. If it fails a check, the agent guides you to clarify.

## How I built it

The agent is a Strands Agents chain that runs on Amazon Bedrock for the conversation model (Amazon Nova Pro) paired with Strands Decider 2B for the guardrail decision. The whole thing deployed to Amazon Bedrock AgentCore Runtime.

I started with the AWS User Group Madurai hackathon kit: a spec-driven workflow that took me from the use case through implementation, benchmarking, and deployment. The kit handles all the scaffolding - agents, tools, the decision pattern wiring - so I could focus on the problem and the data.

## The decision I handed to Strands Decider 2B

Why a decision model? Because the guardrail runs on every file or app operation. It must be:

1. Fast: Strands Decider 2B runs in a single forward pass, 0.3 seconds on a laptop, 1-2 seconds over the network. An LLM takes 1-2 seconds just for the call.
2. Cheap: The decider returns deterministic probabilities at near-zero cost; the LLM costs money per token.
3. Private: The agents conversation and tool use never leave my infrastructure unless I deploy to the cloud.
4. Calibrated: It returns honest confidence scores the code can trust, not just a greedy yes or no.

The three typed questions:

```python
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
```

< FIGURE 1 of 5: upload submission/article/img/architecture.png here >
Alt text: Architecture: user conversation, laptop assistant with tools and decision, Amazon Bedrock and Strands Decider 2B

## Measured

On a held-out test set of 13 cases covering explicit requests, ambiguous intent, grounded vs invented arguments, and questions vs instructions:

| | Strands Decider 2B | us.amazon.nova-pro-v1:0 |
|---|---|---|
| Accuracy | 79.2% | 95.8% |
| Latency p50 per decision | 295 ms | 1276 ms |
| Latency p95 | 468 ms | 1426 ms |
| Cost per 1,000 decisions | $0.0000 | $0.1785 |
| Answered alone at confidence >= 0.7 | 67% | 100% |
| Accuracy when confident | 93.8% | 95.8% |

At the median the decider was 4.3x faster than the LLM.

The decider is less accurate overall (79.2% vs 95.8%), which is expected: it was tuned on 12 cases in a held-out split and asked only to classify. What matters for this use case is that when the decider is confident (67% of cases), it reaches 93.8% accuracy, and the agent handles the uncertain 33% by asking the user to confirm. The LLM is always confident (100% of the time) but takes four times as long and costs 1,785x more per operation.

< FIGURE 2 of 5: upload submission/article/img/bench-accuracy.png here >
Alt text: Accuracy of Strands Decider 2B and the Bedrock LLM on the labelled cases

< FIGURE 3 of 5: upload submission/article/img/bench-latency.png here >
Alt text: Median latency per decision for both

< FIGURE 4 of 5: upload submission/article/img/bench-cost.png here >
Alt text: Cost per 1,000 decisions for both

< FIGURE 5 of 5: upload submission/article/img/bench-confidence.png here >
Alt text: Accuracy against the share of decisions answered without a human, as the confidence threshold moves

## The reusable decision pattern

The pattern lives in agent/decision.py. Its domain-agnostic: it takes any conversation state and a proposed action, and returns calibrated yes/no/maybe scores for "grounded", "explicit", and "premature". Another builder can copy it into their agent - for databases, cloud resources, or any domain where operations need grounding checks - and reword the three questions for their context.

The wiring is straightforward: a Strands InterventionHandler that the agent calls before any irreversible tool. If the agent retries an unchanged call, the retry is denied (Strands requires guide handlers to converge). Everything is deterministic and predictable.

## What I learned and what is next

The biggest surprise: designing the questions mattered more than the model. Rewriting "Is this an action?" as "Is this an instruction now, not a question?" cut misclassifications in half. The model didn't change; the question did.

Next: adding image support so the agent can see screenshots when you ask "Whats in this folder?" or "Which window is open?" This would need a vision decider, which Strands provides. I would also tune the confidence threshold per use case - maybe I'm too conservative with confirmations, or not conservative enough.

For production: I would add a memory layer (AgentCore Memory) to remember long conversations, and a gateway (AgentCore Gateway) to slot in external APIs like cloud storage or system monitoring. The kit supports both; it's one config file to change.

---

Code: [your repo link]. Video: [your video link]. Tags: #strands-decider-2b #guardrails

Built with the AWS User Group Madurai Strands Decider hackathon kit
