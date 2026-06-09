"""HTML QC report writer (v0.2 stub)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_html_report(report: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in report.items())
    html = f"<!DOCTYPE html><html><body><h1>jpclaims QC Report</h1><table>{rows}</table></body></html>"
    p.write_text(html, encoding="utf-8")
