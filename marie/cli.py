"""Command line interface.

    python interpreter.py program.mas                 # run
    python interpreter.py program.mas --input 6 7     # values for Input, in order
    python interpreter.py program.mas --trace         # also print a trace

Connects all the stages: read the file -> parse -> load -> execute.
Any MarieError is printed as ONE line on standard error and the program
ends with exit code 1. A Python traceback is never shown.

Exit codes: 0 = finished with Halt, 1 = MARIE error, 2 = bad command line.
"""

import argparse
import re
import sys

from marie.errors import MarieError
from marie.executor import Executor
from marie.io_handler import IOHandler
from marie.loader import load_program
from marie.machine import Machine
from marie.parser import parse_program

WHOLE_NUMBER = re.compile(r"^[+-]?[0-9]+$")


def build_arg_parser():
    """Describe the command line options."""
    parser = argparse.ArgumentParser(
        prog="interpreter.py",
        description="MARIE275 interpreter: runs a .mas program.")
    parser.add_argument("program", help="the .mas file to run")
    parser.add_argument("--input", nargs="*", default=[], metavar="N",
                        help="values for Input, in order (-32768 to 32767)")
    parser.add_argument("--trace", action="store_true",
                        help="print address, instruction and AC after each step (on stderr)")
    return parser


def check_input_values(texts):
    """Turn the --input strings into ints.

    Each value must be a whole number from -32768 to 32767. A bad value is
    reported before the program runs, as line 0 (it is not a source line).
    """
    values = []
    for text in texts:
        if not WHOLE_NUMBER.match(text):
            raise MarieError(0, f"input value '{text}' is not a whole number")
        value = int(text)
        if value < -32768 or value > 32767:
            raise MarieError(0, f"input value {value} is out of range (-32768 to 32767)")
        values.append(value)
    return values


def read_source(path):
    """Read the .mas file as text."""
    try:
        with open(path, encoding="utf-8-sig") as f:   # utf-8-sig drops a BOM
            return f.read()
    except (OSError, UnicodeDecodeError) as e:
        raise MarieError(0, f"cannot read file '{path}': {e}")


def run(program_path, input_texts, trace):
    """Run one program from start to finish (raises MarieError on error)."""
    inputs = check_input_values(input_texts)      # checked before running
    source = read_source(program_path)

    machine = Machine()
    load_program(parse_program(source), machine)  # stages 1 and 2

    io = IOHandler(inputs, trace)
    Executor(machine, io).run()                   # stage 4


def main(argv=None):
    """Entry point. Returns the exit code."""
    args = build_arg_parser().parse_args(argv)
    try:
        run(args.program, args.input, args.trace)
    except MarieError as error:
        sys.stdout.flush()                 # Output lines before the error stay printed
        print(error, file=sys.stderr)      # "Error (line N): message"
        return 1
    except Exception as error:             # safety net: never show a traceback
        sys.stdout.flush()
        print(MarieError(0, f"internal error: {error}"), file=sys.stderr)
        return 1
    return 0
