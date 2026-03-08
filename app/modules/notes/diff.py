import difflib

FIELDS = [
    "subjective",
    "objective",
    "assessment",
    "plan",
]


def build_diff(old, new):

    result = {}

    for field in FIELDS:

        old_text = old.get(field) or ""
        new_text = new.get(field) or ""

        diff = difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            lineterm="",
        )

        result[field] = "\n".join(diff)

    return result