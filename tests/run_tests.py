"""Run every test in tests/test_cases and print a PASS/FAIL table.

For each testN.mas:
  * the input values are read from its first line: "/ Input: 6 7" or "/ Input: none"
  * the interpreter is run as a separate program (like the grader does)
  * standard output must match the expected lines exactly
  * if testN_output.txt ends with "Error (line N): ...", the interpreter must
    also report an error on the same line N (the message wording may differ)

Usage:
    python tests/run_tests.py
"""

import re
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent / "test_cases"
INTERPRETER = Path(__file__).parent.parent / "interpreter.py"
ERROR_LINE = re.compile(r"^Error \(line (\d+)\):")


def read_inputs(mas_file):
    """Return the input values from the first line of the program."""
    first_line = mas_file.read_text(encoding="utf-8").splitlines()[0]
    values = first_line.split("Input:", 1)[1].split()
    return [] if values == ["none"] else values


def split_expected(lines):
    """Split the expected lines into (output lines, error line number or None)."""
    if lines and ERROR_LINE.match(lines[-1]):
        return lines[:-1], int(ERROR_LINE.match(lines[-1]).group(1))
    return lines, None


def run_test(mas_file):
    """Run one test. Returns (passed, details)."""
    expected_file = mas_file.with_name(mas_file.stem + "_output.txt")
    expected_lines = expected_file.read_text(encoding="utf-8").splitlines()
    expected_output, expected_error = split_expected(expected_lines)

    command = [sys.executable, str(INTERPRETER), str(mas_file)]
    inputs = read_inputs(mas_file)
    if inputs:
        command += ["--input"] + inputs
    result = subprocess.run(command, capture_output=True, text=True)

    actual_output = result.stdout.splitlines()
    error_lines = [line for line in result.stderr.splitlines() if ERROR_LINE.match(line)]
    actual_error = int(ERROR_LINE.match(error_lines[-1]).group(1)) if error_lines else None

    if actual_output != expected_output:
        return False, f"stdout {actual_output} != expected {expected_output}"
    if actual_error != expected_error:
        return False, f"error line {actual_error} != expected {expected_error}"
    if (expected_error is None) != (result.returncode == 0):
        return False, f"unexpected exit code {result.returncode}"
    return True, "error on line " + str(actual_error) if actual_error else "ok"


def test_number(path):
    """Sort test1, test2, ..., test10 by number, not alphabetically."""
    return int(re.search(r"\d+", path.stem).group())


def main():
    tests = sorted(TESTS_DIR.glob("test*.mas"), key=test_number)
    passed = 0
    print(f"{'Test':<8}{'Result':<8}Details")
    print("-" * 50)
    for mas_file in tests:
        ok, details = run_test(mas_file)
        passed += ok
        print(f"{mas_file.stem:<8}{'PASS' if ok else 'FAIL':<8}{details}")
    print("-" * 50)
    print(f"{passed}/{len(tests)} tests passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
