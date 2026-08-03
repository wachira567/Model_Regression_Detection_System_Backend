from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from jinja2 import Template
from app.db.session import get_db
from app.services.diff_engine import DiffEngine

router = APIRouter()

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Eval Run Diff Report</title>
    <style>
        body { font-family: sans-serif; margin: 40px; }
        .critical { color: red; }
        .warning { color: orange; }
        .pass { color: green; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Diff Report: {{ report.current_run_id }} vs {{ report.baseline_run_id }}</h1>
    <h2 class="{{ report.severity }}">Severity: {{ report.severity | upper }}</h2>
    <p>{{ report.summary_text }}</p>
    
    <h3>Overall Deltas</h3>
    <ul>
        <li>Accuracy Delta: {{ "%.2f"|format(report.overall_delta.accuracy_delta * 100) }}%</li>
        <li>Relevance Delta: {{ "%.2f"|format(report.overall_delta.relevance_delta) }} points</li>
        <li>Latency Delta: {{ "%.2f"|format(report.overall_delta.latency_delta) }} ms</li>
    </ul>
    
    <h3>Regressions ({{ report.regressions | length }})</h3>
    {% if report.regressions %}
    <table>
        <tr><th>Test Case ID</th><th>Reason</th><th>Baseline Relev</th><th>Current Relev</th></tr>
        {% for reg in report.regressions %}
        <tr>
            <td>{{ reg.test_case_id }}</td>
            <td>{{ reg.reason }}</td>
            <td>{{ reg.baseline_relevance }}</td>
            <td>{{ reg.current_relevance }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No regressions found.</p>
    {% endif %}
</body>
</html>
"""

@router.get("/{curr_run_id}/diff/{base_run_id}", response_class=HTMLResponse)
async def generate_html_report(curr_run_id: str, base_run_id: str, db: AsyncSession = Depends(get_db)):
    diff_engine = DiffEngine(db)
    report = await diff_engine.compare(curr_run_id, base_run_id)
    if not report:
        raise HTTPException(status_code=404, detail="One or both runs not found")
        
    template = Template(REPORT_TEMPLATE)
    html_content = template.render(report=report)
    return HTMLResponse(content=html_content)
