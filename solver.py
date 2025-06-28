# solver.py
# ---------------------------------------------------------------------
# RCPSPSolver: mem-build model CP-SAT, menyelesaikannya, dan
# menyimpan hasil (solution dict). Tidak ada logika baca/tampil/pdf, dsb.
# ---------------------------------------------------------------------
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from ortools.sat.python import cp_model

class RCPSPSolver:
    """
    Resource-Constrained Project Scheduling Problem (RCPSP) solver
    berbasis OR-Tools CP-SAT.

    Parameters
    ----------
    tasks : List[Dict]
        Dict = {id, name, duration, resource_req: List[int]}
    resources : List[Dict]
        Dict = {id, name, capacity}
    dependencies : List[Tuple[int, int]]
        List pasangan (predecessor_id, successor_id)
    """

    # ------------------------------------------------------------------
    def __init__(
        self,
        tasks: List[Dict],
        resources: List[Dict],
        dependencies: List[Tuple[int, int]],
    ) -> None:
        self.tasks = tasks
        self.resources = resources
        self.dependencies = dependencies
        self._solution: Optional[Dict] = None

    # ------------------------------------------------------------------
    def solve(self, time_limit: float = 30.0) -> bool:
        """Bangun model CP-SAT & cari solusi. Return True jika feasible."""
        model = cp_model.CpModel()

        # ------------- Variabel ----------------------------------------
        max_makespan = sum(t["duration"] for t in self.tasks)
        starts, ends, intervals = {}, {}, {}

        for t in self.tasks:
            starts[t["id"]] = model.NewIntVar(0, max_makespan, f"start_{t['id']}")
            ends[t["id"]] = model.NewIntVar(0, max_makespan, f"end_{t['id']}")
            intervals[t["id"]] = model.NewIntervalVar(
                starts[t["id"]], t["duration"], ends[t["id"]], f"int_{t['id']}"
            )

        # ------------- Precedence --------------------------------------
        for pred, succ in self.dependencies:
            model.Add(starts[succ] >= ends[pred])

        # ------------- Kapasitas Resource ------------------------------                
        for res in self.resources:          # res['id'], res['capacity']
            ints, demands = [], []
            for t in self.tasks:
                demand = t["resource_req"].get(res["id"], 0)
                if demand > 0:
                    ints.append(intervals[t["id"]])
                    demands.append(demand)
            if ints:
                model.AddCumulative(ints, demands, res["capacity"])

        # ------------- Objective: Minimize Makespan --------------------
        makespan = model.NewIntVar(0, max_makespan, "makespan")
        model.AddMaxEquality(makespan, [ends[t["id"]] for t in self.tasks])
        model.Minimize(makespan)

        # ------------- Solve -------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            self._solution = {
                "status": "SUCCESS",
                "makespan": solver.Value(makespan),
                "task_schedule": {
                    t["id"]: {
                        "name": t["name"],
                        "start": solver.Value(starts[t["id"]]),
                        "end": solver.Value(ends[t["id"]]),
                        "duration": t["duration"],
                    }
                    for t in self.tasks
                },
            }
            return True

        self._solution = {"status": "FAILED"}
        return False

    # ------------------------------------------------------------------
    #  Helper / Accessor
    # ------------------------------------------------------------------
    @property
    def solution(self) -> Optional[Dict]:
        """Dapatkan solusi terakhir (None bila belum/ gagal)."""
        return self._solution

    def makespan(self) -> Optional[int]:
        """Convenience untuk langsung ambil makespan."""
        if self._solution and self._solution.get("status") == "SUCCESS":
            return self._solution["makespan"]
        return None
