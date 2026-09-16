"""
Deterministic extractor for DOCX reports whose projects/programs are
listed in structured Word tables (the common case for association
annual reports, e.g. جمعية البر الخيرية بالمشعلية).

Why this exists:
The Qwen + LoRA model only ever returns a single extracted item per
document, even when a report lists 40-50+ projects across several
tables. Retraining the LoRA on multi-item examples is the real fix,
but for DOCX inputs that already contain clean tables we don't need
the LLM at all: python-docx gives us the rows directly, so we can
build the "programs" list with 100% recall and correct budgets/counts,
and fall back to the LLM path only when a table can't be parsed this
way (e.g. no recognizable column headers) or the input isn't a DOCX
with tables.
"""

import re
from docx import Document


NAME_KEYWORDS = ["اسم المشروع", "إسم المشروع", "المشروع"]
ENTITY_KEYWORDS = ["اسم الجهة", "إسم الجهة", "الجهة"]
BUDGET_KEYWORDS = ["مبلغ"]
COUNT_KEYWORDS = ["عدد المستفيدين", "المستفيدين"]
TYPE_KEYWORDS = ["نوع المستفيدين"]


def _clean(text):
    if text is None:
        return ""
    text = text.replace("\xa0", " ").replace("\t", " ").replace("\r", " ")
    text = " ".join(text.split())
    return text.strip()


def _row_cells(row):
    return [_clean(c.text) for c in row.cells]


def _find_col(header_cells, keywords, exclude=None):
    exclude = exclude or set()
    # Prefer an exact/substring match that isn't already claimed by
    # another column.
    for i, cell in enumerate(header_cells):
        if i in exclude:
            continue
        for kw in keywords:
            if kw in cell:
                return i
    return None


def _detect_header(table):
    """
    Returns (header_row_index, columns) where columns is a dict with
    keys: entity, name, budget, count, type -> column index (or None).
    Returns None if this table doesn't look like a project table at all.
    """
    max_scan = min(2, len(table.rows))
    for row_idx in range(max_scan):
        cells = _row_cells(table.rows[row_idx])
        if len(cells) < 3:
            continue

        budget_col = _find_col(cells, BUDGET_KEYWORDS)
        if budget_col is None:
            continue  # not a header row we recognize

        name_col = _find_col(cells, NAME_KEYWORDS, exclude={budget_col})
        entity_col = _find_col(cells, ENTITY_KEYWORDS, exclude={budget_col, name_col})
        count_col = _find_col(cells, COUNT_KEYWORDS, exclude={budget_col, name_col, entity_col})
        type_col = _find_col(cells, TYPE_KEYWORDS, exclude={budget_col, name_col, entity_col, count_col})

        n_cols = len(cells)

        if name_col is None:
            # Header row didn't literally say "المشروع" (seen when the
            # real header got merged into a title row above this
            # table, or duplicated across merged cells). Fall back
            # based on how many unclaimed columns sit before the
            # budget column: 1 -> just a name column; 2+ -> entity
            # then name.
            before_budget = [i for i in range(budget_col) if i not in {count_col, type_col}]
            if len(before_budget) == 1:
                name_col = before_budget[0]
            elif len(before_budget) >= 2:
                entity_col, name_col = before_budget[0], before_budget[1]
            else:
                continue

        if count_col is None:
            # duplicated "عدد المستفيدين" merged-cell artifacts mean the
            # count is usually right after budget.
            candidates = [i for i in range(n_cols) if i not in {budget_col, name_col, entity_col}]
            count_col = candidates[0] if candidates else None

        if type_col is None:
            # the audience/type value is conventionally the last column.
            type_col = n_cols - 1

        return row_idx, {
            "entity": entity_col,
            "name": name_col,
            "budget": budget_col,
            "count": count_col,
            "type": type_col,
        }

    return None


def _to_number(text):
    if not text:
        return None
    cleaned = text.replace(",", "").strip()
    if re.fullmatch(r"\d+(\.\d+)?", cleaned):
        value = float(cleaned)
        return int(value) if value.is_integer() else value
    return None


_PARTNER_SPLIT_RE = re.compile(r"\s*بالشراكة مع\s*")


def _split_embedded_partner(name):
    """
    Some report tables wrap the partner note into the SAME cell as the
    project name, on a second line, e.g.:
        "كفالة الأيتام\n بالشراكة مع شركة سابك"
    Once whitespace/newlines are collapsed this reads as one name
    ("كفالة الأيتام بالشراكة مع شركة سابك"). Split it back into the
    real project name and a partner note.
    Returns (clean_name, partner_note_or_None).
    """
    parts = _PARTNER_SPLIT_RE.split(name, maxsplit=1)
    if len(parts) == 2 and parts[0].strip():
        return parts[0].strip(), f"بالشراكة مع {parts[1].strip()}"
    return name, None


def _build_description(name, entity, embedded_partner_name, audience, count, budget_num):
    """
    Always returns a non-empty description sentence, generated from
    the project name plus whatever surrounding info is available
    (partner entity, target audience, beneficiaries count, budget).
    This is used when the table has no separate narrative/description
    column to pull from.
    """
    clauses = [f"مشروع {name}"]

    if audience:
        clauses.append(f"يستهدف فئة {audience}")

    partners = [p for p in (entity, embedded_partner_name) if p]
    if partners:
        clauses.append(f"بالشراكة مع {' و'.join(partners)}")

    if count is not None:
        clauses.append(f"استفاد منه {count} مستفيد")

    if budget_num is not None:
        clauses.append(f"بميزانية {budget_num} ريال سعودي حسب الوارد في التقرير")

    return "، ".join(clauses) + "."


def extract_projects_from_docx(file_path, year=None):
    """
    Returns a list of program/project dicts matching the pipeline's
    schema, or an empty list if no recognizable project tables were
    found (caller should then fall back to the LLM path).
    """
    doc = Document(file_path)
    programs = []

    for table in doc.tables:
        header = _detect_header(table)
        if header is None:
            continue

        header_row_idx, cols = header

        for row in table.rows[header_row_idx + 1:]:
            cells = _row_cells(row)
            if len(cells) <= max(v for v in cols.values() if v is not None):
                continue

            name = cells[cols["name"]] if cols["name"] is not None else ""
            budget_raw = cells[cols["budget"]] if cols["budget"] is not None else ""
            count_raw = cells[cols["count"]] if cols["count"] is not None else ""

            # Skip blank / title / separator rows.
            if not name or not (budget_raw or count_raw):
                continue
            if _to_number(budget_raw) is None and _to_number(count_raw) is None:
                continue

            entity = cells[cols["entity"]] if cols.get("entity") is not None else ""
            audience = cells[cols["type"]] if cols["type"] is not None else None

            name, embedded_partner = _split_embedded_partner(name)
            # embedded_partner looks like "بالشراكة مع X" already.
            embedded_partner_name = (
                embedded_partner.replace("بالشراكة مع", "", 1).strip()
                if embedded_partner else None
            )

            count_num = _to_number(count_raw)
            budget_num = _to_number(budget_raw)

            description = _build_description(
                name, entity, embedded_partner_name, audience, count_num, budget_num
            )

            programs.append({
                "type": "project",
                "name": name,
                "year": year,
                "description": description,
                "beneficiaries_count": count_num,
                "budget": budget_num if budget_num is not None else (budget_raw or None),
                "beneficiary_value": None,
                "target_audience": audience or None,
                "delivery_method": None,
                "notes": None,
            })

    return programs
