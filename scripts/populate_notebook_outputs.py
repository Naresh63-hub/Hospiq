"""Execute Jupyter notebooks and persist rich outputs (stdout, tables, matplotlib plots).

Ensures all 3 project notebooks display rendered dataframes and visualizations directly on GitHub.
"""

import os
import sys
import json
import io
import base64
import contextlib
import traceback
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def execute_notebook(nb_path: str, output_path: str = None):
    print(f"\n{'='*70}\nExecuting: {nb_path}\n{'='*70}")
    if output_path is None:
        output_path = nb_path
        
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    project_root = os.path.abspath(".")
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    execution_namespace = {
        "__name__": "__main__",
        "__file__": os.path.abspath(nb_path),
        "sys": sys,
        "os": os
    }
    
    exec_count = 1
    
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
            
        source_code = "".join(cell.get("source", []))
        if not source_code.strip():
            cell["execution_count"] = None
            cell["outputs"] = []
            continue
            
        print(f"  Running Cell {idx + 1} (exec_count={exec_count})...")
        cell["execution_count"] = exec_count
        cell["outputs"] = []
        
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        
        plt.close("all")
        
        try:
            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                # Try evaluating as an expression first (for trailing expressions like df.head())
                lines = [l for l in source_code.splitlines() if l.strip() and not l.strip().startswith("#")]
                last_line = lines[-1] if lines else None
                
                # Check if multi-line or compound statement
                can_eval_last = False
                if last_line and not (last_line.startswith("import ") or last_line.startswith("from ") or 
                                       last_line.startswith("def ") or last_line.startswith("class ") or
                                       last_line.startswith("for ") or last_line.startswith("if ") or
                                       last_line.startswith("while ") or last_line.startswith("with ") or
                                       "=" in last_line or last_line.endswith(":")):
                    can_eval_last = True

                if can_eval_last and len(lines) > 1:
                    pre_code = "\n".join(source_code.splitlines()[:-1])
                    if pre_code.strip():
                        exec(pre_code, execution_namespace)
                    res = eval(last_line, execution_namespace)
                elif can_eval_last and len(lines) == 1:
                    res = eval(last_line, execution_namespace)
                else:
                    exec(source_code, execution_namespace)
                    res = None

            # Capture stdout
            stdout_text = stdout_buf.getvalue()
            if stdout_text:
                cell["outputs"].append({
                    "output_type": "stream",
                    "name": "stdout",
                    "text": stdout_text.splitlines(keepends=True)
                })

            # Capture figures
            fignums = plt.get_fignums()
            for fignum in fignums:
                fig = plt.figure(fignum)
                img_buf = io.BytesIO()
                fig.savefig(img_buf, format="png", bbox_inches="tight", dpi=120)
                img_buf.seek(0)
                b64_data = base64.b64encode(img_buf.read()).decode("utf-8")
                cell["outputs"].append({
                    "output_type": "display_data",
                    "data": {
                        "text/plain": ["<Figure size ...>"],
                        "image/png": b64_data
                    },
                    "metadata": {}
                })
            plt.close("all")

            # Capture evaluated expression result
            if res is not None:
                if isinstance(res, pd.DataFrame):
                    cell["outputs"].append({
                        "output_type": "execute_result",
                        "execution_count": exec_count,
                        "data": {
                            "text/html": [res.to_html(max_rows=10, max_cols=12)],
                            "text/plain": [res.to_string(max_rows=10, max_cols=12)]
                        },
                        "metadata": {}
                    })
                elif isinstance(res, pd.Series):
                    cell["outputs"].append({
                        "output_type": "execute_result",
                        "execution_count": exec_count,
                        "data": {
                            "text/plain": [res.to_string(max_rows=10)]
                        },
                        "metadata": {}
                    })
                elif not isinstance(res, (type(None))):
                    cell["outputs"].append({
                        "output_type": "execute_result",
                        "execution_count": exec_count,
                        "data": {
                            "text/plain": [repr(res)]
                        },
                        "metadata": {}
                    })

            # Check stderr
            stderr_text = stderr_buf.getvalue()
            if stderr_text and "UserWarning" not in stderr_text and "FutureWarning" not in stderr_text:
                print(f"    Notice: {stderr_text[:120].strip()}")

        except Exception as e:
            err_trace = traceback.format_exc()
            print(f"  [ERROR] in Cell {idx + 1}: {e}")
            cell["outputs"].append({
                "output_type": "error",
                "ename": type(e).__name__,
                "evalue": str(e),
                "traceback": err_trace.splitlines()
            })
            
        exec_count += 1
        
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
        
    print(f"Saved executed notebook to: {output_path}")


if __name__ == "__main__":
    notebooks = [
        "notebooks/01_data_generation_cleaning.ipynb",
        "notebooks/02_eda_feature_engineering.ipynb",
        "notebooks/03_rfm_kmeans_clustering.ipynb"
    ]
    for nb in notebooks:
        if os.path.exists(nb):
            execute_notebook(nb)
            # Copy to submission directory
            sub_nb = os.path.join("submission", os.path.basename(nb))
            execute_notebook(nb, sub_nb)
