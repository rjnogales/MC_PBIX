from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET
import re


def parse_junit(junit_xml: Path) -> dict:
    """Parse JUnit XML into summary and detailed test rows.

    Args:
        junit_xml: Source JUnit XML report.

    Returns:
        dict: Parsed suite metrics and table rows.
    """
    tree = ET.parse(junit_xml)
    root = tree.getroot()

    def as_int(value: str | None) -> int:
      return int(value or "0")

    def as_float(value: str | None) -> float:
      return float(value or "0")

    tests = as_int(root.attrib.get("tests"))
    failures = as_int(root.attrib.get("failures"))
    errors = as_int(root.attrib.get("errors"))
    skipped = as_int(root.attrib.get("skipped"))
    total_time = as_float(root.attrib.get("time"))

    # Pytest JUnit often uses <testsuites> as root and stores metrics in child <testsuite> nodes.
    if root.tag == "testsuites" and tests == 0:
      suites = list(root.iter("testsuite"))
      tests = sum(as_int(s.attrib.get("tests")) for s in suites)
      failures = sum(as_int(s.attrib.get("failures")) for s in suites)
      errors = sum(as_int(s.attrib.get("errors")) for s in suites)
      skipped = sum(as_int(s.attrib.get("skipped")) for s in suites)
      total_time = sum(as_float(s.attrib.get("time")) for s in suites)

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
    pass_rate = (passed / tests * 100.0) if tests else 0.0

    return {
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "passed": passed,
        "pass_rate": pass_rate,
        "total_time": f"{total_time:.3f}",
        "rows": rows,
    }


