# Model Regression Detection System

A CI/CD-style pipeline that continuously tests any LLM-powered feature against a golden dataset whenever a prompt or model changes, detects quality regressions, and alerts your team via Slack before bad outputs reach users.

## Architecture
```mermaid
graph TB
    subgraph "Trigger Layer"
        A["GitHub PR<br/>(prompts/ changed)"] --> B["GitHub Actions"]
        C["Manual Trigger<br/>(Dashboard button)"] --> D["Backend API"]
        E["Scheduled Cron<br/>(Daily/Weekly)"] --> D
    end

    subgraph "Backend — GCP Cloud Run"
        B --> D
        D --> F["Eval Engine"]
        F --> G["LLM Feature Runner<br/>(async batched)"]
        G --> H["OpenAI API"]
        F --> I["Multi-Dim Scorer"]
        I --> J["LLM-as-Judge"]
        J --> H
        I --> K["Deterministic Checks"]
        F --> L["Diff Engine"]
        L --> M["Statistical Analyzer"]
        F --> N["Drift Detector<br/>(rolling average)"]
        D --> O["Report Generator<br/>(HTML)"]
        D --> P["Slack Alerter"]
        D --> Q["PostgreSQL"]
    end

    subgraph "Frontend — Cloudflare Pages"
        R["React Dashboard"]
        R --> D
    end

    P --> S["Slack Channel"]
    B --> T["PR Comment Bot"]
```

## Prerequisites
- Docker & docker-compose
- Python 3.11+
- Node 20+
- PostgreSQL 16 (handled by docker)

## Setup Instructions
1. Clone the repository
2. `cp .env.example .env` and fill in your keys
3. `make setup`
4. `make dev`

## Usage
- **Add Golden Dataset:** Add a JSON file to `golden-dataset/` 
- **Add Prompt:** Add a YAML file to `prompts/`
- **Adjust Thresholds:** Change `REGRESSION_WARNING_THRESHOLD` in `.env`
