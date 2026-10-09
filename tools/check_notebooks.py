"""Check the lecture and lab notebooks.

1. Every internal link ``[..](#anchor)`` points to an existing ``<a class="anchor" id="anchor">``,
   no anchor id is used twice, and every link to another notebook ``[..](Лекція_NN_….ipynb)`` points to an existing file.
2. (unless --no-exec) every notebook executes top to bottom without errors,
   including errors swallowed by ipywidgets.interact and shown inside the widget.

Usage:
    python tools/check_notebooks.py            # links + execution
    python tools/check_notebooks.py --no-exec  # links only (fast)
    python tools/check_notebooks.py --inplace  # also save executed outputs into the notebooks
    python tools/check_notebooks.py Лекція_03  # only notebooks whose name contains the given text

Set CHECK_KERNEL=<kernel name> to execute with a kernel other than python3.
"""
import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = sorted(glob.glob(str(ROOT / "Лекція_*.ipynb"))) + sorted(glob.glob(str(ROOT / "Лб*.ipynb")))


def check_links(path):
    nb = json.load(open(path, encoding="utf-8"))
    text = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
    anchors = re.findall(r'<a class="anchor" id="([^"]+)"', text)
    links = set(re.findall(r"\]\(#([^)]+)\)", text))
    problems = [f"broken link #{l}" for l in sorted(links - set(anchors))]
    problems += [f"duplicate anchor #{a}" for a in sorted({a for a in anchors if anchors.count(a) > 1})]
    problems += [f"broken link {f}" for f in sorted(set(re.findall(r"\]\(([^)#:]+\.ipynb)\)", text)))
                 if not (ROOT / f).exists()]
    return problems


def execute(path, inplace):
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError, CellTimeoutError

    for attempt in range(3):   # nbclient occasionally loses the kernel reply after a widget cell — retry
        nb = nbformat.read(path, as_version=4)
        client = NotebookClient(nb, timeout=600, kernel_name=os.environ.get("CHECK_KERNEL", "python3"),
                                resources={"metadata": {"path": str(ROOT)}}, store_widget_state=True)
        try:
            client.execute()
            break
        except CellTimeoutError:
            continue
        except CellExecutionError as e:
            return [str(e).splitlines()[-1] if str(e) else "cell execution error"]
    else:
        return ["execution kept timing out"]

    # interact() catches exceptions and shows them inside the widget, so look there too
    problems = []
    state = nb.metadata.get("widgets", {}).get("application/vnd.jupyter.widget-state+json", {}).get("state", {})
    parent = {ch.replace("IPY_MODEL_", ""): mid for mid, m in state.items()
              for ch in m.get("state", {}).get("children", [])}
    for model_id, model in state.items():
        for out in model.get("state", {}).get("outputs", []):
            if out.get("output_type") == "error":
                root = model_id
                while root in parent:
                    root = parent[root]
                cell = next((i for i, c in enumerate(nb.cells) if c.cell_type == "code" and any(
                    root in str(o) for o in c.get("outputs", []))), "?")
                problems.append(f"error inside widget output (cell {cell}): {out['ename']}: {out['evalue']}")
    if inplace and not problems:
        nbformat.write(nb, path)
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-exec", action="store_true")
    ap.add_argument("--inplace", action="store_true")
    ap.add_argument("only", nargs="*", help="check only notebooks whose file name contains one of these strings")
    args = ap.parse_args()

    failed = False
    for path in NOTEBOOKS:
        name = Path(path).name
        if args.only and not any(s in name for s in args.only):
            continue
        problems = check_links(path)
        if not args.no_exec:
            problems += execute(path, args.inplace)
        for p in problems:
            print(f"FAIL {name}: {p}")
        if problems:
            failed = True
        else:
            print(f"OK   {name}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
