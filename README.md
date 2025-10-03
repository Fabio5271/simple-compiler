# simple-compiler
SIMPLE Programming Language compiler written in Python, that generates a Simpletron Machine Language (SML) program.

SIMPLE is an imaginary programming language similar to the first versions of BASIC, and SML is the language of a simpletron machine, a simple, imaginary machine that has an accumulator that can store a value, and 100 memory adresses that it can store SML instructions, variables, and constants in. Each item of these is represented by a 4-digit signed integer in a specific simpletron memory adress.

[SIMPLE Documentation (pt-br)](http://www.ybadoo.com.br/tutoriais/cmp/11/)
[SML Documentation (pt-br)](http://www.ybadoo.com.br/tutoriais/cmp/10/)

This is a completed university project on the subject of compilers, made with the objective of understanding how a compiler works. This is not a compiler designed for speed and efficiency, as, first of all, it would have to have been written in C to even have a chance of excelling at that. The focus here is on the compiling process, as well as demonstrating many Python development concepts in practice. The code comments and strings are all in Brazilian Portuguese (pt-br), as my university is Brazilian.

To use the compiler, insert/copy the SIMPLE source code into source.txt, and run compiler.py. The output binary will be saved as binary.txt.
