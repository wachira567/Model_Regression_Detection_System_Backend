from dataclasses import dataclass
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.eval_run import EvalRun
from app.models.eval_result import EvalResult
from app.config import settings

@dataclass
class OverallDelta:
    accuracy_delta: float
    relevance_delta: float
    latency_delta: float

@dataclass
class CaseDiff:
    test_case_id: str
    baseline_status: str
    current_status: str
    baseline_relevance: float
    current_relevance: float
    baseline_error: str | None
    current_error: str | None
    reason: str

@dataclass
class DiffReport:
    current_run_id: str
    baseline_run_id: str
    overall_delta: OverallDelta
    regressions: list[CaseDiff]
    improvements: list[CaseDiff]
    new_failures: list[CaseDiff]
    stable_passes: list[str]
    stable_failures: list[str]
    severity: str
    summary_text: str

class DiffEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def compare(self, current_run_id: str, baseline_run_id: str) -> DiffReport | None:
        curr_run = await self.session.get(EvalRun, current_run_id)
        base_run = await self.session.get(EvalRun, baseline_run_id)

        if not curr_run or not base_run:
            return None

        # Fetch results
        curr_results = (await self.session.execute(select(EvalResult).where(EvalResult.eval_run_id == current_run_id))).scalars().all()
        base_results = (await self.session.execute(select(EvalResult).where(EvalResult.eval_run_id == baseline_run_id))).scalars().all()

        curr_map = {r.test_case_id: r for r in curr_results}
        base_map = {r.test_case_id: r for r in base_results}

        regressions = []
        improvements = []
        new_failures = []
        stable_passes = []
        stable_failures = []

        all_case_ids = set(curr_map.keys()).union(set(base_map.keys()))

        for cid in all_case_ids:
            curr = curr_map.get(cid)
            base = base_map.get(cid)

            if curr and base:
                if base.status == "pass" and curr.status != "pass":
                    regressions.append(CaseDiff(cid, base.status, curr.status, base.relevance_score, curr.relevance_score, base.error_message, curr.error_message, "Status flipped to fail"))
                elif base.status != "pass" and curr.status == "pass":
                    improvements.append(CaseDiff(cid, base.status, curr.status, base.relevance_score, curr.relevance_score, base.error_message, curr.error_message, "Status flipped to pass"))
                elif base.status == "pass" and curr.status == "pass":
                    if base.relevance_score - curr.relevance_score >= 2:
                        regressions.append(CaseDiff(cid, base.status, curr.status, base.relevance_score, curr.relevance_score, base.error_message, curr.error_message, "Relevance score dropped by >= 2"))
                    elif curr.relevance_score - base.relevance_score >= 2:
                        improvements.append(CaseDiff(cid, base.status, curr.status, base.relevance_score, curr.relevance_score, base.error_message, curr.error_message, "Relevance score improved by >= 2"))
                    else:
                        stable_passes.append(cid)
                else: # both failed
                    if base.error_message != curr.error_message:
                        new_failures.append(CaseDiff(cid, base.status, curr.status, base.relevance_score, curr.relevance_score, base.error_message, curr.error_message, "Different error message"))
                    else:
                        stable_failures.append(cid)
            elif curr:
                # new case in current
                if curr.status != "pass":
                    new_failures.append(CaseDiff(cid, "none", curr.status, 0.0, curr.relevance_score, None, curr.error_message, "New test case failed"))
                else:
                    improvements.append(CaseDiff(cid, "none", curr.status, 0.0, curr.relevance_score, None, curr.error_message, "New test case passed"))
            elif base:
                # case removed in current
                pass

        acc_delta = (curr_run.overall_accuracy or 0) - (base_run.overall_accuracy or 0)
        rel_delta = (curr_run.avg_relevance_score or 0) - (base_run.avg_relevance_score or 0)
        lat_delta = (curr_run.avg_latency_ms or 0) - (base_run.avg_latency_ms or 0)

        severity = "pass"
        if acc_delta <= -settings.REGRESSION_CRITICAL_THRESHOLD:
            severity = "critical"
        elif acc_delta <= -settings.REGRESSION_WARNING_THRESHOLD:
            severity = "warning"

        report = DiffReport(
            current_run_id=current_run_id,
            baseline_run_id=baseline_run_id,
            overall_delta=OverallDelta(acc_delta, rel_delta, lat_delta),
            regressions=regressions,
            improvements=improvements,
            new_failures=new_failures,
            stable_passes=stable_passes,
            stable_failures=stable_failures,
            severity=severity,
            summary_text=f"Diff: {len(regressions)} regressions, {len(improvements)} improvements. Severity: {severity}"
        )
        return report
