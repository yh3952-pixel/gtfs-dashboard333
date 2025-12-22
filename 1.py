import pathlib
import re

root = pathlib.Path(".")

print("Scanning for deprecated st.plotly_chart usage...\n")

for p in root.rglob("*.py"):
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    for m in re.finditer(r"st\.plotly_chart\(.*?\)", t, re.S):
        block = m.group(0)
        if (
            ("displaylogo" in block or "scrollZoom" in block or "modebar" in block.lower())
            and "config=" not in block
        ):
            line = t[: m.start()].count("\n") + 1
            print(f"[FOUND] {p}  line {line}")
            print(block.replace("\n", " ")[:200])
            print()
