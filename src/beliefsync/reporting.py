from __future__ import annotations

import json

from .models import AnalysisReport


class ReportRenderer:
    def render_text(self, report: AnalysisReport, max_actions: int = 5) -> str:
        stale = [item for item in report.assessments if item.stale_probability >= 0.5]
        lines = [
            f"Beliefs: {len(report.beliefs)}",
            f"Potentially stale beliefs: {len(stale)}",
            "Top revalidation actions:",
        ]
        for idx, action in enumerate(report.actions[:max_actions], start=1):
            lines.append(f"{idx}. {action.action_type.value}: {action.target} | score={action.score():.3f}")
        return "\n".join(lines)

    def render_markdown(self, report: AnalysisReport, max_actions: int = 10) -> str:
        stale = [item for item in report.assessments if item.stale_probability >= 0.5]
        lines = [
            "# BeliefSync Report",
            "",
            "## Summary",
            "",
            f"- Beliefs: `{len(report.beliefs)}`",
            f"- Potentially stale beliefs: `{len(stale)}`",
            f"- Candidate revalidation actions: `{len(report.actions)}`",
            "",
            "## Stale Beliefs",
            "",
        ]
        if not report.assessments:
            lines.append("No assessments available.")
        else:
            for assessment in report.assessments:
                lines.append(
                    f"- `{assessment.belief_id}` | stale_probability=`{assessment.stale_probability}` | reasons={', '.join(assessment.reasons) or 'none'}"
                )
        lines.extend(["", "## Recommended Actions", ""])
        if not report.actions:
            lines.append("No actions generated.")
        else:
            for idx, action in enumerate(report.actions[:max_actions], start=1):
                lines.append(
                    f"{idx}. `{action.action_type.value}` -> `{action.target}` | score=`{action.score():.3f}` | rationale={action.rationale}"
                )
        return "\n".join(lines)

    def render_json(self, report: AnalysisReport) -> str:
        return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)

    def render_html(self, report: AnalysisReport, title: str = "BeliefSync Report") -> str:
        stale = [item for item in report.assessments if item.stale_probability >= 0.5]
        action_items = "".join(
            (
                f"<li><code>{action.action_type.value}</code> -> <code>{_escape_html(action.target)}</code> "
                f"(score={action.score():.3f})<br><small>{_escape_html(action.rationale)}</small></li>"
            )
            for action in report.actions
        ) or "<li>No actions generated.</li>"
        stale_items = "".join(
            (
                f"<tr><td><code>{_escape_html(item.belief_id)}</code></td>"
                f"<td>{item.stale_probability:.3f}</td>"
                f"<td>{_escape_html(', '.join(item.reasons) or 'none')}</td></tr>"
            )
            for item in report.assessments
        ) or "<tr><td colspan='3'>No assessments available.</td></tr>"

        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape_html(title)}</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --panel: #fffaf0;
      --ink: #1f1d1a;
      --muted: #6e6558;
      --accent: #b54d2e;
      --line: #d8ccbb;
      --good: #2d6a4f;
      --warn: #b7791f;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: linear-gradient(180deg, #efe6d6 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }}
    .hero {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 28px;
      box-shadow: 0 10px 30px rgba(60, 43, 20, 0.06);
    }}
    .hero h1 {{
      margin: 0 0 10px;
      font-size: 40px;
      line-height: 1.1;
    }}
    .hero p {{
      margin: 0;
      color: var(--muted);
      font-size: 18px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-top: 24px;
    }}
    .stat {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
    }}
    .stat .label {{
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .stat .value {{
      margin-top: 8px;
      font-size: 28px;
      font-weight: bold;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 18px;
      margin-top: 20px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 22px;
    }}
    h2 {{
      margin-top: 0;
      font-size: 24px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    ol {{
      margin: 0;
      padding-left: 22px;
    }}
    code {{
      background: rgba(181, 77, 46, 0.08);
      padding: 2px 6px;
      border-radius: 6px;
    }}
    .note {{
      margin-top: 18px;
      color: var(--muted);
      font-size: 14px;
    }}
    @media (max-width: 880px) {{
      .grid {{
        grid-template-columns: 1fr;
      }}
      .hero h1 {{
        font-size: 32px;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>{_escape_html(title)}</h1>
      <p>BeliefSync report for repository-state belief drift and targeted recovery.</p>
      <div class="stats">
        <div class="stat"><div class="label">Beliefs</div><div class="value">{len(report.beliefs)}</div></div>
        <div class="stat"><div class="label">Potentially Stale</div><div class="value">{len(stale)}</div></div>
        <div class="stat"><div class="label">Actions</div><div class="value">{len(report.actions)}</div></div>
      </div>
    </section>
    <section class="grid">
      <div class="card">
        <h2>Stale Belief Assessments</h2>
        <table>
          <thead>
            <tr><th>Belief</th><th>Stale Prob.</th><th>Reasons</th></tr>
          </thead>
          <tbody>{stale_items}</tbody>
        </table>
      </div>
      <div class="card">
        <h2>Recommended Actions</h2>
        <ol>{action_items}</ol>
        <p class="note">These actions are ranked by expected value minus estimated cost.</p>
      </div>
    </section>
  </div>
</body>
</html>"""


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
