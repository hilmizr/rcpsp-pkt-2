from pathlib import Path
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from report_generator import (
    report_to_df,      
    resource_util_df,
    critical_path_list
)

# ------ HTML REPORT (interaktif) -----------------------------------------
_env = Environment(loader=FileSystemLoader("templates"), autoescape=True)

def export_html_report(tasks, resources, deps, sol,
                       gantt_html_path: Path,
                       out: str | Path = "report.html") -> Path:
    tmpl = _env.get_template("report.html.j2")
    rendered = tmpl.render(
        tasks_df       = pd.DataFrame(tasks).to_html(index=False),
        resources_df   = pd.DataFrame(resources).to_html(index=False),
        deps_df        = pd.DataFrame(deps).to_html(index=False),
        solution_df    = report_to_df(sol).to_html(index=False),
        util_df        = resource_util_df(tasks, resources, sol).to_html(index=False),
        crit_list      = critical_path_list(deps, sol),
        gantt_html     = gantt_html_path.read_text(encoding="utf-8"),
    )
    out = Path(out)
    out.write_text(rendered, encoding="utf-8")
    return out

# ------ MARKDOWN REPORT ---------------------------------------------------
def export_md_report(tasks, resources, deps, sol,
                     gantt_png_path: Path,
                     out: str | Path = "report.md") -> Path:
    md = []
    md += ["# RCPSP Project Report", ""]
    md += ["## Tasks", pd.DataFrame(tasks).to_markdown(index=False), ""]
    md += ["## Resources", pd.DataFrame(resources).to_markdown(index=False), ""]
    md += ["## Dependencies", pd.DataFrame(deps).to_markdown(index=False), ""]
    md += ["## Solution Summary", report_to_df(sol).to_markdown(index=False), ""]
    md += ["## Resource Utilization",
           resource_util_df(tasks, resources, sol).to_markdown(index=False), ""]
    md += ["## Critical Path"]
    for c in critical_path_list(deps, sol):
        md.append(f"- {c}")
    md += ["", "## Gantt Chart",
           f"[Lihat Gantt interaktif]({gantt_png_path.with_suffix('.html').name})",
           "", f"![Gantt]({gantt_png_path.name})", ""]
    out = Path(out)
    out.write_text("\n".join(md), encoding="utf-8")
    return out
