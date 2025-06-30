"""
visualizer.py
Fungsi-fungsi visualisasi RCPSP - menerima dict `solution`
(dari RCPSPSolver.get_solution()) & mengembalikan objek Plotly Figure.
"""
from __future__ import annotations
from typing import Dict, Optional
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------
def _solution_ok(solution: Optional[Dict]) -> bool:
    """Cek solution tidak None dan berstatus SUCCESS."""
    return bool(solution) and solution.get("status") == "SUCCESS"


# ----------------------------------------------------------------------
def create_gantt_chart(solution: Dict) -> Optional[go.Figure]:
    """
    Gantt menggunakan px.timeline - waktu numerik → tanggal fiktif
    (agar Plotly mudah merender) lalu label sumbu dikembalikan ke 'time unit'.
    """
    if not _solution_ok(solution):
        return None

    base_date = pd.Timestamp("2024-01-01")        # t=0
    gantt_rows = [
        {
            "Task": f"Task {tid}: {sch['name']}",
            "Start": base_date + pd.Timedelta(days=sch["start"]),
            "Finish": base_date + pd.Timedelta(days=sch["end"]),
            "Resource": f"Duration: {sch['duration']}",
        }
        for tid, sch in solution["task_schedule"].items()
    ]

    fig = px.timeline(
        pd.DataFrame(gantt_rows),
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Resource",
        title=f"Project Schedule (Makespan: {solution['makespan']} time units)",
    )

    # Tweak sumbu X supaya tampil sebagai 'unit' (day no.)
    fig.update_layout(xaxis_title="Time Units", yaxis_title="Tasks", height=600)
    fig.update_xaxes(tickformat="%d", tickmode="linear",
                     tick0=base_date, dtick=86_400_000)  # 1 day in ms
    fig.update_yaxes(autorange="reversed")
    return fig


# ----------------------------------------------------------------------
def create_gantt_chart_bar(solution: Dict) -> Optional[go.Figure]:
    """
    Gantt bar horizontal—lebih “rigid” & tidak perlu konversi tanggal.
    """
    if not _solution_ok(solution):
        return None

    fig = go.Figure()
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c",
               "#d62728", "#9467bd", "#8c564b"]

    tasks_sorted = sorted(solution["task_schedule"].items(), key=lambda x: x[0])

    for idx, (tid, sch) in enumerate(tasks_sorted):
        task_label = f"Task {tid}: {sch['name']}"
        fig.add_trace(
            go.Bar(
                name=f"Dur: {sch['duration']}",
                orientation="h",
                y=[task_label],
                x=[sch["end"] - sch["start"]],
                base=[sch["start"]],
                marker_color=palette[idx % len(palette)],
                hovertemplate=(
                    f"<b>{task_label}</b><br>"
                    f"Start: {sch['start']}<br>"
                    f"End: {sch['end']}<br>"
                    f"Duration: {sch['duration']}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"Project Schedule (Makespan: {solution['makespan']} time units)",
        xaxis_title="Time Units",
        yaxis_title="Tasks",
        height=600,
        showlegend=True,
        yaxis={
            "categoryorder": "array",
            "categoryarray": [f"Task {tid}: {sch['name']}"
                              for tid, sch in reversed(tasks_sorted)],
        },
    )
    return fig


# ----------------------------------------------------------------------
def create_gantt_chart_fixed(solution: Dict) -> Optional[go.Figure]:
    """
    Versi “fixed” – numerik di-encode ke epoch+detik agar tick linear
    (mis. 1 unit = 1 jam).
    """
    if not _solution_ok(solution):
        return None

    epoch = pd.Timestamp("1970-01-01")
    rows = [
        {
            "Task": f"Task {tid}: {sch['name']}",
            "Start": epoch + pd.Timedelta(hours=sch["start"]),
            "Finish": epoch + pd.Timedelta(hours=sch["end"]),
            "Resource": f"Duration: {sch['duration']}",
            "StartUnit": sch["start"],
            "EndUnit": sch["end"],
        }
        for tid, sch in solution["task_schedule"].items()
    ]
    df = pd.DataFrame(rows)

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Resource",
        title=f"Project Schedule (Makespan: {solution['makespan']} time units)",
        hover_data=["StartUnit", "EndUnit"],
    )

    fig.update_layout(
        xaxis=dict(
            tickmode="linear",
            tick0=epoch,
            dtick=3_600_000,          # 1 h in ms
            tickformat="%H",
            title="Time Units",
        ),
        yaxis_title="Tasks",
        height=600,
    )
    fig.update_yaxes(autorange="reversed")
    return fig

# ----------------------------------------------------------------------
def save_gantt_files(fig: go.Figure, base_name: str = "gantt"):
    """
    Simpan figur Gantt sebagai:
    - <base_name>.html  (interaktif Plotly)
    - <base_name>.png   (statis, butuh kaleido)
    """
    html_path = Path(f"{base_name}.html")
    fig.write_html(html_path, include_plotlyjs="cdn", full_html=True)

    png_path = Path(f"{base_name}.png")
    fig.write_image(png_path, width=1200, height=600)  # pastikan kaleido ☑
    return html_path, png_path