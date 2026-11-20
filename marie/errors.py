"""The single error type used by the whole interpreter.

Every problem (while loading or while running) is raised as a MarieError.
cli.py catches it and prints exactly one line on standard error:

    Error (line N): message

N is the source line number (blank lines and comment lines are counted too).
Line 0 is used for problems that do not belong to any source line,
for example a bad --input value or a file that cannot be opened.
"""


class MarieError(Exception):
    """An error in a MARIE275 program, tied to one source line."""

    def __init__(self, line, message):
        super().__init__(message)
        self.line = line          # source line number (int)
        self.message = message    # short description, e.g. "division by zero"

    def __str__(self):
        # The exact format required by the project description.
        return f"Error (line {self.line}): {self.message}"
