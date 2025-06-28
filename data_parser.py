"""
data_parser.py
Membaca file Excel proyek dan mengonversinya ke struktur list[dict]
yang dipakai RCPSPSolver. Terpisah dari solver → low coupling.
"""
from __future__ import annotations
from typing import List, Tuple, Dict

import pandas as pd


# ---------------------------------------------------------------------- #
def _parse_dataframes(
    tasks_df: pd.DataFrame,
    resources_df: pd.DataFrame,
    dependencies_df: pd.DataFrame,
) -> Tuple[List[Dict], List[Dict], List[Tuple[int, int]]]:
    """
    Ubah tiga DataFrame menjadi struktur internal.

    - tasks:  {id, name, duration, resource_req: Dict[resource_id, qty]}
    - resources: {id, name, capacity}
    - dependencies: List[(pred_id, succ_id)]
    """
    # Urutan resource_id sesuai sheet Resources untuk pemetaan qty
    res_ids: List[int] = resources_df["resource_id"].tolist()

    def _str_to_req_dict(req_str: str) -> Dict[int, int]:
        """'2,1,0' -> {resource_id: qty}"""
        qty_list = [int(x) for x in str(req_str).split(",")]
        return {
            res_id: qty_list[idx] if idx < len(qty_list) else 0
            for idx, res_id in enumerate(res_ids)
            if idx < len(qty_list) and qty_list[idx] > 0
        }

    # ---------- Tasks --------------------------------------------------
    tasks = [
        {
            "id": int(row.task_id),
            "name": row.task_name,
            "duration": int(row.duration),
            "resource_req": _str_to_req_dict(row.resource_requirements),
        }
        for _, row in tasks_df.iterrows()
    ]

    # ---------- Resources ---------------------------------------------
    resources = [
        {"id": int(r.resource_id), "name": r.resource_name, "capacity": int(r.capacity)}
        for _, r in resources_df.iterrows()
    ]

    # ---------- Dependencies ------------------------------------------
    dependencies = [
        (int(r.predecessor_id), int(r.successor_id))
        for _, r in dependencies_df.iterrows()
    ]

    return tasks, resources, dependencies


# ---------------------------------------------------------------------- #
def load_project_data(
    file_path: str,
) -> Tuple[List[Dict], List[Dict], List[Tuple[int, int]]]:
    """Wrapper publik: membaca tiga sheet & parsing."""
    tasks_df = pd.read_excel(file_path, sheet_name="Tasks")
    resources_df = pd.read_excel(file_path, sheet_name="Resources")
    dependencies_df = pd.read_excel(file_path, sheet_name="Dependencies")
    return _parse_dataframes(tasks_df, resources_df, dependencies_df)
