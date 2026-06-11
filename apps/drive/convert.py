"""Convert downloaded note files to Markdown.

Word-processor files go through pandoc (a system binary — see README): `.md`
passes through unchanged; `.docx`/`.odt` (and exported Google Docs, which we
hand off as `.docx`) are converted to GitHub-flavored Markdown.

Spreadsheets are handled in-process (no pandoc): `.xlsx` via openpyxl and `.csv`
via the stdlib, each rendered as one GFM table per sheet so the row/column/sheet
relationships survive for the AI context builder. Very large sheets are capped
with a visible truncation note to protect the AI token budget.
"""

import csv
import io
import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

# Per-sheet caps so one huge spreadsheet can't dominate the AI token budget.
MAX_ROWS = 500
MAX_COLS = 50


class ConversionError(Exception):
    """Raised when a file cannot be converted to Markdown."""


def to_markdown(content: bytes, ext: str) -> str:
    """Convert raw file bytes of the given extension to a Markdown string.

    Args:
        content: the raw bytes of the source file.
        ext: lowercase file extension including the dot (".docx", ".odt", ".md",
            ".xlsx", ".csv").

    Returns:
        The Markdown text.
    """
    if ext == ".md":
        return content.decode("utf-8", errors="replace")
    if ext == ".xlsx":
        return _xlsx_to_markdown(content)
    if ext == ".csv":
        return _csv_to_markdown(content)

    # pandoc infers the input format from the temp file's extension.
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        try:
            result = subprocess.run(
                ["pandoc", tmp_path, "-t", "gfm", "--wrap=none"],
                capture_output=True,
            )
        except FileNotFoundError as e:
            raise ConversionError(
                "pandoc is not installed — it is required to convert "
                ".docx/.odt notes (install with `apt-get install pandoc`)."
            ) from e
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            raise ConversionError(f"pandoc failed for {ext} file: {stderr}")
        return result.stdout.decode("utf-8", errors="replace")
    finally:
        os.remove(tmp_path)


# --------------------------------------------------------------------------- #
# Spreadsheets -> Markdown tables
# --------------------------------------------------------------------------- #
def _cell_text(value) -> str:
    """Render one cell as table-safe Markdown text."""
    if value is None:
        return ""
    text = str(value)
    # Pipes and newlines would break the GFM table layout.
    return (
        text.replace("|", "\\|")
        .replace("\r\n", " ")
        .replace("\n", " ")
        .replace("\r", " ")
        .strip()
    )


def _trim(rows):
    """Drop trailing empty rows and columns from a list-of-rows grid."""
    grid = [[_cell_text(c) for c in row] for row in rows]
    # Trailing empty rows.
    while grid and not any(grid[-1]):
        grid.pop()
    if not grid:
        return []
    # Trailing empty columns (ragged rows are padded to a common width).
    width = max(len(r) for r in grid)
    grid = [r + [""] * (width - len(r)) for r in grid]
    while width and not any(r[width - 1] for r in grid):
        width -= 1
        grid = [r[:width] for r in grid]
    return grid


def _render_table(rows, sheet_name=None) -> str:
    """Render a grid of cells as a GFM table (first row treated as header).

    Returns an empty string if the grid has no data. Applies MAX_ROWS/MAX_COLS
    caps and appends a visible truncation note when exceeded.
    """
    grid = _trim(rows)
    heading = f"## {sheet_name}\n\n" if sheet_name else ""
    if not grid:
        return ""

    total_rows, total_cols = len(grid), len(grid[0])
    extra_rows = max(0, total_rows - MAX_ROWS)
    extra_cols = max(0, total_cols - MAX_COLS)
    grid = [r[:MAX_COLS] for r in grid[:MAX_ROWS]]

    header, *body = grid
    width = len(header)
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    lines += ["| " + " | ".join(r) + " |" for r in body]

    if extra_rows or extra_cols:
        notes = []
        if extra_rows:
            notes.append(f"{extra_rows} more rows")
        if extra_cols:
            notes.append(f"{extra_cols} more columns")
        lines.append("")
        lines.append(f"_[truncated: {', '.join(notes)}]_")

    return heading + "\n".join(lines)


def _xlsx_to_markdown(content: bytes) -> str:
    """Convert an .xlsx workbook to one GFM table section per non-empty sheet."""
    try:
        import openpyxl
    except ImportError as e:  # pragma: no cover - dependency is declared
        raise ConversionError(
            "openpyxl is not installed — it is required to convert .xlsx notes "
            "(install with `pip install openpyxl`)."
        ) from e

    try:
        # data_only=True reads cached computed values so formulas render as
        # their results, not the formula text.
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
    except Exception as e:
        raise ConversionError(f"could not read .xlsx file: {e}") from e

    sections = []
    for ws in wb.worksheets:
        rows = [list(row) for row in ws.iter_rows(values_only=True)]
        table = _render_table(rows, sheet_name=ws.title)
        if table:
            sections.append(table)
    wb.close()
    return "\n\n".join(sections)


def _csv_to_markdown(content: bytes) -> str:
    """Convert a .csv file to a single GFM table."""
    text = content.decode("utf-8", errors="replace")
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error as e:
        raise ConversionError(f"could not read .csv file: {e}") from e
    return _render_table(rows)
