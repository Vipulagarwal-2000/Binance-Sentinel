"""
Binance Sentinel
Evidence persistence integration test.
"""

from analysis.evidence import EvidenceLedger
from research.case_manager import CaseManager
from research.plan_manager import PlanManager
from research.session import SessionManager


def main():

    print("=" * 50)
    print("       SESSION EVIDENCE TEST")
    print("=" * 50)
    print()

    # --------------------------------------------------
    # 1. Create case
    # --------------------------------------------------

    case_manager = CaseManager()

    case = case_manager.create_case(
        name="Evidence Persistence Test",
        symbol="TESTUSDT",
        direction="LONG",
        time_horizon="15 days",
        thesis=(
            "Test whether evidence can be persisted "
            "inside a research session."
        ),
    )

    print("[1] Case created:")
    print(f"    {case.case_id}")
    print()

    # --------------------------------------------------
    # 2. Load research plan
    # --------------------------------------------------

    plan_manager = PlanManager()

    plan = plan_manager.load_plan(
        case.case_id
    )

    print("[2] Research plan loaded.")
    print()

    # --------------------------------------------------
    # 3. Create session
    # --------------------------------------------------

    session_manager = SessionManager()

    session = session_manager.create_session(
        case_id=case.case_id,
        thesis=case.thesis,
        direction=case.direction,
        time_horizon=case.time_horizon,
        research_plan=plan.to_dict(),
    )

    print("[3] Session created:")
    print(f"    {session.session_id}")
    print()

    # --------------------------------------------------
    # 4. Create evidence
    # --------------------------------------------------

    ledger = EvidenceLedger()

    ledger.add(
        evidence_type="FOR",
        observation=(
            "4H trend is bullish."
        ),
        timeframe="4H",
        source="python_market_analysis",
        strength="MEDIUM",
        reasoning=(
            "Bullish structure supports the "
            "long thesis."
        ),
    )

    ledger.add(
        evidence_type="AGAINST",
        observation=(
            "Price is near resistance."
        ),
        timeframe="4H",
        source="python_market_analysis",
        strength="MEDIUM",
        reasoning=(
            "Resistance may restrict upside."
        ),
    )

    ledger.add(
        evidence_type="INVALIDATION",
        observation=(
            "Break below structural support."
        ),
        timeframe="4H",
        source="research_plan",
        strength="HIGH",
        reasoning=(
            "A sustained support break would "
            "invalidate the long thesis."
        ),
    )

    print("[4] Evidence created:")
    print(f"    {ledger.summary()}")
    print()

    # --------------------------------------------------
    # 5. Save evidence into session
    # --------------------------------------------------

    session_manager.save_evidence(
        session,
        ledger,
    )

    print("[5] Evidence saved to session.")
    print()

    # --------------------------------------------------
    # 6. Reload session from disk
    # --------------------------------------------------

    loaded_session = (
        session_manager.load_session(
            case.case_id,
            session.session_id,
        )
    )

    print("[6] Session reloaded from disk.")
    print(
        f"    Evidence count: "
        f"{len(loaded_session.evidence)}"
    )

    print()

    # --------------------------------------------------
    # 7. Verify
    # --------------------------------------------------

    assert len(
        loaded_session.evidence
    ) == 3

    assert (
        loaded_session.evidence[0]
        ["evidence_type"]
        == "FOR"
    )

    assert (
        loaded_session.evidence[1]
        ["evidence_type"]
        == "AGAINST"
    )

    assert (
        loaded_session.evidence[2]
        ["evidence_type"]
        == "INVALIDATION"
    )

    print("[7] Persistence verification passed.")
    print()

    print("=" * 50)
    print("SESSION EVIDENCE TEST PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()