from jinja2 import Template
from app.services.diff_engine import DiffReport
import os
import uuid

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

class ReportGenerator:
    def __init__(self, output_dir: str = "/tmp/reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.template = Template(REPORT_TEMPLATE)

    def generate_html(self, report: DiffReport) -> str:
        return self.template.render(report=report)

    def save_report(self, report: DiffReport) -> str:
        html_content = self.generate_html(report)
        filename = f"diff_report_{report.current_run_id}.html"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as f:
            f.write(html_content)
        return filepath
