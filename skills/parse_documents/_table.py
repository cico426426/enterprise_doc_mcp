def _normalize_cell(cell: object) -> str:
    value = "" if cell is None else str(cell)
    value = value.replace("\n", " ")
    value = value.replace("|", r"\|")
    return value.strip()


def rows_to_markdown(rows: list[list[str]]) -> str:
    """
    Convert 2D rows into markdown table.
    """
    if not rows:
        return ""

    width = max((len(row) for row in rows), default=0)
    if width == 0:
        return ""

    def fmt_row(row: list[str]) -> str:
        cells = [_normalize_cell(row[i]) if i < len(row) else "" for i in range(width)]
        return "| " + " | ".join(cells) + " |"

    header = fmt_row(rows[0])
    divider = "| " + " | ".join(["---"] * width) + " |"
    body = [fmt_row(row) for row in rows[1:]]

    if not body:
        return "\n".join([header, divider])
    return "\n".join([header, divider, *body])
