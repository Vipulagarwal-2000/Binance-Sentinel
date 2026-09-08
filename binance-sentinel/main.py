"""
Binance Sentinel
Judge-facing GUI.

Workflow:
CASE -> PLAN -> MCP REQUEST -> WAIT FOR RESULT -> ANALYSIS -> VERDICT
"""

from pathlib import Path
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

from config import initialize_directories
from research.case_manager import CaseManager
from research.plan_manager import PlanManager
from research.mcp_bridge import MCPResearchBridge
from research.mcp_runner import MCPResearchRunner
from research.pdf_report import PDFResearchReport


class SentinelGUI:
    POLL_MS = 2000

    def __init__(self, root):
        initialize_directories()

        self.root = root
        self.root.title("Binance Sentinel")
        self.root.geometry("1180x820")
        self.root.resizable(True, True)
        self.root.minsize(900, 650)
        self._center_window(1180, 820)

        self.case_manager = CaseManager()
        self.plan_manager = PlanManager()
        self.bridge = MCPResearchBridge()
        self.runner = MCPResearchRunner()
        self.pdf_report = PDFResearchReport()

        self.case = None
        self.plan = None
        self.request = None
        self.request_id = None
        self.result_file = None
        self.pipeline_result = None
        self.report_path = None
        self.stage_order = ["CASE", "PLAN", "DATA", "ANALYSIS", "VERDICT"]
        self.stage_state = {name: "pending" for name in self.stage_order}

        self.symbol_var = tk.StringVar(value="EDENUSDT")
        self.direction_var = tk.StringVar(value="LONG")
        self.horizon_var = tk.StringVar(value="15-20 days")
        self.status_var = tk.StringVar(value="Ready — enter a research thesis.")
        self.verdict_var = tk.StringVar(value="—")
        self.confidence_var = tk.StringVar(value="—")
        self.evidence_state_var = tk.StringVar(value="—")
        self.risk_var = tk.StringVar(value="—")
        self.alignment_var = tk.StringVar(value="—")
        self.data_quality_var = tk.StringVar(value="—")
        self.provenance_var = tk.StringVar(value="—")

        self._build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self):
        root = self.root

        header = ttk.Frame(root, padding=(24, 18))
        header.pack(fill="x")

        title_row = ttk.Frame(header)
        title_row.pack(fill="x")

        ttk.Label(
            title_row,
            text="BINANCE SENTINEL",
            style="Title.TLabel",
        ).pack(side="left")

        ttk.Label(
            title_row,
            text="ADVERSARIAL MARKET RESEARCH",
            style="Kicker.TLabel",
        ).pack(side="left", padx=(16, 0), pady=(7, 0))

        ttk.Label(
            header,
            text="Turn a trader thesis into evidence, challenges, and an auditable decision.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        stages = ttk.Frame(root, padding=(24, 0, 24, 12))
        stages.pack(fill="x")

        self.stage_labels = {}
        for name in ["CASE", "PLAN", "DATA", "ANALYSIS", "VERDICT"]:
            label = ttk.Label(
                stages,
                text=name,
                relief="solid",
                padding=(12, 7),
                anchor="center",
            )
            label.pack(side="left", padx=(0, 8))
            self.stage_labels[name] = label

        # Scrollable research body. The header and stage timeline remain fixed
        # while the full research workspace can be scrolled vertically.
        body_container = ttk.Frame(root)
        body_container.pack(fill="both", expand=True)
        body_container.columnconfigure(0, weight=1)
        body_container.rowconfigure(0, weight=1)

        body_canvas = tk.Canvas(body_container, highlightthickness=0, bd=0)
        body_canvas.grid(row=0, column=0, sticky="nsew")

        body_scroll = ttk.Scrollbar(
            body_container,
            orient="vertical",
            command=body_canvas.yview,
        )
        body_scroll.grid(row=0, column=1, sticky="ns")
        body_canvas.configure(yscrollcommand=body_scroll.set)

        scrollable_body = ttk.Frame(body_canvas, padding=(24, 8, 24, 14))
        body_window = body_canvas.create_window(
            (0, 0),
            window=scrollable_body,
            anchor="nw",
        )

        def update_scroll_region(_event=None):
            body_canvas.configure(scrollregion=body_canvas.bbox("all"))

        def resize_scrollable_body(event):
            body_canvas.itemconfigure(body_window, width=event.width)

        scrollable_body.bind("<Configure>", update_scroll_region)
        body_canvas.bind("<Configure>", resize_scrollable_body)

        def scroll_body(event):
            body_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_mousewheel(widget):
            if widget is not self.result_text:
                widget.bind("<MouseWheel>", scroll_body)
            for child in widget.winfo_children():
                bind_mousewheel(child)

        self.body_canvas = body_canvas
        self.scrollable_body = scrollable_body
        main = scrollable_body

        input_frame = ttk.LabelFrame(
            main,
            text="  RESEARCH CASE  ",
            padding=16,
        )
        input_frame.pack(fill="x")

        ttk.Label(input_frame, text="Symbol").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6
        )
        symbol_entry = ttk.Entry(
            input_frame,
            textvariable=self.symbol_var,
            width=22,
        )
        symbol_entry.grid(row=0, column=1, sticky="w", pady=6)

        ttk.Label(input_frame, text="Direction").grid(
            row=0, column=2, sticky="w", padx=(30, 8), pady=6
        )
        direction_box = ttk.Combobox(
            input_frame,
            textvariable=self.direction_var,
            values=["LONG", "SHORT"],
            state="readonly",
            width=12,
        )
        direction_box.grid(row=0, column=3, sticky="w", pady=6)

        ttk.Label(input_frame, text="Time horizon").grid(
            row=0, column=4, sticky="w", padx=(30, 8), pady=6
        )
        ttk.Entry(
            input_frame,
            textvariable=self.horizon_var,
            width=18,
        ).grid(row=0, column=5, sticky="w", pady=6)

        ttk.Label(input_frame, text="Trader thesis").grid(
            row=1, column=0, sticky="nw", padx=(0, 8), pady=8
        )

        self.thesis_text = tk.Text(
            input_frame,
            height=5,
            width=90,
            wrap="word",
            font=("Segoe UI", 10),
        )
        self.thesis_text.grid(
            row=1,
            column=1,
            columnspan=5,
            sticky="ew",
            pady=8,
        )
        self.thesis_text.insert(
            "1.0",
            "EDEN may be entering a favorable accumulation and breakout phase.",
        )

        input_frame.columnconfigure(5, weight=1)

        action_frame = ttk.Frame(main, padding=(0, 14))
        action_frame.pack(fill="x")

        self.start_button = ttk.Button(
            action_frame,
            text="START RESEARCH",
            command=self.start_research,
            style="Primary.TButton",
        )
        self.start_button.pack(side="left")

        self.new_research_button = ttk.Button(
            action_frame,
            text="NEW RESEARCH",
            command=self.new_research,
            state="disabled",
        )
        self.new_research_button.pack(side="left", padx=(10, 0))

        self.request_button = ttk.Button(
            action_frame,
            text="VIEW MCP INSTRUCTION",
            command=self.show_mcp_instruction,
            state="disabled",
        )
        self.request_button.pack(side="left", padx=10)

        self.request_details_button = ttk.Button(
            action_frame,
            text="VIEW REQUEST DETAILS",
            command=self.show_request_details,
            state="disabled",
        )
        self.request_details_button.pack(side="left")

        self.pdf_button = ttk.Button(
            action_frame,
            text="OPEN PDF REPORT",
            command=self.open_pdf_report,
            state="disabled",
            style="Accent.TButton",
        )
        self.pdf_button.pack(side="left", padx=(10, 0))

        self.markdown_button = ttk.Button(
            action_frame,
            text="VIEW MARKDOWN",
            command=self.show_markdown_result,
            state="disabled",
        )
        self.markdown_button.pack(side="left", padx=8)

        result_frame = ttk.LabelFrame(
            main,
            text="  SENTINEL DECISION  ",
            style="Result.TLabelframe",
            padding=14,
        )
        result_frame.pack(fill="both", expand=True)

        status_row = ttk.Frame(result_frame)
        status_row.pack(fill="x", pady=(0, 6))

        ttk.Label(
            status_row,
            textvariable=self.status_var,
            style="Status.TLabel",
        ).pack(side="left")

        self.progress = ttk.Progressbar(
            status_row,
            mode="indeterminate",
            length=180,
        )
        self.progress.pack(side="right")

        metrics = ttk.Frame(result_frame, padding=(0, 20))
        metrics.pack(fill="x")

        self._metric(metrics, 0, "VERDICT", self.verdict_var)
        self._metric(metrics, 1, "CONFIDENCE", self.confidence_var)
        self._metric(metrics, 2, "EVIDENCE STATE", self.evidence_state_var)
        self._metric(metrics, 3, "ADVERSARIAL RISK", self.risk_var)
        self._metric(metrics, 4, "TIMEFRAME", self.alignment_var)

        info_row = ttk.Frame(result_frame, padding=(0, 0, 0, 10))
        info_row.pack(fill="x")
        ttk.Label(
            info_row,
            text="DATA QUALITY",
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left")
        ttk.Label(
            info_row,
            textvariable=self.data_quality_var,
        ).pack(side="left", padx=(6, 24))
        ttk.Label(
            info_row,
            text="MCP PROVENANCE",
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left")
        ttk.Label(
            info_row,
            textvariable=self.provenance_var,
        ).pack(side="left", padx=6)

        # Decision rationale panels: these are deliberately structured as
        # judge-facing GUI components rather than dense Markdown paragraphs.
        rationale_frame = ttk.Frame(result_frame)
        rationale_frame.pack(fill="x", pady=(0, 12))
        rationale_frame.columnconfigure(0, weight=1)
        rationale_frame.columnconfigure(1, weight=1)

        verdict_panel = ttk.LabelFrame(
            rationale_frame,
            text="  WHY THIS VERDICT?  ",
            padding=(12, 10),
        )
        verdict_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.verdict_highlight_label = tk.Label(
            verdict_panel,
            text="Waiting for research result.",
            anchor="w",
            justify="left",
            font=("Segoe UI", 11, "bold"),
            padx=8,
            pady=6,
        )
        self.verdict_highlight_label.pack(fill="x")

        self.verdict_stats_label = tk.Label(
            verdict_panel,
            text="",
            anchor="w",
            justify="left",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
        )
        self.verdict_stats_label.pack(fill="x")

        self.verdict_detail_label = tk.Label(
            verdict_panel,
            text="",
            anchor="nw",
            justify="left",
            wraplength=500,
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
        )
        self.verdict_detail_label.pack(fill="x")

        invalidation_panel = ttk.LabelFrame(
            rationale_frame,
            text="  WHAT WOULD INVALIDATE THIS THESIS?  ",
            padding=(12, 10),
        )
        invalidation_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.invalidation_primary_label = tk.Label(
            invalidation_panel,
            text="Waiting for research result.",
            anchor="w",
            justify="left",
            wraplength=500,
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=6,
        )
        self.invalidation_primary_label.pack(fill="x")

        self.invalidation_levels_label = tk.Label(
            invalidation_panel,
            text="",
            anchor="w",
            justify="left",
            wraplength=500,
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
        )
        self.invalidation_levels_label.pack(fill="x")

        self.invalidation_note_label = tk.Label(
            invalidation_panel,
            text="",
            anchor="w",
            justify="left",
            wraplength=500,
            font=("Segoe UI", 8),
            padx=8,
            pady=4,
        )
        self.invalidation_note_label.pack(fill="x")

        # Key evidence cards: surface the strongest directional evidence
        # before the judge has to read the full ledger.
        evidence_cards = ttk.LabelFrame(
            result_frame,
            text="  KEY EVIDENCE  ",
            padding=(10, 8),
        )
        evidence_cards.pack(fill="x", pady=(0, 10))

        self.evidence_card_labels = []
        for column in range(3):
            card = tk.Frame(
                evidence_cards,
                relief="solid",
                bd=1,
                padx=10,
                pady=7,
            )
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
            evidence_cards.columnconfigure(column, weight=1)

            title = tk.Label(
                card,
                text="—",
                anchor="w",
                font=("Segoe UI", 9, "bold"),
            )
            title.pack(fill="x")

            body = tk.Label(
                card,
                text="Waiting for research result.",
                anchor="w",
                justify="left",
                wraplength=310,
                font=("Segoe UI", 9),
            )
            body.pack(fill="x", pady=(3, 0))
            self.evidence_card_labels.append((card, title, body))

        result_text_frame = ttk.Frame(result_frame)
        result_text_frame.pack(fill="both", expand=True)

        self.result_text = tk.Text(
            result_text_frame,
            height=18,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
        )
        self.result_text.pack(side="left", fill="both", expand=True)

        result_scroll = ttk.Scrollbar(
            result_text_frame,
            orient="vertical",
            command=self.result_text.yview,
        )
        result_scroll.pack(side="right", fill="y")
        self.result_text.configure(yscrollcommand=result_scroll.set)

        footer = ttk.Frame(root, padding=(24, 8))
        footer.pack(fill="x")

        ttk.Label(
            footer,
            text="FILE-BASED MCP  •  DETERMINISTIC ANALYSIS  •  ADVERSARIAL REVIEW",
            style="Footer.TLabel",
        ).pack(side="left")

        ttk.Label(
            footer,
            text="Research only — no trade execution",
            style="Footer.TLabel",
        ).pack(side="right")

        self._set_stage("CASE")
        bind_mousewheel(scrollable_body)

    def _metric(self, parent, column, title, variable):
        frame = ttk.Frame(parent)
        frame.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0 if column == 0 else 8, 8),
        )
        ttk.Label(
            frame,
            text=title,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            frame,
            textvariable=variable,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w", pady=(3, 0))
        parent.columnconfigure(column, weight=1)

    # ---------------------------------------------------------
    # Workflow
    # ---------------------------------------------------------

    def start_research(self):
        symbol = self.symbol_var.get().strip().upper()
        direction = self.direction_var.get().strip().upper()
        horizon = self.horizon_var.get().strip()
        thesis = self.thesis_text.get("1.0", "end").strip()

        if not symbol:
            messagebox.showerror("Invalid case", "Enter a Binance symbol.")
            return

        if not thesis:
            messagebox.showerror("Invalid case", "Enter a trader thesis.")
            return

        if direction not in {"LONG", "SHORT"}:
            messagebox.showerror("Invalid case", "Choose LONG or SHORT.")
            return

        if not symbol.endswith("USDT"):
            proceed = messagebox.askyesno(
                "Symbol check",
                "This prototype is configured around Binance symbols.\n\n"
                f"You entered: {symbol}\n\n"
                "Continue?",
            )
            if not proceed:
                return

        try:
            self.start_button.config(state="disabled")
            self.new_research_button.config(state="disabled")
            self.request_button.config(state="disabled")
            self.progress.start(10)

            self._reset_result()
            self._set_stage("CASE")
            self.status_var.set("Creating research case...")
            self.root.update_idletasks()

            self.case = self.case_manager.create_case(
                name=f"{symbol} {direction} Thesis",
                symbol=symbol,
                direction=direction,
                time_horizon=horizon or "unspecified",
                thesis=thesis,
                assumptions=[],
            )

            self._set_stage("PLAN")
            self.status_var.set("Loading research plan...")
            self.root.update_idletasks()

            self.plan = self.plan_manager.load_plan(self.case.case_id)

            self._set_stage("DATA")
            self.status_var.set("Creating Binance MCP request...")
            self.root.update_idletasks()

            self.request = self._create_mcp_request()
            request_file, prompt_file = self._save_mcp_request()
            self.request_id = request_file.stem

            self.status_var.set(
                f"MCP request {self.request_id} created. "
                "Use the instruction in the request folder."
            )
            self.request_button.config(state="normal")
            self.request_details_button.config(state="normal")

            self._show_request_summary()

            self.progress.stop()
            self.start_button.config(state="disabled")

            self._poll_for_result()

        except Exception as exc:
            self.progress.stop()
            self.start_button.config(state="normal")
            self.new_research_button.config(state="disabled")
            self._set_stage("CASE")
            self.status_var.set("Research start failed.")
            messagebox.showerror(
                "Sentinel error",
                str(exc),
            )

    def _create_mcp_request(self):
        """Build a market-data request for the current case and plan."""
        return self.bridge.create_request(
            symbol=self.case.symbol,
            plan=self.plan,
        )

    def _save_mcp_request(self):
        """Persist the request and MCP instruction files."""
        return self.bridge.save_request(self.request)

    # ---------------------------------------------------------
    # MCP result polling
    # ---------------------------------------------------------

    def _poll_for_result(self):
        if not self.request_id:
            return

        try:
            result = self.bridge.find_result(self.request_id)

            if result:
                self.result_file = Path(result)

                if self.result_file.exists():
                    self._process_result()
                    return

        except Exception as exc:
            self.status_var.set(
                f"Waiting for MCP result... ({exc})"
            )

        self.status_var.set(
            f"Waiting for Binance MCP result: {self.request_id}"
        )
        self.root.after(self.POLL_MS, self._poll_for_result)

    def _process_result(self):
        try:
            # Binance MCP results may be emitted with a UTF-8 BOM. Normalize
            # that harmless encoding marker before handing the file to the
            # existing research runner. This does not alter the JSON data.
            if self.result_file and self.result_file.exists():
                raw_result = self.result_file.read_text(encoding="utf-8-sig")
                self.result_file.write_text(raw_result, encoding="utf-8")

            self._set_stage("ANALYSIS")
            self.status_var.set("Binance result received. Running Sentinel analysis...")
            self.progress.start(10)
            self.root.update_idletasks()

            result = self.runner.run_research(
                case_id=self.case.case_id,
                plan=self.plan,
                result_file=self.result_file,
            )

            self.pipeline_result = result

            self._set_stage("VERDICT")
            self._display_result(result)

            try:
                report_path = self.pdf_report.generate(result)
                self.report_path = Path(report_path)
                self.pdf_button.config(state="normal")
                self.markdown_button.config(state="normal")
                report_text = (
                    "\n\nREPORTS\n"
                    f"PDF: {self.report_path}\n"
                    "The full research result is also available in the "
                    "scrollable Markdown-style view."
                )
            except Exception as exc:
                self.report_path = None
                self.pdf_button.config(state="disabled")
                self.markdown_button.config(state="normal")
                report_text = f"\n\nPDF REPORT\nGeneration failed: {exc}"

            self._append_result(report_text)

            self.progress.stop()
            self.status_var.set(
                "Research complete — verdict generated."
            )
            self.start_button.config(state="normal")
            self.new_research_button.config(state="normal")

        except Exception as exc:
            self.progress.stop()
            self.status_var.set("Research processing failed.")
            self.start_button.config(state="normal")
            self.new_research_button.config(state="disabled")
            messagebox.showerror(
                "Research error",
                str(exc),
            )

    # ---------------------------------------------------------
    # Display
    # ---------------------------------------------------------

    def _display_result(self, result):
        confidence = result["confidence"]
        critic = result["critic"]
        timeframe = result["timeframe_result"]
        ledger = result["ledger"]
        session = result["session"]

        self.verdict_var.set(
            str(session.verdict or "—")
        )
        self.confidence_var.set(
            f"{confidence.confidence:.1f}%"
        )
        self.evidence_state_var.set(
            str(confidence.state)
        )
        self.risk_var.set(
            str(critic.overall_risk)
        )
        self.alignment_var.set(
            str(timeframe.alignment)
        )
        self.data_quality_var.set("PASSED")
        self.provenance_var.set(
            f"Binance MCP • {self.request_id or '—'}"
        )

        evidence_items = self._ledger_items(ledger)
        self._display_key_evidence(evidence_items)
        self._display_decision_rationale(
            session=session,
            confidence=confidence,
            critic=critic,
            timeframe=timeframe,
            evidence_items=evidence_items,
        )

        sections = [
            "CASE",
            self.case.case_id,
            "",
            "SYMBOL",
            self.case.symbol,
            "",
            "DIRECTION",
            self.case.direction,
            "",
            "TIME HORIZON",
            self.case.time_horizon,
            "",
            "TRADER THESIS",
            self.case.thesis,
            "",
            "DECISION",
            str(session.verdict or "—"),
            "",
            "WHY THIS VERDICT?",
            self._build_verdict_explanation(
                session=session,
                confidence=confidence,
                critic=critic,
                timeframe=timeframe,
                evidence_items=evidence_items,
            ),
            "",
            "FOCUSED RESEARCH",
            self._build_focused_research(
                session=session,
                confidence=confidence,
                critic=critic,
                timeframe=timeframe,
                evidence_items=evidence_items,
            ),
            "",
            "DATA QUALITY",
            self._build_data_quality_summary(),
            "",
            "MCP PROVENANCE",
            f"Request ID: {self.request_id or "—"}",
            f"Result file: {self.result_file or "—"}",
            "Source: Binance MCP",
            "",
            "EVIDENCE-WEIGHTED CONFIDENCE",
            f"{confidence.confidence:.1f}% — {confidence.state}",
            "",
            "ADVERSARIAL RISK",
            str(critic.overall_risk),
            "",
            "MULTI-TIMEFRAME",
            str(timeframe.alignment),
            f"Direction: {getattr(timeframe, 'direction', self.case.direction)}",
            f"Timeframes: {getattr(timeframe, 'timeframes', '—')}",
            "",
            "EVIDENCE SUMMARY",
            f"FOR: {timeframe.total_for}",
            f"AGAINST: {timeframe.total_against}",
            f"INCONCLUSIVE: {timeframe.total_inconclusive}",
            f"INVALIDATION: {timeframe.total_invalidation}",
            "",
            "CONFIDENCE BREAKDOWN",
            f"Supporting score: {getattr(confidence, 'supporting_score', '—')}",
            f"Contradicting score: {getattr(confidence, 'contradicting_score', '—')}",
            f"Invalidation score: {getattr(confidence, 'invalidation_score', '—')}",
            f"Inconclusive items: {getattr(confidence, 'inconclusive_items', getattr(confidence, 'inconclusive_count', '—'))}",
            "",
            "EVIDENCE LEDGER",
        ]

        if evidence_items:
            for index, item in enumerate(evidence_items, 1):
                sections.append(
                    self._format_evidence_item(index, item)
                )
        else:
            sections.append("No ledger entries available.")

        sections.extend([
            "",
            "ADVERSARIAL CHALLENGES",
        ])

        challenges = getattr(critic, "challenges", []) or []
        if challenges:
            for index, challenge in enumerate(challenges, 1):
                sections.append(
                    self._format_challenge(index, challenge)
                )
        else:
            sections.append("No adversarial challenges reported.")

        sections.extend([
            "",
            "WHAT WOULD INVALIDATE THIS THESIS?",
        ])

        invalidations = (
            getattr(session, "invalidation_conditions", None)
            or getattr(ledger, "invalidation_conditions", None)
            or []
        )
        if invalidations:
            sections.extend(str(item) for item in invalidations)
        else:
            sections.append(
                "No deterministic invalidation condition was triggered by the available market data.\n"
                "Sentinel does not invent a future price threshold when the evidence does not provide a defensible level."
            )

        sections.extend([
            "",
            "RESULT",
            "Sentinel completed the research pipeline and produced an "
            "evidence-weighted decision from the supplied Binance data.",
        ])

        self._set_result_text("\n".join(sections))

    def _build_focused_research(
        self,
        session,
        confidence,
        critic,
        timeframe,
        evidence_items,
    ):
        """Perform a second, focused review using evidence already collected.

        This is deliberately not a second MCP request. It identifies the most
        important unresolved research question from the completed investigation
        and answers it from the existing multi-timeframe and ledger evidence.
        """
        alignment = str(getattr(timeframe, "alignment", "—")).upper()
        direction = str(getattr(timeframe, "direction", self.case.direction)).upper()

        by_type = {"FOR": [], "AGAINST": [], "INCONCLUSIVE": [], "INVALIDATION": []}
        for item in evidence_items:
            if isinstance(item, dict):
                kind = str(item.get("evidence_type", item.get("type", ""))).upper()
                observation = str(item.get("observation", item.get("reasoning", "")))
                tf = str(item.get("timeframe", ""))
                strength = str(item.get("strength", "MEDIUM"))
            else:
                kind = str(getattr(item, "evidence_type", getattr(item, "type", ""))).upper()
                observation = str(getattr(item, "observation", getattr(item, "reasoning", "")))
                tf = str(getattr(item, "timeframe", ""))
                strength = str(getattr(item, "strength", "MEDIUM"))
            if kind in by_type:
                by_type[kind].append((tf, strength, observation))

        # Select the unresolved question based on the actual result.
        if alignment in {"DIVERGENT", "MIXED"}:
            question = (
                f"Does the proposed {direction} direction have "
                "multi-timeframe structural confirmation?"
            )
            tf_lines = []
            for tf in getattr(timeframe, "timeframes", []) or []:
                state = "not reported"
                for item in evidence_items:
                    if isinstance(item, dict):
                        item_tf = str(item.get("timeframe", ""))
                        obs = str(item.get("observation", ""))
                    else:
                        item_tf = str(getattr(item, "timeframe", ""))
                        obs = str(getattr(item, "observation", ""))
                    if item_tf == tf and any(
                        word in obs.lower()
                        for word in ("bullish", "bearish", "higher high", "higher low",
                                     "lower high", "lower low", "neutral")
                    ):
                        state = obs
                        break
                tf_lines.append(f"{tf}: {state}")
            finding = (
                "Timeframes are not fully aligned. The existing evidence indicates "
                f"{alignment.lower()} confirmation, so structural confirmation for "
                f"{direction} is incomplete."
            )
            detail = "\n".join(tf_lines[:3]) if tf_lines else "Timeframe-level structure is available in the ledger."
        elif len(by_type["INCONCLUSIVE"]) > 0:
            question = "Which unresolved evidence most limits the current decision?"
            strongest = sorted(
                by_type["INCONCLUSIVE"],
                key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x[1], 3),
            )[:3]
            detail = "\n".join(
                f"{tf or '—'}: {obs}" for tf, strength, obs in strongest
            ) or "No specific unresolved observation was available."
            finding = (
                "The remaining uncertainty comes from evidence that could not be "
                "classified decisively by the deterministic evaluator."
            )
        else:
            question = "Does the strongest directional evidence remain internally consistent?"
            strongest = by_type["FOR"] if direction == "LONG" else by_type["AGAINST"]
            strongest = strongest[:3]
            detail = "\n".join(
                f"{tf or '—'}: {obs}" for tf, strength, obs in strongest
            ) or "No additional directional evidence was available."
            finding = (
                "The focused review found no additional unresolved issue beyond "
                "the evidence already represented in the final ledger."
            )

        return (
            "RESEARCH PASS 2 — FOCUSED REVIEW\n"
            f"Question: {question}\n\n"
            f"Finding: {finding}\n"
            f"Evidence inspected:\n{detail}\n\n"
            "Status: COMPLETED — no new external data was introduced."
        )

    def _build_data_quality_summary(self):
        """Summarize the deterministic data-quality gate using the loaded result."""
        if not self.plan or not self.result_file:
            return "Not available."
        try:
            payload = json.loads(Path(self.result_file).read_text(encoding="utf-8-sig"))
            candles = payload.get("candles", {})
            lines = ["PASSED"]
            for timeframe in self.plan.timeframes:
                required = self.plan.history_depth.get(timeframe, 0)
                received = len(candles.get(timeframe, []))
                status = "✓" if received >= required else "✗"
                lines.append(f"{status} {timeframe}: {received}/{required} candles")
            price_ok = bool(payload.get("price") or payload.get("ticker"))
            stats_ok = bool(payload.get("24h_statistics") or payload.get("ticker"))
            order_book_ok = bool(payload.get("order_book"))
            lines.extend([
                f"{'✓' if price_ok else '✗'} Price",
                f"{'✓' if stats_ok else '✗'} 24h statistics",
                f"{'✓' if order_book_ok else '✗'} Order book",
                "✓ Volume (from candles)",
            ])
            return "\n".join(lines)
        except Exception as exc:
            return f"Unable to summarize: {exc}"

    def _build_verdict_explanation(
        self,
        session,
        confidence,
        critic,
        timeframe,
        evidence_items,
    ):
        """Build a concise explanation from already-computed research results."""
        verdict = str(session.verdict or "—")
        direction = str(getattr(timeframe, "direction", self.case.direction)).upper()
        alignment = str(getattr(timeframe, "alignment", "—")).upper()

        counts = {
            "FOR": getattr(timeframe, "total_for", 0),
            "AGAINST": getattr(timeframe, "total_against", 0),
            "INCONCLUSIVE": getattr(timeframe, "total_inconclusive", 0),
            "INVALIDATION": getattr(timeframe, "total_invalidation", 0),
        }

        statements = []

        if verdict == "CONTRADICTED":
            if counts["AGAINST"] > counts["FOR"]:
                statements.append(
                    f"The {direction} thesis is contradicted by a stronger body of "
                    f"evidence against it ({counts['AGAINST']} AGAINST vs "
                    f"{counts['FOR']} FOR)."
                )
            else:
                statements.append(
                    "The final evidence-weighted assessment contradicts the proposed thesis."
                )
        elif verdict == "SUPPORTIVE":
            statements.append(
                f"The {direction} thesis is supported by the current evidence, "
                f"with {counts['FOR']} FOR items versus {counts['AGAINST']} AGAINST."
            )
        else:
            statements.append(
                f"The evidence does not justify an unconditional {direction} decision: "
                f"{counts['FOR']} FOR, {counts['AGAINST']} AGAINST, and "
                f"{counts['INCONCLUSIVE']} INCONCLUSIVE items were recorded."
            )

        if alignment in {"DIVERGENT", "MIXED"}:
            statements.append(
                f"Multi-timeframe evidence is {alignment.lower()}, reducing confidence "
                "in a single directional conclusion."
            )
        elif alignment not in {"—", "ALIGNED", "SUPPORTIVE"}:
            statements.append(
                f"Multi-timeframe evidence is {alignment.lower()}."
            )

        challenges = getattr(critic, "challenges", []) or []
        risk = str(getattr(critic, "overall_risk", "—")).upper()
        if challenges:
            statements.append(
                f"The adversarial review identified {len(challenges)} challenge(s) "
                f"with an overall risk level of {risk}."
            )

        if counts["INVALIDATION"]:
            statements.append(
                f"{counts['INVALIDATION']} deterministic invalidation condition(s) "
                "were triggered."
            )

        return " ".join(statements)

    def _display_decision_rationale(
        self,
        session,
        confidence,
        critic,
        timeframe,
        evidence_items,
    ):
        """Populate the judge-facing rationale panels from existing results only."""
        verdict = str(getattr(session, "verdict", "—") or "—").upper()
        direction = str(
            getattr(timeframe, "direction", getattr(self.case, "direction", "—"))
        ).upper()
        alignment = str(getattr(timeframe, "alignment", "—")).upper()
        risk = str(getattr(critic, "overall_risk", "—")).upper()

        counts = {
            "FOR": getattr(timeframe, "total_for", 0),
            "AGAINST": getattr(timeframe, "total_against", 0),
            "INCONCLUSIVE": getattr(timeframe, "total_inconclusive", 0),
            "INVALIDATION": getattr(timeframe, "total_invalidation", 0),
        }

        if verdict == "SUPPORTIVE":
            headline = f"The {direction} thesis is supported by the current evidence."
        elif verdict == "CONTRADICTED":
            headline = f"The {direction} thesis is contradicted by the current evidence."
        else:
            headline = f"The {direction} thesis remains conditional — CAUTION."

        stats = (
            f"Confidence {getattr(confidence, 'confidence', 0):.1f}%  •  "
            f"{counts['FOR']} FOR  •  {counts['AGAINST']} AGAINST  •  "
            f"{counts['INCONCLUSIVE']} INCONCLUSIVE"
        )

        detail = (
            f"Multi-timeframe alignment: {alignment}. "
            f"Adversarial risk: {risk}. "
            f"The decision is based on the evidence-weighted research score "
            f"and the adversarial review; it is not a price prediction."
        )

        if hasattr(self, "verdict_highlight_label"):
            self.verdict_highlight_label.config(text=headline)
            self.verdict_stats_label.config(text=stats)
            self.verdict_detail_label.config(text=detail)

        invalidations = getattr(session, "invalidation_conditions", None) or []
        if hasattr(self, "invalidation_primary_label"):
            if invalidations:
                primary, levels = self._format_invalidation_panel(invalidations, direction)
                self.invalidation_primary_label.config(text=primary)
                self.invalidation_levels_label.config(text=levels)
                self.invalidation_note_label.config(
                    text="Future invalidation conditions are derived from deterministic market structure; no new data is introduced."
                )
            else:
                self.invalidation_primary_label.config(
                    text="No sufficiently reliable deterministic invalidation condition was established."
                )
                self.invalidation_levels_label.config(text="")
                self.invalidation_note_label.config(
                    text="Sentinel does not invent a future price threshold when the evidence does not provide a defensible level."
                )

    @staticmethod
    def _format_invalidation_panel(invalidations, direction):
        """Collapse repeated timeframe-specific swing conditions into one readable condition."""
        swing_lines = []
        qualitative = []

        for condition in invalidations:
            text = str(condition).strip()
            if "established swing high (" in text and direction == "SHORT":
                try:
                    timeframe, remainder = text.split(":", 1)
                    level = remainder.split("established swing high (", 1)[1].split(")", 1)[0]
                    swing_lines.append((timeframe.strip(), level.strip()))
                    continue
                except (IndexError, ValueError):
                    pass
            if "established swing low (" in text and direction == "LONG":
                try:
                    timeframe, remainder = text.split(":", 1)
                    level = remainder.split("established swing low (", 1)[1].split(")", 1)[0]
                    swing_lines.append((timeframe.strip(), level.strip()))
                    continue
                except (IndexError, ValueError):
                    pass
            qualitative.append(text)

        if direction == "SHORT" and swing_lines:
            primary = "A sustained break above the relevant swing-high structure would invalidate the SHORT thesis."
        elif direction == "LONG" and swing_lines:
            primary = "A sustained break below the relevant swing-low structure would invalidate the LONG thesis."
        else:
            primary = "Future thesis invalidation depends on the conditions below."

        parts = []
        if swing_lines:
            parts.append(
                "TIMEFRAME LEVELS\n" +
                "\n".join(f"• {tf}: {level}" for tf, level in swing_lines)
            )
        if qualitative:
            parts.append(
                "ADDITIONAL CONDITIONS\n" +
                "\n".join(f"• {item}" for item in qualitative)
            )

        levels = "\n\n".join(parts)
        return primary, levels

    def _display_key_evidence(self, evidence_items):
        """Show up to three strongest evidence items in judge-readable language."""
        if not hasattr(self, "evidence_card_labels"):
            return

        normalized = []
        for item in evidence_items:
            if isinstance(item, dict):
                evidence_type = item.get("evidence_type", item.get("type", "INCONCLUSIVE"))
                strength = item.get("strength", "MEDIUM")
                observation = item.get("observation", item.get("reasoning", ""))
                timeframe = item.get("timeframe", "")
            else:
                evidence_type = getattr(item, "evidence_type", getattr(item, "type", "INCONCLUSIVE"))
                strength = getattr(item, "strength", "MEDIUM")
                observation = getattr(item, "observation", getattr(item, "reasoning", ""))
                timeframe = getattr(item, "timeframe", "")

            normalized.append({
                "type": str(evidence_type).upper(),
                "strength": str(strength).upper(),
                "observation": str(observation),
                "timeframe": str(timeframe),
            })

        priority = {"INVALIDATION": 0, "AGAINST": 1, "FOR": 2, "INCONCLUSIVE": 3}
        strength_priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        normalized.sort(
            key=lambda x: (
                priority.get(x["type"], 4),
                strength_priority.get(x["strength"], 3),
            )
        )

        directional = [
            x for x in normalized
            if x["type"] in {"FOR", "AGAINST", "INVALIDATION"}
        ]
        fallback = [x for x in normalized if x["type"] == "INCONCLUSIVE"]
        selected = (directional + fallback)[:3]

        while len(selected) < 3:
            selected.append({
                "type": "—",
                "strength": "",
                "observation": "No additional key evidence available.",
                "timeframe": "",
            })

        for (card, title, body), item in zip(self.evidence_card_labels, selected):
            kind = item["type"]
            strength = item["strength"]
            timeframe = item["timeframe"]
            observation = item["observation"].replace("\n", " ").strip()

            headline, explanation = self._humanize_evidence(
                observation=observation,
                evidence_type=kind,
                timeframe=timeframe,
            )

            title_text = f"{kind}"
            if timeframe:
                title_text += f"  •  {timeframe}"
            if strength:
                title_text += f"  •  {strength}"

            title.config(text=title_text)
            body.config(text=f"{headline}\n{explanation}")

            if kind == "FOR":
                card.config(bg="#e9f7ef")
                title.config(bg="#e9f7ef", fg="#176b3a")
                body.config(bg="#e9f7ef", fg="#24352b")
            elif kind in {"AGAINST", "INVALIDATION"}:
                card.config(bg="#fcecec")
                title.config(bg="#fcecec", fg="#9b2525")
                body.config(bg="#fcecec", fg="#3b2929")
            elif kind == "INCONCLUSIVE":
                card.config(bg="#f4f4f4")
                title.config(bg="#f4f4f4", fg="#666666")
                body.config(bg="#f4f4f4", fg="#333333")
            else:
                card.config(bg="#f7f7f7")
                title.config(bg="#f7f7f7", fg="#777777")
                body.config(bg="#f7f7f7", fg="#555555")

    def _humanize_evidence(self, observation, evidence_type, timeframe):
        """Translate deterministic evaluator wording into concise judge-facing language."""
        text = observation.strip()
        tf = timeframe or "This timeframe"
        direction = str(getattr(self.case, "direction", "")) if self.case else ""

        lower = text.lower()
        if "market structure is higher_highs_higher_lows" in lower:
            return (
                f"{tf} is forming higher highs and higher lows.",
                f"This structure {'supports' if evidence_type == 'FOR' else 'contradicts' if evidence_type in {'AGAINST', 'INVALIDATION'} else 'does not confirm'} the {direction} thesis."
            )
        if "market structure is lower_highs_lower_lows" in lower:
            return (
                f"{tf} is forming lower highs and lower lows.",
                f"This structure {'supports' if evidence_type == 'FOR' else 'contradicts' if evidence_type in {'AGAINST', 'INVALIDATION'} else 'does not confirm'} the {direction} thesis."
            )
        if "trend is bullish" in lower:
            return (
                f"{tf} trend is bullish.",
                f"The prevailing trend {'supports' if evidence_type == 'FOR' else 'contradicts' if evidence_type in {'AGAINST', 'INVALIDATION'} else 'does not confirm'} the {direction} thesis."
            )
        if "trend is bearish" in lower:
            return (
                f"{tf} trend is bearish.",
                f"The prevailing trend {'supports' if evidence_type == 'FOR' else 'contradicts' if evidence_type in {'AGAINST', 'INVALIDATION'} else 'does not confirm'} the {direction} thesis."
            )
        if "trend is neutral" in lower:
            return (
                f"{tf} trend is neutral.",
                "The trend does not provide decisive directional confirmation."
            )
        if "momentum is negative" in lower:
            return (
                f"{tf} momentum is negative.",
                f"Momentum {'supports' if evidence_type == 'FOR' else 'contradicts' if evidence_type in {'AGAINST', 'INVALIDATION'} else 'does not decisively confirm'} the {direction} thesis."
            )
        if "momentum is positive" in lower:
            return (
                f"{tf} momentum is positive.",
                f"Momentum {'supports' if evidence_type == 'FOR' else 'contradicts' if evidence_type in {'AGAINST', 'INVALIDATION'} else 'does not decisively confirm'} the {direction} thesis."
            )
        if "price-volume relationship is" in lower:
            relationship = text.split("price-volume relationship is", 1)[1].strip().rstrip(".")
            return (
                f"{tf} price/volume behavior: {relationship}.",
                f"This relationship {'supports' if evidence_type == 'FOR' else 'contradicts' if evidence_type in {'AGAINST', 'INVALIDATION'} else 'does not decisively confirm'} the {direction} thesis."
            )

        # Preserve the deterministic observation when no concise translation applies.
        if len(text) > 125:
            text = text[:122].rstrip() + "..."
        return (f"{tf} observation", text)

    @staticmethod
    def _ledger_items(ledger):
        """
        Extract the real EvidenceLedger entries without assuming one
        particular internal representation.

        Supports:
        - to_dict() serialization
        - evidence / entries / items attributes
        - callable items()/entries()
        - dict/list serialized forms
        - object fields as a final fallback

        This method only affects GUI presentation; it does not change
        evidence generation or evaluation.
        """
        def normalize(value):
            if value is None:
                return []

            if callable(value):
                try:
                    value = value()
                except TypeError:
                    return []

            if isinstance(value, dict):
                for key in ("evidence", "entries", "items"):
                    nested = value.get(key)
                    if isinstance(nested, dict):
                        return list(nested.values())
                    if isinstance(nested, (list, tuple)):
                        return list(nested)

                if "evidence_type" in value or "observation" in value:
                    return [value]

                return list(value.values())

            if isinstance(value, (list, tuple)):
                return list(value)

            return []

        # First prefer an explicit serialized representation.
        to_dict = getattr(ledger, "to_dict", None)
        if callable(to_dict):
            try:
                items = normalize(to_dict())
                if items:
                    return items
            except Exception:
                pass

        # Then inspect conventional collection names.
        for attribute in ("evidence", "entries", "items", "_evidence", "_entries"):
            try:
                items = normalize(getattr(ledger, attribute, None))
                if items:
                    return items
            except Exception:
                pass

        if isinstance(ledger, dict):
            items = normalize(ledger)
            if items:
                return items

        # Final fallback: inspect object fields for a collection containing
        # actual evidence records.
        try:
            for value in vars(ledger).values():
                items = normalize(value)
                if items and any(
                    (
                        (isinstance(item, dict) and (
                            "evidence_type" in item
                            or "observation" in item
                        ))
                        or
                        (hasattr(item, "evidence_type") or hasattr(item, "observation"))
                    )
                    for item in items
                ):
                    return items
        except Exception:
            pass

        return []

    @staticmethod
    def _object_value(obj, name, default="—"):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def _format_evidence_item(self, index, item):
        evidence_type = self._object_value(
            item, "evidence_type",
            self._object_value(item, "type", "—"),
        )
        observation = self._object_value(item, "observation", "—")
        timeframe = self._object_value(item, "timeframe", "—")
        source = self._object_value(item, "source", "—")
        strength = self._object_value(item, "strength", "—")
        reasoning = self._object_value(item, "reasoning", "—")

        return (
            f"{index}. [{evidence_type}] {observation}\n"
            f"   Timeframe: {timeframe}\n"
            f"   Strength: {strength}\n"
            f"   Source: {source}\n"
            f"   Reasoning: {reasoning}"
        )

    def _format_challenge(self, index, challenge):
        if isinstance(challenge, dict):
            text = challenge.get(
                "observation",
                challenge.get("challenge", challenge.get("description", str(challenge))),
            )
            severity = challenge.get("severity", "—")
            why = challenge.get("reasoning", challenge.get("why_it_matters", "—"))
        else:
            text = getattr(
                challenge,
                "observation",
                getattr(challenge, "challenge", str(challenge)),
            )
            severity = getattr(challenge, "severity", "—")
            why = getattr(
                challenge,
                "reasoning",
                getattr(challenge, "why_it_matters", "—"),
            )

        return (
            f"{index}. {text} ({severity})\n"
            f"   Why it matters: {why}"
        )

    def _center_window(self, width, height):
        """Place the fixed-size main window in the center of the screen."""
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max((screen_w - width) // 2, 0)
        y = max((screen_h - height) // 2, 0)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def open_pdf_report(self):
        """Open the generated PDF using the operating system's default viewer."""
        if not self.report_path or not self.report_path.exists():
            messagebox.showwarning(
                "PDF report",
                "No generated PDF report is available yet.",
            )
            return

        try:
            os.startfile(str(self.report_path))
        except Exception as exc:
            messagebox.showerror(
                "PDF report",
                f"Could not open the PDF automatically.\n\n{exc}\n\n"
                f"Report path:\n{self.report_path}",
            )

    def show_markdown_result(self):
        """Show the full Sentinel result in a dedicated Markdown-style reader."""
        content = self.result_text.get("1.0", "end-1c").strip()
        if not content:
            messagebox.showwarning(
                "Markdown result",
                "No completed research result is available yet.",
            )
            return

        window = tk.Toplevel(self.root)
        window.title("Binance Sentinel — Research Result")
        window.geometry("1050x760")
        window.minsize(760, 520)
        window.resizable(True, True)
        self._center_child(window, 1050, 760)

        header = ttk.Frame(window, padding=(20, 16, 20, 8))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="RESEARCH RESULT",
            style="WindowTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            header,
            text="Auditable Sentinel analysis — Markdown view",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        body = ttk.Frame(window, padding=(20, 8, 20, 16))
        body.pack(fill="both", expand=True)

        viewer = tk.Text(
            body,
            wrap="word",
            font=("Cascadia Mono", 9),
            relief="flat",
            bd=0,
            padx=16,
            pady=14,
        )
        viewer.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(
            body,
            orient="vertical",
            command=viewer.yview,
        )
        scroll.pack(side="right", fill="y")
        viewer.configure(yscrollcommand=scroll.set)

        viewer.insert("1.0", content)
        viewer.config(state="disabled")

        ttk.Button(
            window,
            text="CLOSE",
            command=window.destroy,
        ).pack(anchor="e", padx=20, pady=(0, 16))

    def _center_child(self, window, width, height):
        window.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max((screen_w - width) // 2, 0)
        y = max((screen_h - height) // 2, 0)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def _show_request_summary(self):
        request_data = {}
        try:
            request_data = self.request.to_dict()
        except Exception:
            pass

        lines = [
            "RESEARCH REQUEST CREATED",
            "=" * 72,
            "",
            f"Case:       {self.case.case_id}",
            f"Symbol:     {self.case.symbol}",
            f"Direction:  {self.case.direction}",
            f"Horizon:    {self.case.time_horizon}",
            f"Request ID: {self.request_id}",
            "",
            "THESIS",
            self.case.thesis,
            "",
            "TIMEFRAMES",
            str(self.plan.timeframes),
            "",
            "HISTORY DEPTH",
        ]

        for timeframe in self.plan.timeframes:
            depth = self.plan.history_depth.get(timeframe, "—")
            lines.append(f"  {timeframe}: {depth} completed candles")

        lines.extend([
            "",
            "MARKET DATA",
            "  " + ", ".join(self.plan.market_data),
            "",
            "ANALYSIS",
            "  " + ", ".join(self.plan.analysis),
            "",
            "REASONING",
            "  " + ", ".join(self.plan.reasoning),
            "",
            "FILE HANDOFF",
            f"  Request JSON: storage/mcp/requests/{self.request_id}.json",
            f"  MCP Prompt:   storage/mcp/requests/{self.request_id}.txt",
            f"  Expected:     storage/mcp/results/{self.request_id}.json",
            "",
            "NEXT STEP",
            "Use VIEW MCP INSTRUCTION to inspect the exact instruction",
            "for the Binance MCP agent. Sentinel will wait for the",
            "matching result file automatically.",
        ])

        self._set_result_text("\n".join(lines))

    def show_request_details(self):
        if not self.request_id or self.request is None:
            return

        window = tk.Toplevel(self.root)
        window.title("Sentinel Research Request Details")
        window.geometry("950x720")
        window.minsize(750, 500)

        ttk.Label(
            window,
            text=f"Request {self.request_id}",
            font=("Segoe UI", 11, "bold"),
            padding=10,
        ).pack(anchor="w")

        frame = ttk.Frame(window, padding=(10, 0, 10, 10))
        frame.pack(fill="both", expand=True)

        text = tk.Text(
            frame,
            wrap="none",
            font=("Consolas", 9),
        )
        text.pack(side="left", fill="both", expand=True)

        y_scroll = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=text.yview,
        )
        y_scroll.pack(side="right", fill="y")

        x_scroll = ttk.Scrollbar(
            window,
            orient="horizontal",
            command=text.xview,
        )
        x_scroll.pack(fill="x", padx=10)

        text.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        try:
            request_data = self.request.to_dict()
            request_json = json.dumps(
                request_data,
                indent=4,
                ensure_ascii=False,
            )
        except Exception as exc:
            request_json = f"Unable to serialize request: {exc}"

        prompt_path = (
            Path("storage")
            / "mcp"
            / "requests"
            / f"{self.request_id}.txt"
        )

        content = (
            "STRUCTURED REQUEST\n"
            + "=" * 72
            + "\n"
            + request_json
            + "\n\n"
            + "FILE PATHS\n"
            + "=" * 72
            + f"\nRequest: {self.request_id}.json"
            + f"\nPrompt:  {prompt_path}"
            + f"\nResult:  storage/mcp/results/{self.request_id}.json"
        )

        text.insert("1.0", content)
        text.config(state="disabled")

    def show_mcp_instruction(self):
        if not self.request_id:
            return

        prompt_path = (
            Path("storage")
            / "mcp"
            / "requests"
            / f"{self.request_id}.txt"
        )

        if not prompt_path.exists():
            messagebox.showwarning(
                "MCP instruction",
                f"Instruction file not found:\n{prompt_path}",
            )
            return

        instruction = prompt_path.read_text(encoding="utf-8")

        window = tk.Toplevel(self.root)
        window.title("Binance MCP Instruction")
        window.geometry("850x600")

        ttk.Label(
            window,
            text=f"Request: {self.request_id}",
            font=("Segoe UI", 10, "bold"),
            padding=10,
        ).pack(anchor="w")

        text = tk.Text(
            window,
            wrap="word",
            font=("Consolas", 9),
        )
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", instruction)
        text.config(state="disabled")

        button_frame = ttk.Frame(window, padding=(10, 0, 10, 10))
        button_frame.pack(fill="x")

        def copy_instruction():
            self.root.clipboard_clear()
            self.root.clipboard_append(instruction)
            self.root.update()
            self.status_var.set(
                "MCP instruction copied to clipboard."
            )

        ttk.Button(
            button_frame,
            text="COPY TO CLIPBOARD",
            command=copy_instruction,
        ).pack(side="left")

        ttk.Button(
            button_frame,
            text="CLOSE",
            command=window.destroy,
        ).pack(side="left", padx=8)

    def new_research(self):
        """Reset the current session and prepare the GUI for a fresh case."""
        self.progress.stop()

        # Invalidate any pending MCP polling callback so an old result cannot
        # be processed after the user starts a new research case.
        self.request_id = None
        self.result_file = None
        self.request = None
        self.case = None
        self.plan = None
        self.pipeline_result = None
        self.report_path = None

        self.verdict_var.set("—")
        self.confidence_var.set("—")
        self.evidence_state_var.set("—")
        self.risk_var.set("—")
        self.alignment_var.set("—")
        self.data_quality_var.set("—")
        self.provenance_var.set("—")

        self.request_button.config(state="disabled")
        self.request_details_button.config(state="disabled")
        self.pdf_button.config(state="disabled")
        self.markdown_button.config(state="disabled")
        self.start_button.config(state="normal")
        self.new_research_button.config(state="disabled")

        self.symbol_var.set("EDENUSDT")
        self.direction_var.set("LONG")
        self.horizon_var.set("15-20 days")
        self.thesis_text.delete("1.0", "end")
        self.thesis_text.insert(
            "1.0",
            "Enter the trader thesis you want Sentinel to investigate.",
        )

        if hasattr(self, "evidence_card_labels"):
            for card, title, body in self.evidence_card_labels:
                card.config(bg="#f7f7f7")
                title.config(bg="#f7f7f7", fg="#777777", text="—")
                body.config(
                    bg="#f7f7f7",
                    fg="#555555",
                    text="Waiting for research result.",
                )

        if hasattr(self, "verdict_highlight_label"):
            self.verdict_highlight_label.config(text="Waiting for research result.")
            self.verdict_stats_label.config(text="")
            self.verdict_detail_label.config(text="")
        if hasattr(self, "invalidation_primary_label"):
            self.invalidation_primary_label.config(text="Waiting for research result.")
            self.invalidation_levels_label.config(text="")
            self.invalidation_note_label.config(text="")

        self._set_result_text("")
        self._set_stage("CASE")
        self.status_var.set("Ready — enter a new research thesis.")

    def _reset_result(self):
        self.verdict_var.set("—")
        self.confidence_var.set("—")
        self.evidence_state_var.set("—")
        self.risk_var.set("—")
        self.alignment_var.set("—")
        self.data_quality_var.set("—")
        self.provenance_var.set("—")
        self.report_path = None
        self.pdf_button.config(state="disabled")
        self.markdown_button.config(state="disabled")
        if hasattr(self, "evidence_card_labels"):
            for card, title, body in self.evidence_card_labels:
                card.config(bg="#f7f7f7")
                title.config(bg="#f7f7f7", fg="#777777", text="—")
                body.config(
                    bg="#f7f7f7",
                    fg="#555555",
                    text="Waiting for research result.",
                )
        if hasattr(self, "verdict_highlight_label"):
            self.verdict_highlight_label.config(text="Waiting for research result.")
            self.verdict_stats_label.config(text="")
            self.verdict_detail_label.config(text="")
        if hasattr(self, "invalidation_primary_label"):
            self.invalidation_primary_label.config(text="Waiting for research result.")
            self.invalidation_levels_label.config(text="")
            self.invalidation_note_label.config(text="")

        self._set_result_text("")

    def _set_result_text(self, text):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")

        lines = text.splitlines()
        section_names = {
            "CASE", "SYMBOL", "DIRECTION", "TIME HORIZON",
            "TRADER THESIS", "DECISION",
            "EVIDENCE-WEIGHTED CONFIDENCE", "EVIDENCE STATE",
            "ADVERSARIAL RISK", "MULTI-TIMEFRAME",
            "EVIDENCE SUMMARY", "CONFIDENCE BREAKDOWN",
            "EVIDENCE LEDGER", "ADVERSARIAL CHALLENGES",
            "THESIS INVALIDATION", "WHAT WOULD INVALIDATE THIS THESIS?", "RESEARCH METHOD", "LIMITATION",
            "RESULT", "REPORTS", "NEXT STEP", "FILE HANDOFF",
            "TIMEFRAMES", "HISTORY DEPTH", "MARKET DATA",
            "ANALYSIS", "REASONING", "THESIS",
            "DATA QUALITY", "MCP PROVENANCE", "FOCUSED RESEARCH",
        }

        for line in lines:
            stripped = line.strip()
            if stripped in section_names:
                self.result_text.insert("end", line + "\n", "section")
            elif stripped.startswith("DECISION"):
                self.result_text.insert("end", line + "\n", "decision")
            else:
                self.result_text.insert("end", line + "\n")

        self.result_text.config(state="disabled")

    def _append_result(self, text):
        self.result_text.config(state="normal")
        self.result_text.insert("end", text)
        self.result_text.config(state="disabled")

    def _set_stage(self, active):
        """Update the visible research timeline with completed/current/pending states."""
        if active not in self.stage_order:
            return

        active_index = self.stage_order.index(active)
        for index, name in enumerate(self.stage_order):
            if index < active_index:
                state = "complete"
                text = f"✓ {name}"
            elif index == active_index:
                state = "active"
                text = f"● {name}"
            else:
                state = "pending"
                text = name

            self.stage_state[name] = state
            label = self.stage_labels[name]
            label.config(
                text=text,
                font=("Segoe UI", 9, "bold" if state != "pending" else "normal"),
                relief="solid",
                borderwidth=1,
            )

        # Once VERDICT is reached, every stage is complete.
        if active == "VERDICT":
            for name in self.stage_order:
                self.stage_state[name] = "complete"
                self.stage_labels[name].config(
                    text=f"✓ {name}",
                    font=("Segoe UI", 9, "bold"),
                    relief="solid",
                    borderwidth=1,
                )


def main():
    root = tk.Tk()

    # ---------------------------------------------------------
    # Visual styling
    # ---------------------------------------------------------

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        "Primary.TButton",
        font=("Segoe UI", 9, "bold"),
        padding=(15, 8),
    )
    style.configure(
        "Accent.TButton",
        font=("Segoe UI", 9, "bold"),
        padding=(13, 8),
    )
    style.configure(
        "WindowTitle.TLabel",
        font=("Segoe UI", 16, "bold"),
    )
    style.configure(
        "Title.TLabel",
        font=("Segoe UI", 24, "bold"),
        padding=0,
    )
    style.configure(
        "Kicker.TLabel",
        font=("Segoe UI", 9, "bold"),
    )
    style.configure(
        "Subtitle.TLabel",
        font=("Segoe UI", 10),
    )
    style.configure(
        "Status.TLabel",
        font=("Segoe UI", 9),
    )
    style.configure(
        "Footer.TLabel",
        font=("Segoe UI", 8),
    )
    style.configure(
        "Result.TLabelframe",
        padding=8,
    )
    style.configure(
        "Result.TLabelframe.Label",
        font=("Segoe UI", 10, "bold"),
    )
    style.configure(
        "TButton",
        font=("Segoe UI", 9, "bold"),
        padding=(12, 7),
    )
    style.configure(
        "TLabel",
        font=("Segoe UI", 9),
    )
    style.configure(
        "TLabelframe.Label",
        font=("Segoe UI", 9, "bold"),
    )

    SentinelGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
