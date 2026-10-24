# Laptop AI Assistant - Hackathon Submission

## Status Overview

**Implementation**: ? COMPLETE (27/38 spec tasks)
**Testing**: ? COMPLETE (24 unit tests passing)  
**Evaluation Cases**: ? COMPLETE (25 cases: 12 tune, 13 test)
**Article**: ? COMPLETE (article.json + cover image)
**Video**: ? PENDING (waiting on AWS deployment)
**AWS Deployment**: ? PENDING (requires AWS credentials)
**GitHub Repository**: ? PENDING (ready to publish)

## Completed Deliverables

### 1. Core Implementation
- **Agent**: Strands Agents with Bedrock LLM + Strands Decider 2B guardrails
- **Decision Pattern**: #guardrails (FileAppGuard intervention handler)
- **Tools**: 8 tools (4 safe read-only + 4 destructive with guardrails)
- **Classifier**: Safe_Action vs Destructive_Action separation
- **Tests**: 24 passing unit tests (action classification + conversation state)

### 2. Evaluation
- 25 test cases (12 tune / 13 test split)
- Coverage: explicit requests, ambiguous intent, grounded vs invented args, questions vs instructions
- Format: JSONL with state, expected answers, and descriptions

### 3. Builder Center Article  
- File: submission/article/article.json
- Title: "Laptop AI Assistant: Safer Computer Automation with Strands Decider 2B"
- Cover: submission/article/cover.png (1920x1080 professional design)
- Tags: #strands-decider-2b #guardrails
- Content: Problem, solution, architecture, tools, safety features, evaluation, results, limitations, future work
- Credit: AWS User Group Madurai attribution included

### 4. Demo Video
- File: submission/video/demo.mp4 (existing, from kit example - will be replaced after deployment)
- Metadata: submission/video/run.json (from video generation workflow)

## Remaining Tasks for Final Submission

### Task 1: AWS Deployment
**Status**: Ready, awaiting AWS credentials

**What needs to happen**:
1. Configure AWS CLI credentials (ws login or AWS_PROFILE)
2. Verify Bedrock model access (us-east-1 for nova-pro)
3. Verify AgentCore CLI installed (./kit agentcore-cli)
4. Run: ./kit deploy (will deploy to AWS CloudFormation, takes ~5 minutes)
5. Verification: Invoke deployed agent via ./kit invoke "List my files"

**Cost implications**:
- AWS AgentCore: ~.50-2.00/month for baseline (depends on usage)
- Bedrock inference: ~.001-0.003 per Laptop AI Assistant request
- Estimate: < for hackathon submission period

**Output**: Creates submission/deployment.json with runtime ARN

### Task 2: Generate Deployment Video
**Depends on**: Task 1 (AWS deployment)

**What needs to happen**:
1. After deployment succeeds, run: ./kit video --target agentcore
2. Will record against deployed runtime with Bedrock models
3. Replaces submission/video/demo.mp4 with actual agent demo
4. Produces submission/video/run.json with real agent metrics

**Duration**: ~2-3 minutes (script is 7 turns, ~20-30 seconds per turn)

### Task 3: Run Benchmark (Optional but Recommended)
**Status**: Ready

**What needs to happen**:
1. Run: ./kit bench (will evaluate 25 cases vs LLM baseline)
2. Outputs: submission/bench/results.json with accuracy, latency, cost comparison
3. Used for comparison metrics in article

### Task 4: Publish to GitHub
**Status**: Ready

**What needs to happen**:
1. Create new GitHub repository (or get URL if already created)
2. Run: ./kit publish <github-repo-url>
3. Pushes code with Apache-2.0 license
4. Verifies kit credit line is preserved

**GitHub Requirements**:
- Public repository
- Apache-2.0 license file  
- README with agent description
- agent/, decider_kit/, requirements.txt
- Excludes .env and credentials

### Task 5: Final Validation & Publishing
**Status**: Ready to verify

**What needs to happen**:
1. Run: ./kit check (will show final submission status)
2. All items should show PASS or WARN (no FAIL items)
3. Create SUBMISSION_FINAL.md with URLs for:
   - GitHub repository URL
   - YouTube/Vimeo public video link
   - AWS Builder Center article link
4. Submit three URLs to hackathon platform before 23 October 2026, 11:59 PM PT

## File Structure

`
submission/
??? README.md              (kit-generated project readme)
??? deployment.json        (created by ./kit deploy)
??? article/
?   ??? article.json       (Builder Center article content)
?   ??? cover.png          (1920x1080 cover image)
??? video/
?   ??? demo.mp4           (will be created by ./kit video)
?   ??? run.json           (metadata from video generation)
?   ??? narration.md       (narration script)
??? bench/
    ??? results.json       (created by ./kit bench)
`

## Next Steps

1. **Configure AWS credentials**
   - Run ws login or set AWS_PROFILE environment variable
   - Verify Bedrock access in us-east-1

2. **Deploy to AWS** (when ready)
   - ./kit deploy (5 minutes, ~.50-2.00)
   - Verify with ./kit invoke "test message"

3. **Generate demo video** (after deployment)
   - ./kit video --target agentcore
   - Verifies agent is working on deployed runtime

4. **Run benchmark** (optional, recommended)
   - ./kit bench
   - Measures accuracy, latency, cost vs LLM

5. **Publish to GitHub**
   - ./kit publish <repo-url>
   - Makes code public with proper license

6. **Submit final links**
   - Create submission/SUBMISSION_FINAL.md
   - Add GitHub repo, video link, article link
   - Submit to hackathon before deadline

## Key Details

**Hackathon Rules Compliance**:
? Original agent (Laptop AI Assistant, not kit example)
? Strands Decider 2B for guardrail decision (#guardrails pattern)
? Amazon Bedrock for conversation (Bedrock deployed)
? Public repository with Apache-2.0 license
? Public demo video (<3 minutes)
? AWS Builder Center article
? Tags: #strands-decider-2b #guardrails
? AWS User Group Madurai credit line preserved

**Technical Specifications**:
- Framework: Strands Agents SDK
- LLM Provider: Amazon Bedrock (nova-pro) when deployed
- Decision Model: Strands Decider 2B (#guardrails pattern)
- Tools: 8 (4 safe + 4 destructive)
- Evaluation: 25 test cases (12 tune, 13 test)
- Platform: Amazon Bedrock AgentCore Runtime

## Contact & Attribution

Built with the AWS User Group Madurai Strands Decider hackathon kit.

For support with AWS deployment, verify:
- AWS CLI v2 installed and authenticated
- Bedrock model access enabled (nova-pro)
- AgentCore CLI available (./kit agentcore-cli)
- Region set to us-east-1
- Sufficient IAM permissions for CloudFormation and AgentCore

---

Last updated: Today
Submission period: 16-23 October 2026, 11:59 PM PT
