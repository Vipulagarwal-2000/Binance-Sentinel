# Binance Sentinel — Fresh Setup & First Research Run

Follow these steps to run **Binance Sentinel from a fresh installation**.

> **Important:** The first large Binance MCP request can take significantly longer while the MCP environment initializes. Warming up the MCP agent with a few small requests before the first Sentinel investigation can reduce the wait substantially.

---

## 1. Download / Clone the Repository

Clone the repository:

```powershell
git clone https://github.com/Vipulagarwal-2000/Binance-Sentinel.git
cd Binance-Sentinel
```

Or download the repository as a ZIP and extract it.

Open the extracted **Binance-Sentinel** project folder in VS Code.

---

## 2. Create a Python Virtual Environment

From the project root:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see:

```text
(.venv)
```

in the terminal.

---

## 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

The current project uses **ReportLab** for PDF generation.

---

## 4. Configure Binance MCP in VS Code

Sentinel currently uses a **file-based MCP handoff** with a Binance MCP-connected agent running through VS Code.

Before starting a full Sentinel investigation:

1. Configure the Binance MCP server/agent in VS Code.
2. Confirm that the MCP agent is connected and able to respond to Binance requests.

Official documentation:

- [Binance MCP Server](https://www.binance.com/en/support/faq/detail/7a6e676e36fb455d96478932cb12d9f3)
- [Binance Developer Documentation](https://developers.binance.com/)

---

## 5. Warm Up the Binance MCP Agent

### Why this matters

On a fresh MCP environment, the first large request can take much longer than subsequent requests.

Run **2–4 small requests** through the Binance MCP agent in VS Code.

### Recommended warm-up requests

```text
Get the current BTCUSDT price using Binance MCP
```

```text
Get 5 recent BTCUSDT 1H candles using Binance MCP
```

```text
Get the top 10 Binance gainers using Binance MCP
```

```text
Get 40 recent 1H candles for BNBUSDT using Binance MCP
```

These are only connectivity/warm-up tests. They do not need to be sent through Sentinel.

### Observed warm-up effect

```text
No warm-up       → 20–40+ minutes
1–2 small tests  → ~6–10 minutes
3–4 small tests  → ~2–5 minutes
```

> These timings were observed during development and may vary by environment, network, and MCP initialization time.

---

## 6. Start Binance Sentinel

From the project root:

```powershell
python main.py
```

The Sentinel GUI should open.

---

## 7. Create a Research Case

Example:

```text
Symbol: BNBUSDT
Direction: LONG
Time Horizon: 7–14 days
```

Example thesis:

```text
BNB has been showing sustained strength. I want to test whether
trend, momentum, volume, and multi-timeframe structure support
further upside over the next 7–14 days.
```

Click:

```text
START RESEARCH
```

---

## 8. Sentinel Creates the Research Request

The current default historical coverage is:

```text
1D → 60 completed candles
4H → 180 completed candles
1H → 720 completed candles
```

It also requests current market information such as:

```text
Current price
24h statistics
Volume information
Order book
```

The request is saved under:

```text
storage/mcp/requests/
```

---

## 9. Open the MCP Instruction

In the GUI, click:

```text
VIEW MCP INSTRUCTION
```

Sentinel displays the exact instruction for the Binance MCP agent.

The request contains a unique request ID, for example:

```text
BNBUSDT_20260909_164855_892219
```

---

## 10. Run the MCP Request

Copy the generated instruction and give it to the **Binance MCP-connected agent in VS Code**.

The MCP agent must return the requested structured JSON using the **same request ID**.

Expected location:

```text
storage/mcp/results/<REQUEST_ID>.json
```

Example:

```text
storage/mcp/results/
└── BNBUSDT_20260909_164855_892219.json
```

### Important

Do not rename the result.

Do not create another request ID.

Do not mix results from another research case.

---

## 11. Sentinel Detects the Result

Once the matching JSON is available, Sentinel detects it automatically.

The GUI workflow progresses through:

```text
✓ CASE
✓ PLAN
✓ DATA
✓ ANALYSIS
✓ VERDICT
```

---

## 12. Data Quality Check

Before analysis, Sentinel verifies the required market data.

Example:

```text
DATA QUALITY

✓ 1D: 60/60 candles
✓ 4H: 180/180 candles
✓ 1H: 720/720 candles
✓ Price
✓ 24h statistics
✓ Order book
✓ Volume
```

---

## 13. Research Pipeline

The completed result moves through:

```text
Data Quality
      ↓
Deterministic Market Analysis
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
```

---

## 14. Review the Verdict

The GUI presents:

```text
VERDICT
CONFIDENCE
EVIDENCE STATE
ADVERSARIAL RISK
TIMEFRAME ALIGNMENT
```

Then review:

```text
WHY THIS VERDICT?
```

---

## 15. Review Key Evidence

The GUI surfaces the strongest evidence as **Key Evidence Cards**.

Cards show:

```text
FOR / AGAINST / INCONCLUSIVE
Timeframe
Strength
Human-readable explanation
```

The full Evidence Ledger remains available below.

---

## 16. Review Adversarial Analysis

Scroll down to:

```text
ADVERSARIAL CHALLENGES
```

Sentinel deliberately looks for evidence that weakens or contradicts the thesis.

---

## 17. Review Invalidation Conditions

Inspect:

```text
WHAT WOULD INVALIDATE THIS THESIS?
```

Sentinel distinguishes:

### Current invalidation

Evidence indicating that the thesis has already failed.

### Future invalidation

Conditions that would make the thesis invalid later.

---

## 18. Review MCP Provenance

The GUI shows:

```text
MCP PROVENANCE
Request ID: <REQUEST_ID>
Source: Binance MCP
Result file: <matching JSON>
```

This links the research result back to its market-data request.

---

## 19. Open the Full Research Result

Click:

```text
VIEW MARKDOWN
```

This opens the full scrollable research result.

---

## 20. Open the PDF Report

After research completes:

```text
OPEN PDF REPORT
```

The report is generated under:

```text
output/reports/<CASE_ID>_result_brief.pdf
```

Example:

```text
output/reports/BNBUSDT_001_result_brief.pdf
```

---

## 21. Start Another Investigation

Click:

```text
NEW RESEARCH
```

Enter a new symbol, direction, horizon, and thesis.

Each investigation receives its own:

```text
Case
Request ID
MCP result
Research session
Verdict
Report
```

---

# Troubleshooting

## Sentinel stays on "Waiting for Binance MCP result"

Check:

```text
✓ Binance MCP is connected in VS Code
✓ The generated instruction was executed
✓ A result JSON was created
✓ The result is inside storage/mcp/results/
✓ The filename exactly matches the active request ID
✓ The JSON is valid
```

Expected structure:

```text
Binance-Sentinel/
└── storage/
    └── mcp/
        ├── requests/
        │   ├── <REQUEST_ID>.json
        │   └── <REQUEST_ID>.txt
        │
        └── results/
            └── <REQUEST_ID>.json
```

## MCP responds slowly

On a fresh environment:

```text
Stop
 ↓
Warm up the MCP agent
 ↓
Run 2–4 small Binance requests
 ↓
Run the Sentinel request
```

Subsequent requests are typically faster once the MCP environment is initialized.

## PDF does not open

Make sure the research pipeline completed and that a report exists under:

```text
output/reports/
```

---

# Reproduction Summary

```text
Clone / Download
        ↓
Create .venv
        ↓
pip install -r requirements.txt
        ↓
Configure Binance MCP in VS Code
        ↓
Warm up MCP
        ↓
python main.py
        ↓
Create Thesis
        ↓
START RESEARCH
        ↓
VIEW MCP INSTRUCTION
        ↓
Run instruction through Binance MCP
        ↓
Matching Result JSON
        ↓
Data Quality
        ↓
Analysis
        ↓
Evidence Ledger
        ↓
Adversarial Review
        ↓
Invalidation Conditions
        ↓
Verdict
        ↓
PDF / Markdown
```

---

# Final Check

A fresh installation has successfully reproduced Sentinel when:

```text
[✓] Repository opens
[✓] Dependencies install
[✓] MCP connects
[✓] MCP warm-up succeeds
[✓] Sentinel GUI starts
[✓] Research case is created
[✓] MCP request is generated
[✓] Matching result is returned
[✓] Data quality passes
[✓] Evidence is generated
[✓] Verdict appears
[✓] Adversarial review appears
[✓] Invalidation conditions appear
[✓] PDF is generated
[✓] PDF opens
```

> **Sentinel is a semi-autonomous research agent:** the research workflow, analysis, evidence evaluation, and reporting are automated, while the current MCP handoff is performed through the connected Binance agent in VS Code.
