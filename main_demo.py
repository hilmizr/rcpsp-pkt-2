"""
main_demo.py
End-to-end demo RCPSP dengan struktur modular -– cocok dijalankan di Colab / lokal.
"""

from pathlib import Path

# --- modul internal ---
from data_generator import create_sample_excel
from data_parser import load_project_data
from solver import RCPSPSolver
import report_generator as rpt
import visualizer as viz


def main():
    print("🚀 STARTING RCPSP SOLVER DEMO")
    print("=" * 80)

    # ------------------------------------------------------------------
    # 1) Siapkan data contoh
    # ------------------------------------------------------------------
    print("Creating sample Excel file …")
    xlsx_bytes = create_sample_excel()
    sample_path = Path("sample_project.xlsx")
    sample_path.write_bytes(xlsx_bytes)
    print(f"✅ Sample file saved to: {sample_path}")

    # ------------------------------------------------------------------
    # 2) Parsing  ➜  tasks, resources, dependencies
    # ------------------------------------------------------------------
    tasks, resources, deps = load_project_data(sample_path)
    rpt.display_input_data(tasks, resources, deps)

    # ------------------------------------------------------------------
    # 3) Solve RCPSP
    # ------------------------------------------------------------------
    print("\n🔄 Solving RCPSP …")
    print("-" * 50)
    solver = RCPSPSolver(tasks, resources, deps)

    if solver.solve():                             # time-limit default 30 s
        sol = solver.solution                      # dict result
        print("✅ Solution found!")

        # ------------------------------------------------------------------
        # 4) Laporan teks
        # ------------------------------------------------------------------
        rpt.display_solution_data(tasks, resources, sol)
        rpt.display_resource_utilization(tasks, resources, sol)
        rpt.display_critical_path(deps, sol)

        # ------------------------------------------------------------------
        # 5) Visualisasi
        # ------------------------------------------------------------------
        print("\n📈 Creating visualizations …")
        print("-" * 50)
        fig = viz.create_gantt_chart_bar(sol)      # pilih varian favorit
        fig.show()

        # ------------------------------------------------------------------
        # 6) Ekspor jadwal ke Excel
        # ------------------------------------------------------------------
        print("\n💾 Exporting schedule …")
        print("-" * 50)
        schedule_xlsx = _export_schedule_to_excel(sol)   # helper lokal
        Path("project_schedule.xlsx").write_bytes(schedule_xlsx)
        print("✅ Schedule exported to: project_schedule.xlsx")

        print("\n🎉 PROCESS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
    else:
        print("❌ No feasible solution.")
        print("Possible issues:")
        print("- Resource constraints too tight")
        print("- Infeasible dependencies")
        print("- Solver time limit reached")


# ----------------------------------------------------------------------
# Helper ekspor – sengaja dipisah agar solver.py tetap bersih dari I/O
# ----------------------------------------------------------------------
import io
import pandas as pd


def _export_schedule_to_excel(solution: dict) -> bytes:
    rows = [
        {
            "Task ID": tid,
            "Task Name": sch["name"],
            "Start Time": sch["start"],
            "End Time": sch["end"],
            "Duration": sch["duration"],
        }
        for tid, sch in solution["task_schedule"].items()
    ]
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Schedule", index=False)
    return buffer.getvalue()


# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
