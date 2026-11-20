"""Stage 5: input and output.

    Input  - takes the next value from the list given after --input
    Output - prints AC in decimal on its own line on standard output

Standard output must contain ONLY the Output values, because the grader
compares it exactly.
"""

import sys

from marie.errors import MarieError


class IOHandler:
    """Holds the input values and writes the program's output."""

    def __init__(self, input_values, trace=False):
        self.input_values = list(input_values)   # already checked ints
        self.next_index = 0                       # next value to hand out
        self.trace_enabled = trace                # True when --trace is given

    def read_input(self, line):
        """Return the next input value; error if every value is used."""
        if self.next_index >= len(self.input_values):
            raise MarieError(line, "no input left")
        value = self.input_values[self.next_index]
        self.next_index += 1
        return value

    def write_output(self, value):
        """Print one value in decimal on its own line (standard output)."""
        print(value)

    def write_trace(self, address, instr, ac):
        """With --trace, print one step on standard error, for example:
               004  Add D         AC=9
        (address in 3-digit hex, the instruction as written, then AC).
        It goes to standard error so standard output stays unchanged.
        """
        if not self.trace_enabled:
            return
        text = instr.name if instr.text is None else f"{instr.name} {instr.text}"
        print(f"{address:03X}  {text:<14}AC={ac}", file=sys.stderr)
