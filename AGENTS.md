# MRDS Agent Architecture

This document outlines the multi-agent architecture and workflow states used by the Model Regression Detection System (MRDS). Our approach follows a system-first methodology, ensuring each AI agent operates within strict, governed boundaries to automate evaluation processes effectively.

## Core Philosophy
We employ an **Agentic State Machine** (via LangGraph) rather than simple linear scripts. This allows us to handle complex failure modes, parallelize critique tasks, and naturally introduce Human-in-the-Loop (HITL) checkpoints.

---

## 1. Supervisor Agent
**Role:** The orchestrator of the evaluation pipeline.
**Responsibilities:**
- Receives the initial feature test request.
- Decomposes the evaluation into parallel dimensions (Accuracy, Consistency, Cost).
- Delegates tasks to specialized Critic Agents.
- Synthesizes the final verdict and triggers downstream business workflows (e.g., Notion, Zapier).

## 2. Critic Agents (Specialists)
These agents operate in parallel, evaluating specific aspects of the LLM feature's output against the golden dataset.

### A. Factual Accuracy Critic
- **Model:** `gpt-4o`
- **Role:** Verifies claims against the ground-truth provided in the golden dataset.
- **Output:** Binary (Pass/Fail) and Confidence Score.

### B. Logical Consistency Critic
- **Model:** `claude-3-5-sonnet`
- **Role:** Checks whether the reasoning strictly follows the input constraints without hallucinations.
- **Output:** Score (1-5) and specific issue callouts.

### C. Cost & Latency Analyst
- **Role:** Deterministic evaluator. Analyzes token usage and execution time.
- **Trigger:** Escalates if token usage spikes beyond the established baseline, regardless of accuracy.

## 3. Human-in-the-Loop (Reviewer Agent)
**Role:** The failsafe mechanism.
**Responsibilities:**
- If the Supervisor Agent determines that critics vehemently disagree, or the confidence score drops below `0.85`, the graph execution pauses.
- The state is pushed to the React Dashboard.
- A human operator must manually "Approve", "Reject", or "Adjust" the evaluation before the graph resumes and alerts are dispatched.

---

## Business Process Integration
This architecture isn't just about AI; it's about business automation.
When a regression is confirmed, the Supervisor Agent automatically:
1. Dispatches a highly-detailed Slack Alert.
2. Triggers an outbound Webhook (compatible with Zapier/Make/n8n).
3. Creates an actionable bug ticket in the team's project management tool.
