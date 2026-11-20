"""Stage 3: memory and registers.

Memory is one Python list of 4096 words (addresses 000 to FFF).
Each word is either
    * an Instruction (a small named tuple, see below), or
    * a Python int holding a 16-bit signed number (-32768 .. 32767).
Instructions are not turned into binary machine code. A word is an
instruction only because the loader put an Instruction object there.
Unused memory starts as the number 0.

The machine also has the two registers:
    AC - the accumulator, a 16-bit signed number
    PC - the program counter, the address of the next instruction
"""

from collections import namedtuple

MEMORY_SIZE = 4096          # addresses 0x000 .. 0xFFF
MAX_ADDRESS = MEMORY_SIZE - 1

# One instruction stored in one memory word.
#   name    - canonical instruction name, e.g. "Add"
#   operand - the operand as a number (an address or a Skipcond condition),
#             or None for Clear, Not, Input, Output and Halt
#   text    - the operand exactly as written in the source (used by --trace)
#   line    - the source line number (used in error messages)
Instruction = namedtuple("Instruction", ["name", "operand", "text", "line"])


def to_signed16(value):
    """Wrap any Python int into the 16-bit two's-complement range.

    Python ints never overflow, so after every calculation we keep only
    the low 16 bits and read them back as a signed number:
        32768  -> -32768      (32767 + 1 wraps around)
        60000  -> -5536       (300 * 200)
        0xFFFF -> -1
    """
    value = value & 0xFFFF          # keep only the low 16 bits
    if value >= 0x8000:             # top bit set means a negative number
        value = value - 0x10000
    return value


def is_instruction(word):
    """True if a memory word holds an instruction (not a number)."""
    return isinstance(word, Instruction)


class Machine:
    """The MARIE275 machine: one memory plus the AC and PC registers."""

    def __init__(self):
        self.memory = [0] * MEMORY_SIZE   # 4096 words, all start as 0
        self.ac = 0                       # accumulator
        self.pc = 0                       # program counter starts at 000
        # Source line of every loaded word (address -> line number).
        # Unused memory has no entry. Used to report "executing data"
        # on the line of the data word that PC reached.
        self.source_lines = {}

    def read(self, address):
        """Return the word stored at address (an Instruction or an int)."""
        return self.memory[address]

    def write(self, address, word):
        """Store a word at address, replacing what was there."""
        self.memory[address] = word
