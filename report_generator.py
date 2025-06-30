from __future__ import annotations
"""report_generator.py
=======================
Stateless utilities for analysing and printing RCPSP input/solution data **and**
for providing tidy `pandas.DataFrame` objects consumed by higher‑level exporter
modules (HTML/Markdown/PDF).

Assumptions
-----------
* `tasks`        : list[dict] – each dict has keys `id`, `name`, `duration`,
  `resource_req`  (dict[int, int])
* `resources`    : list[dict] – keys `id`, `name`, `capacity`
* `dependencies` : list[tuple[int,int]] – (predecessor_id, successor_id)
* `solution`     : dict – produced by `RCPSPSolver`, at minimum:
    {
        "status"        : "SUCCESS" | "...",
        "makespan"      : int,
        "task_schedule" : { task_id : {
              "name"    : str,
              "start"   : int,
              "end"     : int,
              "duration": int }
        }
    }

This file **prints** human‑readable tables for quick inspection *and* offers
`report_to_df`, `resource_util_df`, and `critical_path_list` which return data
without printing – used by `report_exporter.py`.
"""
from typing import List, Dict, Tuple, Optional

import pandas as pd

__all__ = [
    "display_input_data",
    "display_solution_data",
    "display_resource_utilization",
    "display_critical_path",
    "report_to_df",
    "resource_util_df",
    "critical_path_list",
]

# ---------------------------------------------------------------------------
# 1) INPUT DATA OVERVIEW – console only
# ---------------------------------------------------------------------------

def display_input_data(
    tasks: List[Dict],
    resources: List[Dict],
    dependencies: List[Tuple[int, int]],
) -> None:
    """Pretty‑print raw spreadsheet content after parsing."""

    print("=" * 80)
    print("📊 INPUT DATA ANALYSIS")
    print("=" * 80)

    # ---- Tasks table -----------------------------------------------------
    print("\n🔧 TASKS OVERVIEW")
    print("-" * 50)

    tasks_df = pd.DataFrame(tasks).rename(
        columns={"id": "task_id", "name": "task_name"}
    )

    for res in resources:
        col = f"Req_{res['name']}"
        tasks_df[col] = tasks_df["resource_req"].apply(lambda d: d.get(res["id"], 0))

    disp_cols = ["task_id", "task_name", "duration"] + [f"Req_{r['name']}" for r in resources]
    print(tasks_df[disp_cols].to_string(index=False))

    # ---- Resources table --------------------------------------------------
    print("\n⚙️ RESOURCES OVERVIEW")
    print("-" * 50)
    res_df = pd.DataFrame(resources).rename(columns={"id": "resource_id", "name": "resource_name"})
    print(res_df.to_string(index=False))

    # ---- Dependencies table ----------------------------------------------
    print("\n🔗 DEPENDENCIES OVERVIEW")
    print("-" * 50)
    if dependencies:
        dep_df = pd.DataFrame(dependencies, columns=["predecessor_id", "successor_id"])
        id2name = {t["id"]: t["name"] for t in tasks}
        dep_df["Predecessor_Name"] = dep_df["predecessor_id"].map(id2name)
        dep_df["Successor_Name"] = dep_df["successor_id"].map(id2name)
        print(dep_df.to_string(index=False))
    else:
        print("No dependencies defined")

    # ---- Quick stats ------------------------------------------------------
    print("\n📈 PROJECT STATISTICS")
    print("-" * 50)
    stats_df = pd.DataFrame(
        {
            "Metric": [
                "Total Tasks",
                "Total Duration (if sequential)",
                "Total Resources",
                "Total Dependencies",
            ],
            "Value": [
                len(tasks),
                sum(t["duration"] for t in tasks),
                len(resources),
                len(dependencies),
            ],
        }
    )
    print(stats_df.to_string(index=False))


# ---------------------------------------------------------------------------
# 2) SOLUTION OVERVIEW – console only
# ---------------------------------------------------------------------------

def display_solution_data(
    tasks: List[Dict],
    resources: List[Dict],
    solution: Optional[Dict],
) -> None:
    """Pretty‑print solver results: makespan + per‑task schedule."""

    if not solution or solution.get("status") != "SUCCESS":
        print("❌ No solution available to display")
        return

    print("\n" + "=" * 80)
    print("🎯 SOLUTION ANALYSIS")
    print("=" * 80)

    # -- summary table ------------------------------------------------------
    print("\n✅ OPTIMIZATION RESULTS")
    print("-" * 50)
    summary_df = report_to_df(tasks, solution)
    print(summary_df.to_string(index=False))

    # -- detailed schedule --------------------------------------------------
    print("\n📅 DETAILED SCHEDULE")
    print("-" * 50)

    id2res = {r["id"]: r["name"] for r in resources}
    sched_rows = []
    for tid, sch in sorted(solution["task_schedule"].items()):
        task = next(t for t in tasks if t["id"] == tid)
        usage = " | ".join(f"{id2res[rid]}: {qty}" for rid, qty in task["resource_req"].items())
        sched_rows.append(
            {
                "Task_ID": tid,
                "Task_Name": sch["name"],
                "Start": sch["start"],
                "End": sch["end"],
                "Duration": sch["duration"],
                "Resource_Usage": usage or "None",
            }
        )
    print(pd.DataFrame(sched_rows).to_string(index=False))


