"""
report_generator.py
Fungsi-fungsi ringkasan teks & statistik proyek RCPSP.
Bersifat stateless – tidak tergantung pada instance RCPSPSolver.
"""
from __future__ import annotations
from typing import List, Dict, Tuple, Optional

import pandas as pd


# ----------------------------------------------------------------------
# 1. INPUT DATA OVERVIEW
# ----------------------------------------------------------------------
def display_input_data(
    tasks: List[Dict],
    resources: List[Dict],
    dependencies: List[Tuple[int, int]],
) -> None:
    """Print ringkasan data masukan proyek."""

    print("=" * 80)
    print("📊 INPUT DATA ANALYSIS")
    print("=" * 80)

    # ----- Tasks -------------------------------------------------------
    print("\n🔧 TASKS OVERVIEW")
    print("-" * 50)

    tasks_df = pd.DataFrame(tasks).rename(
        columns={"id": "task_id", "name": "task_name"}
    )

    # Tambah kolom permintaan resource per task
    for res in resources:
        col = f"Req_{res['name']}"
        tasks_df[col] = tasks_df["resource_req"].apply(
            lambda d: d.get(res["id"], 0)
        )

    display_cols = ["task_id", "task_name", "duration"] + [
        f"Req_{r['name']}" for r in resources
    ]
    print(tasks_df[display_cols].to_string(index=False))

    # ----- Resources ---------------------------------------------------
    print("\n⚙️ RESOURCES OVERVIEW")
    print("-" * 50)
    resources_df = pd.DataFrame(resources).rename(
        columns={"id": "resource_id", "name": "resource_name"}
    )
    print(resources_df.to_string(index=False))

    # ----- Dependencies ------------------------------------------------
    print("\n🔗 DEPENDENCIES OVERVIEW")
    print("-" * 50)
    if dependencies:
        dep_df = pd.DataFrame(dependencies, columns=["predecessor_id", "successor_id"])
        id_to_name = {t["id"]: t["name"] for t in tasks}
        dep_df["Predecessor_Name"] = dep_df["predecessor_id"].map(id_to_name)
        dep_df["Successor_Name"] = dep_df["successor_id"].map(id_to_name)
        print(dep_df.to_string(index=False))
    else:
        print("No dependencies defined")

    # ----- Statistics --------------------------------------------------
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


# ----------------------------------------------------------------------
# 2. SOLUTION OVERVIEW
# ----------------------------------------------------------------------
def display_solution_data(
    tasks: List[Dict],
    resources: List[Dict],
    solution: Optional[Dict],
) -> None:
    """Print ringkasan hasil optimasi & jadwal rinci."""

    if not solution or solution.get("status") != "SUCCESS":
        print("❌ No solution available to display")
        return

    print("\n" + "=" * 80)
    print("🎯 SOLUTION ANALYSIS")
    print("=" * 80)

    # ----- Summary -----------------------------------------------------
    print("\n✅ OPTIMIZATION RESULTS")
    print("-" * 50)
    makespan = solution["makespan"]
    sequential_time = sum(t["duration"] for t in tasks)
    efficiency = ((sequential_time - makespan) / sequential_time * 100) if sequential_time else 0

    summary_df = pd.DataFrame(
        {
            "Metric": ["Optimal Makespan", "Sequential Time", "Time Saved", "Efficiency Gain"],
            "Value": [
                f"{makespan} units",
                f"{sequential_time} units",
                f"{sequential_time - makespan} units",
                f"{efficiency:.1f}%",
            ],
        }
    )
    print(summary_df.to_string(index=False))

    # ----- Detailed Schedule ------------------------------------------
    print("\n📅 DETAILED SCHEDULE")
    print("-" * 50)
    schedule_rows = []
    id_to_res = {r["id"]: r["name"] for r in resources}

    for task_id, sch in sorted(solution["task_schedule"].items()):
        task = next(t for t in tasks if t["id"] == task_id)
        usage = [f"{id_to_res[rid]}: {qty}" for rid,
                 qty in task["resource_req"].items()]
        schedule_rows.append(
            {
                "Task_ID": task_id,
                "Task_Name": sch["name"],
                "Start": sch["start"],
                "End": sch["end"],
                "Duration": sch["duration"],
                "Resource_Usage": " | ".join(usage) if usage else "None",
            }
        )

    print(pd.DataFrame(schedule_rows).to_string(index=False))


