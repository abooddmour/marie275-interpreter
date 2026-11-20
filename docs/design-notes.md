# Design notes

## Stages

```
.mas text --parser--> parsed lines --loader--> memory + symbol table --executor--> output
```

1. **Parser** (`marie/parser.py`) - removes comments (`/` to end of line), skips
   blank lines, and turns each remaining line into a tuple
   `(line_no, label, mnemonic, operand)`. Line numbers are counted on the raw file,
   so blank and comment lines still count.
2. **Loader** (`marie/loader.py`) - two passes over the parsed lines. Line *i* of
   the list gets address *i*.
   - Pass 1 builds the symbol table and checks instruction names and operand counts.
   - Pass 2 resolves operands to addresses and writes every word into memory.
   Two passes are needed because a label can be used before the line that defines it.
3. **Machine** (`marie/machine.py`) - memory and the AC / PC registers.
4. **Executor** (`marie/executor.py`) - the fetch, advance PC, execute loop.
5. **IO handler** (`marie/io_handler.py`) - `Input` values, `Output`, `--trace`.

## Memory

- A Python list of 4096 entries, `machine.memory[0x000 .. 0xFFF]`.
- Each entry is either an `Instruction` or a Python `int` (a 16-bit signed number).
- Unused memory starts as the number `0`.
- `machine.source_lines` maps each loaded address to its source line. It is used
  for the "executing data" error: a data word reports its own line, unused memory
  reports the line of the last instruction that ran.

## Instructions

- Stored as a named tuple `Instruction(name, operand, text, line)`:
  - `name` - canonical name such as `"Add"` (names are case-insensitive in the source)
  - `operand` - the resolved address (or the Skipcond condition), `None` if there is no operand
  - `text` - the operand as written, for the trace
  - `line` - the source line, for error messages
- They are **not** converted to binary. A word is an instruction because it is an
  `Instruction` object. `Store` onto an instruction's address replaces it with a
  number, so running that address later is "executing data".
- Reading an instruction as a number (`Load`, `Add`, ... on an instruction) is an
  error on the line of the instruction doing the reading.

## Registers and numbers

- `machine.ac` and `machine.pc` are plain ints. PC starts at 0.
- Every result goes through `to_signed16()`, which keeps the low 16 bits and
  reads them back as two's complement (32767 + 1 -> -32768).
- `Div` rounds toward zero using the absolute values and the sign, not Python's
  `//` (which rounds down). `-32768 / -1` wraps to `-32768`.
- `Not` flips all 16 bits (`ac ^ 0xFFFF`); `And` / `Or` work on the 16-bit patterns.

## Symbol table

- A Python dict `label -> address`, built in pass 1. Labels are case-sensitive.
- When an operand is both a label and a valid hex number (for example `A`), the
  label wins. Otherwise a hex operand is an address and must be at most `FFF`.

## Decisions where the description leaves a choice

- **Skipcond** accepts only the hex values 000, 400 and 800; any other value is a loading error.
- **Step limit**: the 100,001st instruction is not run; the error is reported on its line.
- **Bad `--input` values** and unreadable files are reported as `Error (line 0): ...`.
- **Errors in the trace**: an instruction that fails is not printed in the trace.
- **Bonus pointers**: for `LoadI` / `StoreI` / `AddI` the word at X must be a number
  from 0 to 4095, otherwise "address out of range" on that instruction's line.
- **Exit codes**: 0 on Halt, 1 on any MARIE275 error, 2 on wrong command-line usage
  (argparse).
