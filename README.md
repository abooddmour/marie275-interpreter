# MARIE275 Interpreter (M275)

A Python interpreter for **MARIE275**: the MARIE machine from Chapter 4 of the
textbook plus five new instructions (`Mult`, `Div`, `And`, `Or`, `Not`), and the
bonus array instructions `LoadI`, `StoreI` and `AddI`.

It reads a `.mas` program, loads it into a 4096-word memory and runs it
instruction by instruction, with 16-bit two's-complement arithmetic.

## Requirements

- Python 3.8 or newer
- Standard library only, nothing to install

## How to run

```
python interpreter.py program.mas                  # run
python interpreter.py program.mas --input 6 7      # values for Input, in order
python interpreter.py program.mas --trace          # also print a trace
```

### Command-line options

| Option | Meaning |
|---|---|
| `program.mas` | the MARIE275 program to run (required) |
| `--input N ...` | values handed to `Input`, in order. Each must be a whole number from -32768 to 32767, otherwise an error is reported before the program runs |
| `--trace` | after every instruction (including `Halt`) print its address, the instruction and AC on standard error, e.g. `004  Add D         AC=9` |

### Output and errors

- Standard output contains **only** the values printed by `Output`, one per line, in decimal.
- An error prints one line on standard error, `Error (line N): message`, and the
  program exits with code 1. Output printed before the error stays printed.
- `N` is the source line number (blank lines and comments count). Problems that
  are not on a source line (a bad `--input` value, a missing file) use line 0.
- Exit codes: `0` finished with `Halt`, `1` MARIE275 error, `2` wrong command-line usage.

## How to run the tests

```
python tests/run_tests.py
```

This runs every `tests/test_cases/testN.mas`, taking the input values from the
first line of the program (`/ Input: 6 7` or `/ Input: none`). It compares
standard output with `testN_output.txt` exactly and, for programs that end with an
error, checks that the error is on the same line. It prints a PASS/FAIL table.

| Test | What it checks |
|---|---|
| 1-5 | provided, with given answers: input/add, loops, if-else, 16-bit arithmetic, division by zero |
| 6-10 | provided: countdown loop, logic + Hex data, sum 1..n, factorial overflow, missing Halt |
| 11 | error: no input left |
| 12 | error: undefined label (loading error, so nothing is printed) |
| 13 | edge cases: -32768 / -1, a label that is also a hex number (`A`), any-case instruction names, `Hex 8000` |
| 14 | edge case: a loop that runs zero times, a program that prints nothing |
| 15 | error: more than 100,000 steps (infinite loop) |
| 16 | bonus: sum of an array with `AddI` |
| 17 | bonus: copy an array with `LoadI` / `StoreI` |

## Project layout

```
interpreter.py          entry point
marie/errors.py         MarieError: "Error (line N): message"
marie/parser.py         stage 1: split each line into label / instruction / operand
marie/loader.py         stage 2: two passes, symbol table, loading errors
marie/machine.py        stage 3: memory (4096 words), AC, PC, 16-bit wrap
marie/executor.py       stage 4: fetch-decode-execute loop, one method per instruction
marie/io_handler.py     stage 5: input values, Output, trace
marie/cli.py            command line, error reporting, exit codes
tests/run_tests.py      test runner
tests/test_cases/       test1 .. test17 (.mas and _output.txt)
docs/design-notes.md    how memory, instructions and the symbol table are represented
```

## Use of AI tools

This project was developed with the help of an AI coding assistant, with the
instructor's permission. All code was reviewed, tested and is explained by the author.
