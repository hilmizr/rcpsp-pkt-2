"""
data_generator.py
Berisi fungsi pembuat data dummy agar terpisah dari solver.
"""
import io
import pandas as pd

def create_sample_excel() -> bytes:
    """Create sample Excel file for testing"""

    # Sample data
    tasks_data = {
        'task_id': [1, 2, 3, 4, 5],
        'task_name': ['Design', 'Procurement', 'Installation', 'Testing', 'Commissioning'],
        'duration': [5, 3, 4, 2, 1],
        'resource_requirements': ['2,1,0', '1,0,2', '0,2,3', '1,1,1', '0,1,0']
    }

    resources_data = {
        'resource_id': [0, 1, 2],
        'resource_name': ['Engineers', 'Electricians', 'Technicians'],
        'capacity': [3, 4, 5]
    }

    dependencies_data = {
        'predecessor_id': [1, 2, 3, 4],
        'successor_id': [2, 3, 4, 5]
    }

    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(tasks_data).to_excel(writer, sheet_name='Tasks', index=False)
        pd.DataFrame(resources_data).to_excel(writer, sheet_name='Resources', index=False)
        pd.DataFrame(dependencies_data).to_excel(writer, sheet_name='Dependencies', index=False)

    return output.getvalue()