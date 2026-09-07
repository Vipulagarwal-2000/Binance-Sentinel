# Binance Sentinel 

> ### **Adversarial Market Research Agent**
> Turn a trading thesis into a structured investigation — then challenge it.

**Research only. No trade execution. Semi Autonomus Agent**

---
## Useful Links

- [Architecture](#architecture)
- [Research Model](#research-model)
- [User-Facing GUI](#user-facing-gui)
- [Reports](#reports)
- [Run Locally](#run-locally)
- [Testing](#testing)
- [Strengths](#strengths)
- [Trade-offs](#trade-offs)
- [Current Scope](#current-scope)
- [Future Direction](#future-direction)

---

## What is Sentinel?

Binance Sentinel takes a user's **LONG/SHORT thesis** and turns it into an auditable research workflow.

Instead of:

```text
"Should I buy or sell?"
        ↓
     BUY / SELL
```

Sentinel asks:

```text
What supports the thesis?
What contradicts it?
How strong is the evidence?
Are timeframes aligned?
What would invalidate the thesis?
```



---

# Architecture

```text
                ┌──────────────┐
                │     User     │
                │  Thesis/GUI  │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │ Research     │
                │ Case + Plan  │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │  MCP Bridge  │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │ Binance MCP  │
                │     Agent    │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │ Data Quality │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │ Deterministic│
                │   Analysis   │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │ Evidence     │
                │   Ledger     │
                └──────┬───────┘
                       ↓
             ┌─────────┴─────────┐
             ↓                   ↓
       Multi-Timeframe     Adversarial Critic
             └─────────┬─────────┘
                       ↓
                ┌──────────────┐
                │ Confidence + │
                │ Invalidation │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │ Verdict +    │
                │ PDF/Markdown │
                └──────────────┘

---

### Default market coverage

| Timeframe | Completed candles |
|---|---:|
| 1D | 60 |
| 4H | 180 |
| 1H | 720 |

Also requested: current price, 24h statistics, volume information, and order-book data.

Official links:

- [Binance MCP Server](https://www.binance.com/en-ZA/support/faq/detail/7a6e676e36fb455d96478932cb12d9f3)
- [Binance Developer Docs](https://developers.binance.com/)

---

# Research Model

## Evidence Ledger

Every observation is classified as:

| Type | Meaning |
|---|---|
| 🟢 **FOR** | Supports the thesis |
| 🔴 **AGAINST** | Contradicts the thesis |
| ⚪ **INCONCLUSIVE** | Does not provide reliable confirmation |
| 🟠 **INVALIDATION** | Indicates the thesis has already failed |

Evidence keeps context such as:

```text
Timeframe
Observation
Strength
Source
Reasoning
```

## Multi-Timeframe

Sentinel evaluates the configured timeframes separately and then identifies whether they are aligned.

Example:

```text
1D → BULLISH
4H → BEARISH
1H → NEUTRAL

Alignment → DIVERGENT
```

## Adversarial Review

The critic deliberately searches for:

- contradictory evidence
- timeframe conflict
- weak confirmation
- unresolved evidence

## Invalidation

Sentinel separates:

**Current invalidation**  
Has the thesis already failed?

**Future invalidation**  
What future condition would make the thesis invalid?

---

# User-Facing GUI

The GUI is designed to make the research process visible.

### Input

```text
Symbol
Direction: LONG / SHORT
Time horizon
Trader thesis
```

### Result

The interface shows:

```text
Verdict
Confidence
Evidence State
Adversarial Risk
Timeframe Alignment
Data Quality
MCP Provenance
Why This Verdict
What Would Invalidate This Thesis?
Key Evidence Cards
Evidence Ledger
Adversarial Challenges
Confidence Breakdown
```

### Output

```text
[ VIEW MCP INSTRUCTION ]
[ VIEW REQUEST DETAILS ]
[ VIEW MARKDOWN ]
[ OPEN PDF REPORT ]
[ NEW RESEARCH ]
```

---

# Example

```text
Symbol: BNBUSDT
Direction: LONG
Horizon: 7–14 days

Thesis:
BNB has been showing sustained strength. I want to test whether
trend, momentum, volume and multi-timeframe structure support
further upside.
```

Sentinel may return:

```text
VERDICT       CAUTION
CONFIDENCE    63.4%
EVIDENCE      5 FOR / 4 AGAINST / 12 INCONCLUSIVE
RISK          HIGH
TIMEFRAME     DIVERGENT
```

The important part is that the result also explains **why**, shows the strongest evidence, and states what would invalidate the thesis.

---

# Run Locally

## 1. Install

Python 3.10+ recommended.

```powershell
pip install -r requirements.txt
```

PDF reports require **ReportLab**.

## 2. Start

From the project root:

```powershell
python main.py
```

## MCP Setup — Required Before Running Sentinel

Sentinel currently uses a **file-based handoff with a Binance MCP-connected agent running through VS Code**.

Before starting Sentinel, the user must configure the Binance MCP server/agent in their VS Code environment.

- [Binance MCP Server](https://www.binance.com/en-ZA/support/faq/detail/7a6e676e36fb455d96478932cb12d9f3)


## 3. Research workflow

```text
1. Enter thesis
2. Click START RESEARCH
3. Open VIEW MCP INSTRUCTION
4. Run the instruction through the Binance MCP agent
5. MCP writes the matching result JSON
6. Sentinel detects it automatically
7. Review evidence + verdict
8. Open Markdown or PDF
```

---

# Testing

Run the core tests:

```powershell
python -m analysis.session_evidence_test
python -m research.pipeline_test
python -m research.mcp_bridge
python -m research.pdf_report
```

Acceptance flow:

```text
GUI
 ↓
MCP Request
 ↓
Binance Result
 ↓
Data Quality
 ↓
Analysis
 ↓
Evidence
 ↓
Adversarial Review
 ↓
Verdict
 ↓
PDF
```
---

# Reports

Completed cases generate:

```text
output/reports/<CASE_ID>_result_brief.pdf
```

The report focuses on:

```text
Decision
↓
Market Structure
↓
Supporting / Contradicting Evidence
↓
Adversarial Review
↓
Invalidation
↓
Confidence
↓
Conclusion
```

The report is generated from the **current research session**, so it is not tied to a specific coin.

---

# Demonstrated Cases

The prototype has been exercised with:

```text
BTCUSDT    → SHORT
EDENUSDT   → LONG
BNBUSDT    → LONG
```

These are examples, not hardcoded modes.

A fresh investigation creates its own case, request, result, session, and report.

---

# Strengths

- **Evidence-first** — decisions are backed by structured observations.
- **Adversarial** — the system actively looks for reasons the thesis could be wrong.
- **Multi-timeframe** — divergence is made explicit.
- **Auditable** — research artifacts are persisted.
- **MCP-integrated** — market-data retrieval is separated from analysis.
- **Judge-readable** — reasoning is visible in both GUI and PDF.

# Trade-offs

- Default historical coverage is aimed at technical short/medium-term research.
- MCP currently uses a file-based handoff.
- Analysis is deterministic and technical rather than fundamental/news/sentiment based.
- Confidence is an evidence-weighted score, not a calibrated probability.
- Sentinel does not execute trades.

---

# Current Scope

Sentinel is a **working adversarial market-research prototype**.

It is intentionally not:

- a trading execution bot
- a portfolio manager
- a market-wide scanner
- a fundamental/news research platform
- a price-prediction ML system
- a multi-year backtesting framework

The current product focuses on one research loop:

> **Thesis → Evidence → Challenge → Invalidation → Decision**

---

# Future Direction

The same architecture can grow into:

```text
Session Comparison
        ↓
Thesis Evolution
        ↓
Automatic Re-Research
        ↓
Invalidation Alerts
        ↓
Longer Historical Research
        ↓
Additional Binance Evidence
        ↓
Autonomous Market Research
```

---

# Scope & Safety

Sentinel is **research and decision support only**.

It does not:

- guarantee returns
- predict exact prices
- treat confidence as probability
- execute trades

---
## External Links

### Binance

- [Binance MCP Server](https://www.binance.com/en/support/faq/detail/7a6e676e36fb455d96478932cb12d9f3)
- [Binance Agent OS](https://www.binance.com/en/agent-os)
- [Binance Developer Documentation](https://developers.binance.com/)
- [Binance Market Data Documentation](https://developers.binance.com/docs/)

### MCP Endpoint

```text
https://agent.binance.com/mcp/agentic

## Binance Sentinel

**Investigate the thesis. Challenge the thesis. Make the evidence visible.**