# ----------------------------------------------------------------------
# 3. RESOURCE UTILISATION
# ----------------------------------------------------------------------
def display_resource_utilization(
    tasks: List[Dict],
    resources: List[Dict],
    solution: Optional[Dict],
) -> None:
    """Cetak ringkasan utilisasi puncak & rata-rata tiap resource."""

    if not solution or solution.get("status") != "SUCCESS":
        return

    max_time = solution["makespan"]
    util = {r["name"]: [0] * (max_time + 1) for r in resources}
    id_to_name = {r["id"]: r["name"] for r in resources}

    # Hitung pemakaian per time unit
    for task_id, sch in solution["task_schedule"].items():
        task = next(t for t in tasks if t["id"] == task_id)
        for t_unit in range(sch["start"], sch["end"]):
            for rid, qty in task["resource_req"].items():
                util[id_to_name[rid]][t_unit] += qty

    # Ringkasan
    rows = []
    for r in resources:
        name, cap = r["name"], r["capacity"]
        usage = util[name]
        max_use, avg_use = max(usage), sum(usage) / len(usage)
        rows.append(
            {
                "Resource": name,
                "Capacity": cap,
                "Peak_Usage": max_use,
                "Avg_Usage": f"{avg_use:.1f}",
                "Peak_Utilization": f"{max_use / cap * 100:.1f}%" if cap else "N/A",
                "Avg_Utilization": f"{avg_use / cap * 100:.1f}%" if cap else "N/A",
            }
        )

    print("\n📊 RESOURCE UTILIZATION ANALYSIS")
    print("-" * 50)
    print(pd.DataFrame(rows).to_string(index=False))


# ----------------------------------------------------------------------
# 4. CRITICAL PATH
# ----------------------------------------------------------------------
def display_critical_path(
    dependencies: List[Tuple[int, int]],
    solution: Optional[Dict],
) -> None:
    """Telusuri & tampilkan jalur kritis."""

    if not solution or solution.get("status") != "SUCCESS":
        return

    print("\n🎯 CRITICAL PATH ANALYSIS")
    print("-" * 50)

    makespan = solution["makespan"]
    critical_tasks = [tid for tid, sch in solution["task_schedule"].items() if sch["end"] == makespan]

    critical_path: List[Tuple[int, int]] = []
    current = critical_tasks.copy()

    while current:
        preds = []
        for pred, succ in dependencies:
            if succ in current:
                sch_pred = solution["task_schedule"][pred]
                sch_succ = solution["task_schedule"][succ]
                if sch_pred["end"] == sch_succ["start"]:
                    preds.append(pred)
                    critical_path.append((pred, succ))
        current = preds

    if critical_path:
        print("Critical Dependencies:")
        for pred, succ in critical_path:
            pred_name = solution["task_schedule"][pred]["name"]
            succ_name = solution["task_schedule"][succ]["name"]
            print(f"  Task {pred} ({pred_name}) → Task {succ} ({succ_name})")
    else:
        print("No clear critical path found (parallel execution)")

# ==========================================
# 5. HELPER – DataFrame / List for exporter
# ==========================================
def report_to_df(tasks: List[Dict], solution: Dict) -> pd.DataFrame:
    """DataFrame ringkas hasil optimasi (makespan dsb.)."""
    makespan = solution["makespan"]
    sequential = sum(t["duration"] for t in tasks)
    time_saved = sequential - makespan
    efficiency = (time_saved / sequential * 100) if sequential else 0
    return pd.DataFrame(
        {
            "Metric": ["Optimal Makespan", "Sequential Time", "Time Saved", "Efficiency Gain"],
            "Value": [
                f"{makespan} units",
                f"{sequential} units",
                f"{time_saved} units",
                f"{efficiency:.1f}%",
            ],
        }
    )

def resource_util_df(tasks: List[Dict], resources: List[Dict], solution: Dict) -> pd.DataFrame:
    """DataFrame utilisasi puncak & rata-rata tiap resource."""
    max_time = solution["makespan"]
    util = {r["name"]: [0]*(max_time+1) for r in resources}
    id2name = {r["id"]: r["name"] for r in resources}

    # hitung pemakaian per slot waktu
    for tid, sch in solution["task_schedule"].items():
        task = next(t for t in tasks if t["id"] == tid)
        for t_unit in range(sch["start"], sch["end"]):
            for rid, qty in task["resource_req"].items():
                util[id2name[rid]][t_unit] += qty

    rows = []
    for r in resources:
        name, cap = r["name"], r["capacity"]
        usage = util[name]
        peak, avg = max(usage), sum(usage)/len(usage)
        rows.append(
            {
                "Resource": name,
                "Capacity": cap,
                "Peak_Usage": peak,
                "Avg_Usage": f"{avg:.1f}",
                "Peak_Utilization": f"{peak/cap*100:.1f}%" if cap else "N/A",
                "Avg_Utilization": f"{avg/cap*100:.1f}%" if cap else "N/A",
            }
        )
    return pd.DataFrame(rows)

def critical_path_list(dependencies: List[Tuple[int, int]], solution: Dict) -> list[str]:
    """Daftar string hubungan pada critical path, urut dari awal→akhir."""
    makespan = solution["makespan"]
    current = [tid for tid, sch in solution["task_schedule"].items() if sch["end"] == makespan]
    cp: list[Tuple[int, int]] = []

    while current:
        preds = []
        for pred, succ in dependencies:
            if succ in current:
                sch_p, sch_s = solution["task_schedule"][pred], solution["task_schedule"][succ]
                if sch_p["end"] == sch_s["start"]:
                    preds.append(pred)
                    cp.append((pred, succ))
        current = preds

    # ubah jadi list string (start→finish)
    result = []
    for pred, succ in reversed(cp):
        nm_p = solution["task_schedule"][pred]["name"]
        nm_s = solution["task_schedule"][succ]["name"]
        result.append(f"Task {pred} ({nm_p}) → Task {succ} ({nm_s})")
    return result
