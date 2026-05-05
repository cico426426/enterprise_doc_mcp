import re


def clean(text: str) -> str:
    """
    Remove invisible chars and normalize whitespace/newlines.
    """
    if not text:
        return ""

    normalized = (
        text.replace("\u00a0", " ")
        .replace("\x0b", "\n")
        .replace("\u200b", "")
    )
    normalized = re.sub(r"[^\S\n]+", " ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def merge_lines(lines: list[str]) -> list[str]:
    """
    Merge accidental line breaks based on simple heuristics.
    """
    if not lines:
        return []

    merged: list[str] = [lines[0]]
    for line in lines[1:]:
        previous = merged[-1]
        prev_trim = previous.rstrip()
        next_trim = line.lstrip()

        if not prev_trim or not next_trim:
            merged.append(line)
            continue

        if prev_trim.endswith("-"):
            merged[-1] = prev_trim[:-1] + next_trim
            continue

        if re.match(r"^[a-z]", next_trim):
            merged[-1] = prev_trim + " " + next_trim
            continue

        if re.match(r"^\d", next_trim) and not prev_trim.endswith("."):
            merged[-1] = prev_trim + " " + next_trim
            continue

        merged.append(line)

    return merged


def normalize_block(text: str) -> str:
    """
    clean() -> splitlines -> merge_lines() -> join.
    """
    cleaned = clean(text)
    if not cleaned:
        return ""
    return "\n".join(merge_lines(cleaned.splitlines()))


def iter_meaningful(text: str, min_len: int = 3) -> list[str]:
    """
    Keep non-empty, non-whitespace lines with minimum length.
    """
    if not text:
        return []

    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and len(stripped) >= min_len:
            kept.append(stripped)
    return kept
