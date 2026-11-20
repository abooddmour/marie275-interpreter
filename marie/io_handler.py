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

    def __init__(self, input_values):
        self.input_values = list(input_values)   # already checked ints
        self.next_index = 0                       # next value to hand out

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
