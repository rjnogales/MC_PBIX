from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET
import re


def build_junit_html(junit_xml: Path, output_html: Path) -> None:
  """Convierte junit.xml en un HTML legible para revision no tecnica."""
    tree = ET.parse(junit_xml)
    root = tree.getroot()

    tests = int(root.attrib.get("tests", "0"))
    failures = int(root.attrib.get("failures", "0"))
    errors = int(root.attrib.get("errors", "0"))
    skipped = int(root.attrib.get("skipped", "0"))
    total_time = root.attrib.get("time", "0")

    rows = []
    for testcase in root.iter("testcase"):
        classname = testcase.attrib.get("classname", "")
        name = testcase.attrib.get("name", "")
        time = testcase.attrib.get("time", "")

        status = "passed"
        details = ""

        failure = testcase.find("failure")
        error = testcase.find("error")
        skip = testcase.find("skipped")

        if failure is not None:
            status = "failed"
            msg = failure.attrib.get("message", "")
            txt = (failure.text or "").strip()
            details = f"{msg}\n{txt}".strip()
        elif error is not None:
            status = "error"
            msg = error.attrib.get("message", "")
            txt = (error.text or "").strip()
            details = f"{msg}\n{txt}".strip()
        elif skip is not None:
            status = "skipped"
            msg = skip.attrib.get("message", "")
            txt = (skip.text or "").strip()
            details = f"{msg}\n{txt}".strip()

        rows.append(
            {
                "classname": classname,
                "name": name,
                "time": time,
                "status": status,
                "details": details,
            }
        )

    passed = tests - failures - errors - skipped

    def css_status(status: str) -> str:
        if status == "passed":
            return "ok"
        if status == "failed":
            return "fail"
        if status == "error":
            return "err"
        return "skip"

    rows_html = []
    for row in rows:
        details = escape(row["details"]) if row["details"] else ""
        rows_html.append(
            "<tr>"
            f"<td>{escape(row['classname'])}</td>"
            f"<td>{escape(row['name'])}</td>"
            f"<td class='num'>{escape(row['time'])}</td>"
            f"<td><span class='badge {css_status(row['status'])}'>{escape(row['status'])}</span></td>"
            f"<td><pre>{details}</pre></td>"
            "</tr>"
        )

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>JUnit Report</title>
  <style>
    :root {{
      --bg: #f7f8fa;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --line: #e5e7eb;
      --ok: #1f7a3f;
      --ok-bg: #e8f7ee;
      --fail: #b42318;
      --fail-bg: #fdecea;
      --err: #8e2a12;
      --err-bg: #fde8e5;
      --skip: #8a6d1d;
      --skip-bg: #fff8e1;
    }}
    body {{
      margin: 0;
      font-family: Segoe UI, Tahoma, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    .wrap {{
      max-width: 1200px;
      margin: 24px auto;
      padding: 0 16px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 16px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
    }}
    .meta {{
      color: var(--muted);
      font-size: 13px;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(6, minmax(120px, 1fr));
      gap: 10px;
      margin-top: 14px;
    }}
    .kpi {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      text-align: center;
      background: #fff;
    }}
    .kpi .v {{
      font-size: 22px;
      font-weight: 700;
    }}
    .kpi .l {{
      color: var(--muted);
      font-size: 12px;
    }}
    .links a {{
      margin-right: 12px;
      color: #0f4c81;
      text-decoration: none;
      font-weight: 600;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      font-size: 13px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      padding: 8px;
      word-wrap: break-word;
    }}
    th {{
      background: #fafafa;
      font-weight: 700;
    }}
    .num {{
      text-align: right;
      white-space: nowrap;
    }}
    .badge {{
      display: inline-block;
      border-radius: 12px;
      padding: 2px 8px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .ok {{ color: var(--ok); background: var(--ok-bg); }}
    .fail {{ color: var(--fail); background: var(--fail-bg); }}
    .err {{ color: var(--err); background: var(--err-bg); }}
    .skip {{ color: var(--skip); background: var(--skip-bg); }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      font-family: Consolas, 'Courier New', monospace;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"card\">
      <h1>JUnit Report</h1>
      <div class=\"meta\">Generated at {escape(datetime.now().isoformat(timespec='seconds'))}</div>
      <div class=\"kpis\">
        <div class=\"kpi\"><div class=\"v\">{tests}</div><div class=\"l\">Tests</div></div>
        <div class=\"kpi\"><div class=\"v\">{passed}</div><div class=\"l\">Passed</div></div>
        <div class=\"kpi\"><div class=\"v\">{failures}</div><div class=\"l\">Failures</div></div>
        <div class=\"kpi\"><div class=\"v\">{errors}</div><div class=\"l\">Errors</div></div>
        <div class=\"kpi\"><div class=\"v\">{skipped}</div><div class=\"l\">Skipped</div></div>
        <div class=\"kpi\"><div class=\"v\">{escape(total_time)}</div><div class=\"l\">Time (s)</div></div>
      </div>
      <div class=\"links\" style=\"margin-top: 14px;\">
        <a href=\"junit.xml\">Open junit.xml</a>
        <a href=\"pytest-summary.txt\">Open pytest-summary.txt</a>
      </div>
    </div>

    <div class=\"card\">
      <table>
        <thead>
          <tr>
            <th style=\"width: 28%;\">Class</th>
            <th style=\"width: 24%;\">Test</th>
            <th style=\"width: 8%;\">Time</th>
            <th style=\"width: 10%;\">Status</th>
            <th style=\"width: 30%;\">Details</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""

    output_html.write_text(html, encoding="utf-8")


def patch_coverage_index(index_file: Path) -> None:
  """Inserta/actualiza enlaces de evidencia dentro del index de htmlcov."""
    if not index_file.exists():
        return

    content = index_file.read_text(encoding="utf-8")

    block = (
        "<!-- TEST_EVIDENCE_START -->\n"
        "        <p class=\"text\">\n"
        "            Test evidence:\n"
        "            <a class=\"nav\" href=\"../tests/reports/junit-report.html\" target=\"_blank\" rel=\"noopener\">junit-report.html</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/junit.xml\" target=\"_blank\" rel=\"noopener\">junit.xml</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/pytest-summary.txt\" target=\"_blank\" rel=\"noopener\">pytest-summary.txt</a>\n"
        "        </p>\n"
        "<!-- TEST_EVIDENCE_END -->"
    )

    marker_pattern = re.compile(
        r"<!-- TEST_EVIDENCE_START -->.*?<!-- TEST_EVIDENCE_END -->",
        flags=re.DOTALL,
    )

    if marker_pattern.search(content):
      # Si ya hay bloque de evidencia, se reemplaza idempotentemente.
        updated = marker_pattern.sub(block, content)
    else:
        # Retrocompatibilidad: reemplaza el bloque "Test evidence" previo si existe.
        legacy = re.compile(r"\n\s*<p class=\"text\">\s*Test evidence:.*?</p>", flags=re.DOTALL)
        if legacy.search(content):
            updated = legacy.sub("\n" + block, content)
        else:
            anchor = "</p>\n    </div>"
            if anchor in content:
              # Inserta el bloque despues del parrafo informativo principal.
                updated = content.replace(anchor, "</p>\n" + block + "\n    </div>", 1)
            else:
                updated = content + "\n" + block + "\n"

    index_file.write_text(updated, encoding="utf-8")


def main() -> int:
  """Postproceso de reportes: HTML de JUnit y enlaces en htmlcov."""
    reports_dir = Path(__file__).resolve().parent
    zcode_dir = reports_dir.parents[1]

    junit_xml = reports_dir / "junit.xml"
    junit_html = reports_dir / "junit-report.html"
    coverage_index = zcode_dir / "htmlcov" / "index.html"

    if not junit_xml.exists():
        print(f"No existe {junit_xml}. Ejecuta pytest con --junitxml primero.")
        return 1

    build_junit_html(junit_xml, junit_html)
    patch_coverage_index(coverage_index)

    print(f"HTML generado: {junit_html}")
    print(f"Index de cobertura actualizado: {coverage_index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