def build_junit_html(
    junit_xml: Path,
    output_html: Path,
    report_title: str,
    xml_link_name: str,
    summary_link_name: str,
) -> None:
    """Convert a JUnit XML report into a human-readable HTML file.

    Args:
        junit_xml: Source JUnit XML report.
        output_html: Target HTML file to generate.
        report_title: Visible title shown in the HTML page.
        xml_link_name: Relative XML filename to expose as evidence link.
        summary_link_name: Relative TXT summary filename to expose as evidence link.
    """
    parsed = parse_junit(junit_xml)
    tests = parsed["tests"]
    failures = parsed["failures"]
    errors = parsed["errors"]
    skipped = parsed["skipped"]
    passed = parsed["passed"]
    total_time = parsed["total_time"]
    pass_rate = parsed["pass_rate"]
    rows = parsed["rows"]

    def css_status(status: str) -> str:
        """Map a test status to its CSS class name.

        Args:
            status: Raw test status.

        Returns:
            str: CSS class name for the badge.
        """
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
  <title>{escape(report_title)}</title>
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
    .suite-summary {{
      margin-top: 12px;
      padding: 10px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: #f9fafb;
      font-size: 13px;
    }}
    .links a {{
      margin-right: 12px;
      color: #0f4c81;
      text-decoration: none;
      font-weight: 600;
    }}
    .links a:hover {{
      text-decoration: underline;
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
      <h1>{escape(report_title)}</h1>
      <div class=\"meta\">Generated at {escape(datetime.now().isoformat(timespec='seconds'))}</div>
      <div class=\"kpis\">
        <div class=\"kpi\"><div class=\"v\">{tests}</div><div class=\"l\">Tests</div></div>
        <div class=\"kpi\"><div class=\"v\">{passed}</div><div class=\"l\">Passed</div></div>
        <div class=\"kpi\"><div class=\"v\">{failures}</div><div class=\"l\">Failures</div></div>
        <div class=\"kpi\"><div class=\"v\">{errors}</div><div class=\"l\">Errors</div></div>
        <div class=\"kpi\"><div class=\"v\">{skipped}</div><div class=\"l\">Skipped</div></div>
        <div class=\"kpi\"><div class=\"v\">{escape(total_time)}</div><div class=\"l\">Time (s)</div></div>
      </div>
      <div class=\"suite-summary\">Pass rate: <strong>{pass_rate:.2f}%</strong></div>
      <div class=\"links\" style=\"margin-top: 14px;\">
        <a href=\"{escape(xml_link_name)}\">Open {escape(xml_link_name)}</a>
        <a href=\"{escape(summary_link_name)}\">Open {escape(summary_link_name)}</a>
        <a href=\"reports-index.html\">Open reports-index.html</a>
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


def build_reports_index(reports_dir: Path, report_targets: list[dict]) -> Path:
    """Generate an index page linking all available suite reports.

    Args:
        reports_dir: Directory that stores report artifacts.
        report_targets: Suite configuration entries.

    Returns:
        Path: Generated HTML index path.
    """
    cards = []
    for target in report_targets:
        if not target["xml"].exists():
            continue

        parsed = parse_junit(target["xml"])
        cards.append(
            "<div class='card'>"
            f"<h2>{escape(target['title'])}</h2>"
            f"<p class='meta'>Tests: {parsed['tests']} | Passed: {parsed['passed']} | "
            f"Failures: {parsed['failures']} | Errors: {parsed['errors']} | "
            f"Skipped: {parsed['skipped']} | Pass rate: {parsed['pass_rate']:.2f}%</p>"
            "<p class='links'>"
            f"<a href='{escape(target['html'].name)}'>HTML</a>"
            f"<a href='{escape(target['xml'].name)}'>XML</a>"
            f"<a href='{escape(target['summary'])}'>Summary TXT</a>"
            "</p>"
            "</div>"
        )

    coverage_link = "../../htmlcov/cobertura-index.html"

    coverage_card = (
      "<div class='card'>"
      "<h2>Coverage Report</h2>"
      "<p class='meta'>Single entry for line-by-line coverage details.</p>"
      "<p class='links'>"
      f"<a href='{coverage_link}'>Open cobertura-index.html</a>"
      "</p>"
      "</div>"
    )

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Test Reports Index</title>
  <style>
    :root {{
      --bg: #f7f8fa;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --line: #e5e7eb;
      --link: #0f4c81;
    }}
    body {{
      margin: 0;
      font-family: Segoe UI, Tahoma, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    .wrap {{
      max-width: 1000px;
      margin: 24px auto;
      padding: 0 16px;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: 30px;
    }}
    .meta {{
      color: var(--muted);
      font-size: 13px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px;
      margin-top: 12px;
    }}
    h2 {{
      margin: 0 0 8px;
      font-size: 20px;
    }}
    .links a {{
      display: inline-block;
      margin-right: 12px;
      color: var(--link);
      text-decoration: none;
      font-weight: 600;
    }}
    .links a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>Test Reports Index</h1>
    <div class=\"meta\">Generated at {escape(datetime.now().isoformat(timespec='seconds'))}</div>
    {coverage_card}
    {''.join(cards) if cards else '<div class="card"><p>No report artifacts were found.</p></div>'}
  </div>
</body>
</html>
"""

    output_html = reports_dir / "reports-index.html"
    output_html.write_text(html, encoding="utf-8")
    return output_html


def patch_coverage_index(index_file: Path) -> None:
    """Insert or update evidence links inside the coverage index page.

    Args:
        index_file: htmlcov index file to patch.
    """
    if not index_file.exists():
        return

    content = index_file.read_text(encoding="utf-8")

    block = (
        "<!-- TEST_EVIDENCE_START -->\n"
        "        <p class=\"text\">\n"
        "            Test evidence:\n"
        "            <a class=\"nav\" href=\"../tests/reports/reports-index.html\" target=\"_blank\" rel=\"noopener\">reports-index.html</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/junit-report.html\" target=\"_blank\" rel=\"noopener\">junit-report.html</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/junit-funcional-report.html\" target=\"_blank\" rel=\"noopener\">junit-funcional-report.html</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/junit-regresion-referencia-report.html\" target=\"_blank\" rel=\"noopener\">junit-regresion-referencia-report.html</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/junit.xml\" target=\"_blank\" rel=\"noopener\">junit.xml</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/junit-funcional.xml\" target=\"_blank\" rel=\"noopener\">junit-funcional.xml</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/junit-regresion-referencia.xml\" target=\"_blank\" rel=\"noopener\">junit-regresion-referencia.xml</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/pytest-summary.txt\" target=\"_blank\" rel=\"noopener\">pytest-summary.txt</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/pytest-funcional-summary.txt\" target=\"_blank\" rel=\"noopener\">pytest-funcional-summary.txt</a>\n"
        "            |\n"
        "            <a class=\"nav\" href=\"../tests/reports/pytest-regresion-referencia-summary.txt\" target=\"_blank\" rel=\"noopener\">pytest-regresion-referencia-summary.txt</a>\n"
        "        </p>\n"
        "<!-- TEST_EVIDENCE_END -->"
    )

    marker_pattern = re.compile(
        r"<!-- TEST_EVIDENCE_START -->.*?<!-- TEST_EVIDENCE_END -->",
        flags=re.DOTALL,
    )

    if marker_pattern.search(content):
        updated = marker_pattern.sub(block, content)
    else:
        legacy = re.compile(r"\n\s*<p class=\"text\">\s*Test evidence:.*?</p>", flags=re.DOTALL)
        if legacy.search(content):
            updated = legacy.sub("\n" + block, content)
        else:
            anchor = "</p>\n    </div>"
            if anchor in content:
                updated = content.replace(anchor, "</p>\n" + block + "\n    </div>", 1)
            else:
                updated = content + "\n" + block + "\n"

    index_file.write_text(updated, encoding="utf-8")


def write_coverage_alias(index_file: Path) -> Path | None:
    """Create a coherent alias name for the coverage landing page.

    Args:
        index_file: Canonical coverage index generated by pytest-cov.

    Returns:
        Path | None: Alias path when generated, otherwise None.
    """
    if not index_file.exists():
        return None

    alias_file = index_file.with_name("cobertura-index.html")
    alias_file.write_text(index_file.read_text(encoding="utf-8"), encoding="utf-8")
    return alias_file


def main() -> int:
    """Run report post-processing for JUnit HTML and coverage links.

    Returns:
        int: Process exit code.
    """
    reports_dir = Path(__file__).resolve().parent
    zcode_dir = reports_dir.parents[1]
    coverage_index = zcode_dir / "htmlcov" / "index.html"

    report_targets = [
        {
            "xml": reports_dir / "junit.xml",
            "html": reports_dir / "junit-report.html",
            "title": "JUnit Report - Unit Suite",
            "summary": "pytest-summary.txt",
        },
        {
            "xml": reports_dir / "junit-funcional.xml",
            "html": reports_dir / "junit-funcional-report.html",
            "title": "JUnit Report - Functional Suite",
            "summary": "pytest-funcional-summary.txt",
        },
        {
            "xml": reports_dir / "junit-regresion-referencia.xml",
            "html": reports_dir / "junit-regresion-referencia-report.html",
            "title": "JUnit Report - Regression Reference Suite",
            "summary": "pytest-regresion-referencia-summary.txt",
        },
    ]

    generated = 0
    for target in report_targets:
        if not target["xml"].exists():
            continue
        build_junit_html(
            target["xml"],
            target["html"],
            target["title"],
            target["xml"].name,
            target["summary"],
        )
        print(f"HTML generado: {target['html']}")
        generated += 1

    if generated == 0:
        print("No existe ningun JUnit XML en tests/reports. Ejecuta pytest con --junitxml primero.")
        return 1

    reports_index = build_reports_index(reports_dir, report_targets)
    print(f"Indice generado: {reports_index}")

    patch_coverage_index(coverage_index)
    coverage_alias = write_coverage_alias(coverage_index)

    print(f"Index de cobertura actualizado: {coverage_index}")
    if coverage_alias is not None:
      print(f"Alias de cobertura generado: {coverage_alias}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
