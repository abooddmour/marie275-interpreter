"""Stage 2: loading.

Takes the parsed lines from parser.py and fills the machine's memory.
Each parsed line gets the next address, starting at 000.

Loading needs TWO passes because a program may use a label before the
line that defines it (for example "Jump Done" above "Done,"):

    Pass 1: give every line its address and build the symbol table
            (label -> address). Also check instruction names and
            how many operands each line has.
    Pass 2: now that every label is known, turn each operand into an
            address and place the instructions and data words in memory.

All loading errors from the project description are found here.
"""

import re

from marie.errors import MarieError
from marie.machine import Instruction, MAX_ADDRESS, to_signed16
from marie.parser import is_valid_label

# Every instruction: lower-case name -> (canonical name, takes an operand?)
# Instruction names are not case-sensitive, so we look them up in lower case.
INSTRUCTIONS = {
    "load":     ("Load", True),
    "store":    ("Store", True),
    "clear":    ("Clear", False),
    "add":      ("Add", True),
    "subt":     ("Subt", True),
    "mult":     ("Mult", True),
    "div":      ("Div", True),
    "and":      ("And", True),
    "or":       ("Or", True),
    "not":      ("Not", False),
    "input":    ("Input", False),
    "output":   ("Output", False),
    "jump":     ("Jump", True),
    "skipcond": ("Skipcond", True),
    "halt":     ("Halt", False),
    # Bonus: array instructions that use a pointer (X holds an address).
    "loadi":    ("LoadI", True),
    "storei":   ("StoreI", True),
    "addi":     ("AddI", True),
}

# Data directives: they put a number in memory instead of an instruction.
DATA_DIRECTIVES = {"dec": "Dec", "hex": "Hex"}

# The only conditions Skipcond accepts: 000 (AC < 0), 400 (AC = 0), 800 (AC > 0).
SKIPCOND_CONDITIONS = (0x000, 0x400, 0x800)

DEC_PATTERN = re.compile(r"^[+-]?[0-9]+$")    # e.g. 5, -7, +12
HEX_PATTERN = re.compile(r"^[0-9A-Fa-f]+$")   # e.g. 00FF, ffff, 8


def load_program(parsed_lines, machine):
    """Load the parsed program into machine.memory.

    Returns the symbol table (a dict: label -> address).
    Raises MarieError for any loading error.
    """
    symbols = first_pass(parsed_lines)
    second_pass(parsed_lines, symbols, machine)
    return symbols


# ---------------------------------------------------------------- pass 1

def first_pass(parsed_lines):
    """Give each line an address, build the symbol table, check names."""
    symbols = {}
    for address, (line_no, label, mnemonic, operand) in enumerate(parsed_lines):
        # The program must fit in memory (addresses 000..FFF).
        if address > MAX_ADDRESS:
            raise MarieError(line_no, "program does not fit in memory (address out of range)")

        # Record the label. Labels are case-sensitive, so "Sum" != "sum".
        if label is not None:
            if label in symbols:
                raise MarieError(line_no, f"duplicate label '{label}'")
            symbols[label] = address

        # Check the instruction name and the number of operands.
        key = mnemonic.lower()
        if key in DATA_DIRECTIVES:
            needs_operand = True
        elif key in INSTRUCTIONS:
            needs_operand = INSTRUCTIONS[key][1]
        else:
            raise MarieError(line_no, f"unknown instruction '{mnemonic}'")

        if needs_operand and operand is None:
            raise MarieError(line_no, f"missing operand for '{mnemonic}'")
        if not needs_operand and operand is not None:
            raise MarieError(line_no, f"extra operand '{operand}' for '{mnemonic}'")
    return symbols


# ---------------------------------------------------------------- pass 2

def second_pass(parsed_lines, symbols, machine):
    """Place every instruction and data word in memory."""
    for address, (line_no, label, mnemonic, operand) in enumerate(parsed_lines):
        key = mnemonic.lower()

        if key in DATA_DIRECTIVES:
            word = parse_data(line_no, key, operand)           # an int
        else:
            name = INSTRUCTIONS[key][0]
            if operand is None:
                value = None
            elif name == "Skipcond":
                value = parse_condition(line_no, operand)
            else:
                value = resolve_address(line_no, operand, symbols)
            word = Instruction(name, value, operand, line_no)

        machine.write(address, word)
        machine.source_lines[address] = line_no


def parse_data(line_no, directive, text):
    """Turn the operand of Dec / Hex into a 16-bit signed int."""
    if directive == "dec":
        if not DEC_PATTERN.match(text):
            raise MarieError(line_no, f"invalid decimal number '{text}'")
        value = int(text)
        if value < -32768 or value > 32767:
            raise MarieError(line_no, f"number out of range: {text} (Dec must be -32768 to 32767)")
        return value

    # Hex: 0000 .. FFFF. Values 8000..FFFF are negative (Hex FFFF is -1).
    if not HEX_PATTERN.match(text):
        raise MarieError(line_no, f"invalid hex number '{text}'")
    value = int(text, 16)
    if value > 0xFFFF:
        raise MarieError(line_no, f"number out of range: {text} (Hex must be 0000 to FFFF)")
    return to_signed16(value)


def parse_condition(line_no, text):
    """Skipcond takes only 000, 400 or 800 (written in hex)."""
    if HEX_PATTERN.match(text) and int(text, 16) in SKIPCOND_CONDITIONS:
        return int(text, 16)
    raise MarieError(line_no, f"invalid Skipcond condition '{text}' (use 000, 400 or 800)")


def resolve_address(line_no, text, symbols):
    """Turn an operand into an address.

    A label is tried first, then a hex address. So if a word is both a
    label and a valid hex number (for example "A"), it means the label.
    """
    if text in symbols:
        return symbols[text]
    if HEX_PATTERN.match(text):
        address = int(text, 16)
        if address > MAX_ADDRESS:
            raise MarieError(line_no, f"address out of range: {text} (memory ends at FFF)")
        return address
    if is_valid_label(text):
        raise MarieError(line_no, f"undefined label '{text}'")
    raise MarieError(line_no, f"invalid operand '{text}'")
