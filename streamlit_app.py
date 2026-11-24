"""
streamlit_app.py — Root entrypoint for Streamlit Community Cloud deployment.
Forwards execution to src/dashboard/streamlit_app.py.
"""

from pathlib import Path
import sys

# Ensure repository root is on sys.path so src imports resolve cleanly
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

dashboard_script = root_dir / "src" / "dashboard" / "streamlit_app.py"

with open(dashboard_script, "r", encoding="utf-8") as fh:
    code = fh.read()

exec(compile(code, str(dashboard_script), "exec"))
