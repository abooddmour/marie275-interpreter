"""Stage 1: parsing.

Reads the .mas source text line by line and splits every line into
    (line_no, label, mnemonic, operand)

Example:   "Loop,   Add One   / comment"   ->   (7, "Loop", "Add", "One")

Rules handled here:
  * everything after "/" is a comment and is thrown away
  * blank lines and comment-only lines are skipped, but they still count
    when numbering lines (so error messages show the real line number)
  * a label is a name followed by a comma at the start of the line
  * after the label there is one instruction word and at most one operand

The parser does not check whether the instruction exists or whether the
operand is valid; that is the loader's job (stage 2).
"""

import re

from marie.errors import MarieError

# A label starts with a letter and contains only letters, digits and "_".
LABEL_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def is_valid_label(name):
    """Return True if name is allowed as a label (e.g. Loop, X1, my_sum)."""
    return LABEL_PATTERN.match(name) is not None


def parse_line(line_no, text):
    """Parse one source line.

    Returns a tuple (line_no, label, mnemonic, operand), or None when the
    line is blank or only a comment. label and operand may be None.
    """
    # 1. Remove the comment: everything from the first "/" to the end.
    code = text.split("/", 1)[0].strip()
    if code == "":
        return None                     # blank or comment-only line

    # 2. Optional label: the part before the first comma.
    label = None
    if "," in code:
        label, code = code.split(",", 1)
        label = label.strip()
        code = code.strip()
        if not is_valid_label(label):
            raise MarieError(line_no, f"invalid label '{label}'")
        if code == "":
            raise MarieError(line_no, f"label '{label}' has no instruction")

    # 3. The rest is the instruction word and (maybe) one operand.
    words = code.split()
    mnemonic = words[0]
    operand = None
    if len(words) == 2:
        operand = words[1]
    elif len(words) > 2:
        raise MarieError(line_no, f"extra operand after '{mnemonic}'")

    return (line_no, label, mnemonic, operand)


def parse_program(source_text):
    """Parse a whole program and return the list of parsed lines.

    Line numbers start at 1. Blank and comment lines are left out of the
    list, but because we number the lines ourselves they are still counted.
    """
    parsed = []
    for line_no, text in enumerate(source_text.splitlines(), start=1):
        result = parse_line(line_no, text)
        if result is not None:
            parsed.append(result)
    return parsed
