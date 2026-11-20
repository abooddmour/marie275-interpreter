"""Stage 4: execution (the fetch-decode-execute loop).

The machine repeats one cycle until Halt:
    1. Fetch:   read the word that PC points at
    2. Advance: PC <- PC + 1
    3. Execute: run the handler for that instruction

There is one small method per instruction (exec_load, exec_add, ...),
and the HANDLERS table maps each instruction name to its method.
Every arithmetic result goes through to_signed16() so the numbers wrap
around exactly like 16-bit hardware.
"""

from marie.errors import MarieError
from marie.machine import MEMORY_SIZE, is_instruction, to_signed16

# More than this many executed instructions is treated as an infinite loop.
MAX_STEPS = 100_000


class Executor:
    """Runs a loaded program on a Machine."""

    def __init__(self, machine, io):
        self.machine = machine
        self.io = io            # IOHandler: input values and output
        self.halted = False
        self.steps = 0          # how many instructions have been executed
        self.last_line = 0      # line of the last instruction that ran

    # ------------------------------------------------------------ main loop

    def run(self):
        """Run until Halt, or until a MarieError is raised."""
        while not self.halted:
            self.step()

    def step(self):
        """Fetch, decode and execute one instruction."""
        m = self.machine
        address = m.pc

        # Fetch. PC must point at an instruction, not at a number.
        if address >= MEMORY_SIZE:
            raise MarieError(self.last_line, "executing data: PC ran past the end of memory")
        word = m.read(address)
        if not is_instruction(word):
            # A data word reports its own line; unused memory (no line)
            # reports the line of the last instruction that ran.
            line = m.source_lines.get(address, self.last_line)
            raise MarieError(line, f"executing data at address {address:03X}")

        # Step limit: 100,000 instructions have already run, so running
        # this one would be "more than 100,000" (a likely infinite loop).
        if self.steps >= MAX_STEPS:
            raise MarieError(word.line, f"too many steps (more than {MAX_STEPS:,} instructions)")

        # Advance PC before carrying out the instruction.
        m.pc = address + 1

        # Decode: find the handler for this instruction, then execute it.
        handler = self.HANDLERS[word.name]
        handler(self, word)
        self.steps += 1
        self.last_line = word.line

        # --trace: print the address, the instruction and the new AC.
        self.io.write_trace(address, word, m.ac)

    # ------------------------------------------------------------ helpers

    def read_number(self, instr, address):
        """Read a number from memory for an arithmetic/logic instruction.

        Reading a cell that holds an instruction is an error, reported
        on the line of the instruction that tried to read it.
        """
        word = self.machine.read(address)
        if is_instruction(word):
            raise MarieError(instr.line,
                             f"reading an instruction as data at address {address:03X}")
        return word

    # ------------------------------------------------------------ data moves

    def exec_load(self, instr):
        # AC <- M[X]
        self.machine.ac = self.read_number(instr, instr.operand)

    def exec_store(self, instr):
        # M[X] <- AC   (if X held an instruction, it is now a number)
        self.machine.write(instr.operand, self.machine.ac)

    def exec_clear(self, instr):
        # AC <- 0
        self.machine.ac = 0

    # ------------------------------------------------------------ arithmetic

    def exec_add(self, instr):
        # AC <- AC + M[X]
        value = self.read_number(instr, instr.operand)
        self.machine.ac = to_signed16(self.machine.ac + value)

    def exec_subt(self, instr):
        # AC <- AC - M[X]
        value = self.read_number(instr, instr.operand)
        self.machine.ac = to_signed16(self.machine.ac - value)

    def exec_mult(self, instr):
        # AC <- AC * M[X], keeping only the low 16 bits
        value = self.read_number(instr, instr.operand)
        self.machine.ac = to_signed16(self.machine.ac * value)

    def exec_div(self, instr):
        # AC <- AC / M[X], rounding toward zero (17/5 = 3, -7/2 = -3).
        # Python's // rounds down (-7 // 2 = -4), so we divide the
        # absolute values and then put the sign back ourselves.
        divisor = self.read_number(instr, instr.operand)
        if divisor == 0:
            raise MarieError(instr.line, "division by zero")
        dividend = self.machine.ac
        quotient = abs(dividend) // abs(divisor)
        if (dividend < 0) != (divisor < 0):     # signs differ -> negative
            quotient = -quotient
        # -32768 / -1 = 32768 does not fit, so it wraps to -32768.
        self.machine.ac = to_signed16(quotient)

    # ------------------------------------------------------------ logic

    def exec_and(self, instr):
        # AC <- AC AND M[X], bit by bit on all 16 bits
        value = self.read_number(instr, instr.operand)
        self.machine.ac = to_signed16((self.machine.ac & 0xFFFF) & (value & 0xFFFF))

    def exec_or(self, instr):
        # AC <- AC OR M[X], bit by bit on all 16 bits
        value = self.read_number(instr, instr.operand)
        self.machine.ac = to_signed16((self.machine.ac & 0xFFFF) | (value & 0xFFFF))

    def exec_not(self, instr):
        # AC <- NOT AC: flip all 16 bits (same as -AC - 1, so Not 5 = -6)
        self.machine.ac = to_signed16(self.machine.ac ^ 0xFFFF)

    # ------------------------------------------------------------ input / output

    def exec_input(self, instr):
        # AC <- next value from the --input list
        self.machine.ac = self.io.read_input(instr.line)

    def exec_output(self, instr):
        # print AC in decimal; AC does not change
        self.io.write_output(self.machine.ac)

    # ------------------------------------------------------------ control

    def exec_jump(self, instr):
        # PC <- X: the next instruction is fetched from address X
        self.machine.pc = instr.operand

    def exec_skipcond(self, instr):
        # If the condition holds, skip the next instruction (PC <- PC + 1).
        #   000: AC < 0     400: AC = 0     800: AC > 0
        ac = self.machine.ac
        condition = instr.operand
        if (condition == 0x000 and ac < 0) or \
           (condition == 0x400 and ac == 0) or \
           (condition == 0x800 and ac > 0):
            self.machine.pc += 1

    def exec_halt(self, instr):
        # Stop the machine.
        self.halted = True

    # Instruction name -> method that carries it out.
    HANDLERS = {
        "Load":  exec_load,
        "Store": exec_store,
        "Clear": exec_clear,
        "Add":   exec_add,
        "Subt":  exec_subt,
        "Mult":  exec_mult,
        "Div":   exec_div,
        "And":   exec_and,
        "Or":    exec_or,
        "Not":   exec_not,
        "Input": exec_input,
        "Output": exec_output,
        "Jump":  exec_jump,
        "Skipcond": exec_skipcond,
        "Halt":  exec_halt,
    }
