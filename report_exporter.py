from __future__ import annotations
"""report_exporter.py
======================
Render project‑wide RCPSP reports into **HTML** (interactive), **Markdown**, and
optionally PDF.  Relies on helper DataFrame creators from `report_generator.py`.

Usage (inside pipeline)
----------------------
html_path, png_path = viz.save_gantt_files(fig, "gantt")
html_rpt = export_html_report(tasks, resources, deps, sol, html_path)
md_rpt   = export_md_report(tasks, resources, deps, sol, png_path)
"""
from pathlib import Path
from typing import List, Dict, Tuple

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from report_generator import (
    report_to_df,
    resource_util_df,
    critical_path_list,
)

__all__ = [
    "export_html_report",
    "export_md_report",
]

# ---------------------------------------------------------------------------
# Jinja2 env (looks for templates/ in project root)
# ---------------------------------------------------------------------------
_ENV = Environment(loader=FileSystemLoader("templates"), autoescape=True)

# ---------------------------------------------------------------------------
# 1. HTML report with embedded interactive Plotly
# ---------------------------------------------------------------------------
def export_html_report(
    tasks: List[Dict],
    resources: List[Dict],
    deps: List[Tuple[int, int]],
    sol: Dict,
    gantt_html_path: Path,
    gantt_png_b64: str,
    out: str | Path = "report.html",
) -> Path:
    """Generate an interactive HTML report in *out* (default `report.html`).

    * `gantt_html_path` is the *full* HTML produced by `fig.write_html()` and
      will be in‑lined into the body of the report to keep everything
      self‑contained.
    """

    tmpl = _ENV.get_template("report.html.j2")
    rendered = tmpl.render(
        tasks_df=pd.DataFrame(tasks).to_html(index=False),
        resources_df=pd.DataFrame(resources).to_html(index=False),
        deps_df=pd.DataFrame(deps).to_html(index=False),
        solution_df=report_to_df(tasks, sol).to_html(index=False),  # <-- fixed
        util_df=resource_util_df(tasks, resources, sol).to_html(index=False),
        crit_list=critical_path_list(deps, sol),
        gantt_html=gantt_html_path.read_text(encoding="utf-8"),
        gantt_png  = gantt_png_b64,  
    )
    out = Path(out)
    out.write_text(rendered, encoding="utf-8")
    return out

# ---------------------------------------------------------------------------
# 2. Markdown report (lightweight, viewable in Git/Notion/VSCode)
# ---------------------------------------------------------------------------
def export_md_report(
    tasks: List[Dict],
    resources: List[Dict],
    deps: List[Tuple[int, int]],
    sol: Dict,
    gantt_png_path: Path | None,
    out: str | Path = "report.md",
) -> Path:
    """Render a Markdown snapshot.  If `gantt_png_path` is *None* (PNG export
    failed), the Gantt section will fall back to a textual link only.
    """
    md: list[str] = []
    md += ["# RCPSP Project Report", ""]
    # Tables
    md += ["## Tasks", pd.DataFrame(tasks).to_markdown(index=False), ""]
    md += ["## Resources", pd.DataFrame(resources).to_markdown(index=False), ""]
    md += ["## Dependencies", pd.DataFrame(deps).to_markdown(index=False), ""]
    md += ["## Solution Summary", report_to_df(tasks, sol).to_markdown(index=False), ""]
    md += [
        "## Resource Utilization",
        resource_util_df(tasks, resources, sol).to_markdown(index=False),
        "",
    ]
    # Critical path bullets
    md += ["## Critical Path"]
    md += [f"- {line}" for line in critical_path_list(deps, sol)]
    md += [""]
    # Gantt section
    md += ["## Gantt Chart"]
    if gantt_png_path and gantt_png_path.exists():
        md += [
            f"[Interactive version]({gantt_png_path.with_suffix('.html').name})",
            "",
            f"![Gantt chart]({gantt_png_path.name})",
            "",
        ]
    else:
        md += ["Interactive Gantt available in HTML report.", ""]

    out = Path(out)
    out.write_text("\n".join(md), encoding="utf-8")
    return out