# ---------------------------------------------------------------------------
# 3) RESOURCE UTILISATION – console only
# ---------------------------------------------------------------------------

def display_resource_utilization(
    tasks: List[Dict],
    resources: List[Dict],
    solution: Optional[Dict],
) -> None:
    """Print peak/avg utilisation for each resource across the schedule."""

    if not solution or solution.get("status") != "SUCCESS":
        return

    util_df = resource_util_df(tasks, resources, solution)

    print("\n📊 RESOURCE UTILIZATION ANALYSIS")
    print("-" * 50)
    print(util_df.to_string(index=False))


# ---------------------------------------------------------------------------
# 4) CRITICAL PATH – console only
# ---------------------------------------------------------------------------

def display_critical_path(
    dependencies: List[Tuple[int, int]],
    solution: Optional[Dict],
) -> None:
    """Trace & print critical path edges."""

    if not solution or solution.get("status") != "SUCCESS":
        return

    lines = critical_path_list(dependencies, solution)

    print("\n🎯 CRITICAL PATH ANALYSIS")
    print("-" * 50)
    if lines:
        print("Critical Dependencies:")
        for ln in lines:
            print("  " + ln)
    else:
        print("No clear critical path found (parallel execution)")


# ---------------------------------------------------------------------------
# 5) DATA HELPERS – returned to exporter modules (no printing)
# ---------------------------------------------------------------------------

def report_to_df(tasks: List[Dict], solution: Dict) -> pd.DataFrame:
    """Return optimisation KPIs as a tiny DataFrame."""
    makespan = solution["makespan"]
    sequential = sum(t["duration"] for t in tasks)
    saved = sequential - makespan
    eff = (saved / sequential * 100) if sequential else 0
    return pd.DataFrame(
        {
            "Metric": [
                "Optimal Makespan",
                "Sequential Time",
                "Time Saved",
                "Efficiency Gain",
            ],
            "Value": [
                f"{makespan} units",
                f"{sequential} units",
                f"{saved} units",
                f"{eff:.1f}%",
            ],
        }
    )


def resource_util_df(tasks: List[Dict], resources: List[Dict], solution: Dict) -> pd.DataFrame:
    """Return peak and average utilisation per resource."""
    horizon = solution["makespan"]
    util: Dict[str, List[int]] = {r["name"]: [0] * (horizon + 1) for r in resources}
    id2name = {r["id"]: r["name"] for r in resources}

    for tid, sch in solution["task_schedule"].items():
        task = next(t for t in tasks if t["id"] == tid)
        for t_unit in range(sch["start"], sch["end"]):
            for rid, qty in task["resource_req"].items():
                util[id2name[rid]][t_unit] += qty

    rows = []
    for r in resources:
        name, cap = r["name"], r["capacity"]
        usage = util[name]
        peak = max(usage)
        avg = sum(usage) / len(usage)
        rows.append(
            {
                "Resource": name,
                "Capacity": cap,
                "Peak_Usage": peak,
                "Avg_Usage": f"{avg:.1f}",
                "Peak_Utilization": f"{peak / cap * 100:.1f}%" if cap else "N/A",
                "Avg_Utilization": f"{avg / cap * 100:.1f}%" if cap else "N/A",
            }
        )
    return pd.DataFrame(rows)


def critical_path_list(dependencies: List[Tuple[int, int]], solution: Dict) -> List[str]:
    """Return critical path as list of strings (pred → succ)."""
    makespan = solution["makespan"]
    frontier = [tid for tid, sch in solution["task_schedule"].items() if sch["end"] == makespan]
    edges: List[Tuple[int, int]] = []

    while frontier:
        preds: List[int] = []
        for pred, succ in dependencies:
            if succ in frontier:
                sch_p = solution["task_schedule"][pred]
                sch_s = solution["task_schedule"][succ]
                if sch_p["end"] == sch_s["start"]:
                    preds.append(pred)
                    edges.append((pred, succ))
        frontier = preds

    lines: List[str] = []
    for pred, succ in reversed(edges):  # order from project start → end
        ln = solution["task_schedule"][pred]["name"]
        ls = solution["task_schedule"][succ]["name"]
        lines.append(f"Task {pred} ({ln}) → Task {succ} ({ls})")
    return lines
