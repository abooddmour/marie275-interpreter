"""MARIE275 interpreter package.

The interpreter is split into the stages from the project description:
    parser.py     - stage 1: split each source line into label / instruction / operand
    loader.py     - stage 2: two passes, symbol table, place words in memory
    machine.py    - stage 3: memory (4096 words), AC and PC
    executor.py   - stage 4: the fetch-decode-execute loop
    io_handler.py - stage 5: Input values, Output and the trace
    cli.py        - the command line (arguments, error reporting, exit codes)
"""
