# Binance Sentinel

> **Adversarial Market Research Agent for Binance**

Binance Sentinel turns a trader's thesis into a structured research investigation. It retrieves Binance market data through an MCP handoff, validates the data, performs deterministic multi-timeframe analysis, builds an Evidence Ledger, challenges the thesis adversarially, derives invalidation conditions, and produces an auditable verdict.

**Research only — Sentinel does not execute trades.**

## Quick Navigation

- [What is Sentinel?](#what-is-sentinel)
- [Architecture](#architecture)
- [How it works](#how-it-works)
- [MCP integration](#mcp-integration)
- [User-facing GUI](#user-facing-gui)
- [Reports](#reports)
- [Run locally](#run-locally)
- [Testing](#testing)
- [Demo research cases](#demo-research-cases)
- [Pros & cons](#pros--cons)
- [Current limitations](#current-limitations)
- [Future scope](#future-scope)

## What is Sentinel?

Sentinel is built around one question:

> **What evidence supports my thesis, what evidence contradicts it, and what would prove it wrong?**

The user supplies a Binance symbol, direction (`LONG`/`SHORT`), time horizon, and thesis. Sentinel turns that input into a persisted research case rather than an immediate trade signal.

### Core workflow

```text
Trader Thesis
     ↓
Research Case
     ↓
Research Plan
     ↓
Binance MCP Data
     ↓
Data Quality Gate
     ↓
Deterministic Analysis
     ↓
Evidence Ledger
     ↓
Multi-Timeframe Assessment
     ↓
Confidence
     ↓
Adversarial Critic
     ↓
Invalidation Conditions
     ↓
Verdict
     ↓
Markdown + PDF Report
```


## Architecture

```text
┌─────────────────────┐
│     User / GUI      │
│ thesis + direction  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Research Case/Plan  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      MCP Bridge     │
│ request + handoff   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Binance MCP Agent   │
│ structured data     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Data Quality Gate   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Deterministic       │
│ Market Analysis     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Evidence Ledger     │
└───────┬─────────────┘
        │
   ┌────┴─────┐
   ▼          ▼
Multi-TF   Adversarial
          Critic
   │          │
   └────┬─────┘
        ▼
┌─────────────────────┐
│ Confidence +        │
│ Invalidation        │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Verdict + Reports   │
└─────────────────────┘
```

### Main modules

```text
main.py                       User-facing GUI
research/case_manager.py     Research case persistence
research/plan.py              Research plan
research/data_request.py      MCP request construction
research/data_quality.py      Data validation
research/mcp_bridge.py        File-based MCP handoff
research/mcp_runner.py        Research execution
research/pipeline.py          End-to-end orchestration
research/pdf_report.py       PDF result brief

binance/market_data.py        Market data models
binance/response_parser.py    MCP response parsing

analysis/market_analysis.py   Deterministic market analysis
analysis/thesis_evaluator.py  Evidence generation
analysis/multi_timeframe.py   Cross-timeframe aggregation
analysis/confidence.py        Evidence-weighted confidence
analysis/critic.py            Adversarial review
```

## How it works

### 1. Create a thesis

Example:

```text
Symbol: BNBUSDT
Direction: LONG
Horizon: 7–14 days

Thesis:
BNB has been showing sustained strength. I want to test whether
trend, momentum, volume and multi-timeframe structure support
further upside.
```

### 2. Generate the MCP request

Sentinel creates:

```text
storage/mcp/requests/<REQUEST_ID>.json
storage/mcp/requests/<REQUEST_ID>.txt
```

The request contains the required market data and output structure.

Current default historical coverage:

```text
1D → 60 completed candles
4H → 180 completed candles
1H → 720 completed candles
```

### 3. MCP result

The connected Binance MCP agent writes:

```text
storage/mcp/results/<REQUEST_ID>.json
```

Sentinel waits for the **matching request ID** rather than consuming an arbitrary result file.

### 4. Data quality

The dataset is checked before analysis. The GUI exposes coverage and core data availability.

### 5. Deterministic analysis

Current observations include:

- trend
- market structure
- momentum
- momentum change
- price/volume relationship
- volume behavior
- volatility

### 6. Evidence Ledger

Observations are classified as:

```text
FOR
AGAINST
INCONCLUSIVE
INVALIDATION
```

Evidence retains context such as timeframe, strength, source, observation, and reasoning.

### 7. Adversarial review

Sentinel deliberately looks for evidence that weakens or contradicts the user's thesis.

### 8. Invalidation conditions

Sentinel distinguishes:

- **current invalidation** — evidence showing the thesis has already failed
- **future invalidation conditions** — conditions that would make the thesis invalid later

### 9. Verdict

Current verdict states are:

```text
SUPPORTIVE
CAUTION
CONTRADICTED
```

Confidence is an **evidence-weighted research score**, not a statistical probability.

## MCP Integration

Sentinel currently uses a file-based MCP handoff:

```text
Sentinel
   │
   ├── request JSON
   ├── agent instruction
   │
   ▼
Binance MCP-connected agent
   │
   ▼
structured JSON result
   │
   ▼
Sentinel research engine
```

Official references:

- [Binance MCP Server](https://www.binance.com/en-ZA/support/faq/detail/7a6e676e36fb455d96478932cb12d9f3)
- [Binance Developer Docs](https://developers.binance.com/)

## User-facing GUI

The GUI is designed for both normal use and judge demonstration.

### Input

- Symbol
- LONG / SHORT
- Time horizon
- Trader thesis

### Visible workflow

```text
✓ CASE
✓ PLAN
✓ DATA
● ANALYSIS
  VERDICT
```

### Result view

The GUI exposes:

- Verdict
- Confidence
- Evidence state
- Adversarial risk
- Timeframe alignment
- Data Quality
- MCP Provenance
- Why This Verdict
- What Would Invalidate This Thesis?
- Key Evidence cards
- Full Evidence Ledger
- Adversarial Challenges
- Confidence Breakdown
- Markdown result
- PDF report

The main workspace is resizable and vertically scrollable.

## Reports

Each completed case can produce:

```text
output/reports/<CASE_ID>_result_brief.pdf
```

The PDF is generated from the current pipeline result and is therefore case-specific.

Typical report structure:

**Page 1**
- Decision metrics
- Trader thesis
- Key finding
- Evidence summary
- Research method

**Page 2**
- Multi-timeframe market view
- Supporting evidence
- Contradicting evidence
- Multi-timeframe assessment

**Page 3**
- Adversarial challenges
- Invalidation conditions
- Confidence breakdown
- Conclusion
- Limitations

## Run locally

### Requirements

Python 3.10+ recommended.

Install dependencies:

```powershell
pip install -r requirements.txt
```

The PDF output requires ReportLab.

### Start Sentinel

From the project root:

```powershell
python main.py
```

### Typical workflow

1. Enter a symbol and thesis.
2. Click **START RESEARCH**.
3. Open **VIEW MCP INSTRUCTION**.
4. Give the generated instruction to the MCP-connected Binance agent.
5. Wait for the matching result file.
6. Sentinel detects the result automatically.
7. Review the evidence and verdict.
8. Open the generated Markdown or PDF report.

## Testing

Core tests:

```powershell
python -m analysis.session_evidence_test
python -m research.pipeline_test
python -m research.mcp_bridge
python -m research.pdf_report
```

A final real-world test should also cover:

```text
GUI
→ MCP request
→ Binance result
→ Data quality
→ analysis
→ evidence
→ adversarial review
→ verdict
→ PDF
```

## Demo Research Cases

The prototype has been exercised with multiple symbols and directions, including:

```text
BTCUSDT  → SHORT
EDENUSDT → LONG
BNBUSDT  → LONG
DOGEUSDT → LONG
PLUMEUSDT → SHORT
```

These are example research cases, not hardcoded modes.

Each fresh case produces its own case ID, MCP request/result path, session, and report.

## Pros & Cons

### Pros

**Evidence-first**  
The decision is backed by structured evidence rather than a single indicator.

**Adversarial by design**  
The system explicitly looks for reasons the user's thesis could be wrong.

**Multi-timeframe**  
Separate timeframe states expose alignment and divergence.

**Auditable**  
Cases, requests, sessions, evidence, and reports are persisted.

**MCP-compatible**  
Data acquisition is separated from the research engine.

**Judge-readable**  
The GUI and PDF expose reasoning, evidence, challenges, and invalidation conditions.

### Cons

**Limited research horizon**  
The default 1D/4H/1H coverage is primarily suited to short-to-medium-term technical research.

**File-based MCP handoff**  
The prototype does not maintain a fully autonomous embedded MCP session.

**Deterministic technical scope**  
No fundamental, news, sentiment, or ML prediction engine is included.

**Confidence is not probability**  
The score is not calibrated to a probability of success.

**No execution**  
Sentinel does not place or manage trades.

## Current Limitations

Sentinel should be treated as a **working research prototype**, not a complete trading platform.

Current boundaries include:

- no automated trading
- no portfolio management
- no market-wide scanner
- no news/sentiment research engine
- no fundamental analysis engine
- no multi-year backtesting framework
- no autonomous recursive MCP research loop
- no claim of predictive accuracy

A long-horizon thesis should be interpreted in the context of the current research coverage.

## Future Scope

The architecture can later support:

- session comparison
- thesis evolution over time
- automatic re-research
- invalidation alerts
- watchlists
- longer historical coverage
- funding/open-interest/trade-flow evidence
- research templates
- scenario analysis
- cross-asset comparison
- historical backtesting
- evidence provenance graphs
- autonomous MCP research cycles

The product can evolve from:

```text
Adversarial Research Agent
        ↓
Personal Research Analyst
        ↓
Market Decision-Support Platform
        ↓
Autonomous Market-Research Agent
```

## Safety / Scope

Sentinel is a research and decision-support system.

It does not:

- guarantee returns
- predict exact future prices
- represent confidence as probability
- execute trades

Users remain responsible for interpreting the research.

## Useful Links

- [Binance MCP Server](https://www.binance.com/en-ZA/support/faq/detail/7a6e676e36fb455d96478932cb12d9f3)
- [Binance Developer Documentation](https://developers.binance.com/)
- [Binance Market Data Documentation](https://developers.binance.com/docs/derivatives/coin-margined-futures/market-data/rest-api/Get-Funding-Info)

## License

Add the project's selected license here before public release.
