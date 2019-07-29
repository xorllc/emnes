# -*- coding: utf-8 -*-
# Dump of the opcode table at
# http://www.thealmightyguru.com/Games/Hacking/Wiki/index.php/6502_Opcodes
wiki_inst_dump = """
00  BRK
01  ORA (Indirect, X)
02
03
04
05  ORA Zero Page
06  ASL Zero Page
07
08  PHP
09  ORA Immediate
0A  ASL Accumulator
0B
0C
0D  ORA Absolute
0E  ASL Absolute
0F
10  BPL
11  ORA (Indirect), Y
12
13
14
15  ORA Zero Page, X
16  ASL Zero Page, X
17
18  CLC
19  ORA Absolute, Y
1A
1B
1C
1D  ORA Absolute, X
1E  ASL Absolute, X
1F
20  JSR
21  AND (Indirect, X)
22
23
24  BIT Zero Page
25  AND Zero Page
26  ROL Zero Page
27
28  PLP
29  AND Immediate
2A  ROL Accumulator
2B
2C  BIT Absolute
2D  AND Absolute
2E  ROL Absolute
2F
30  BMI
31  AND (Indirect), Y
32
33
34
35  AND Zero Page, X
36  ROL Zero Page, X
37
38  SEC
39  AND Absolute, Y
3A
3B
3C
3D  AND Absolute, X
3E  ROL Absolute, X
3F
40  RTI
41  EOR (Indirect, X)
42
43
44
45  EOR Zero Page
46  LSR Zero Page
47
48  PHA
49  EOR Immediate
4A  LSR Accumulator
4B
4C  JMP Absolute
4D  EOR Absolute
4E  LSR Absolute
4F
50  BVC
51  EOR (Indirect), Y
52
53
54
55  EOR Zero Page, X
56  LSR Zero Page, X
57
58  CLI
59  EOR Absolute, Y
5A
5B
5C
5D  EOR Absolute, X
5E  LSR Absolute, X
5F
60  RTS
61  ADC (Indirect, X)
62
63
64
65  ADC Zero Page
66  ROR Zero Page
67
68  PLA
69  ADC Immediate
6A  ROR Accumulator
6B
6C  JMP Indirect
6D  ADC Absolute
6E  ROR Absolute
6F
70  BVS
71  ADC (Indirect), Y
72
73
74
75  ADC Zero Page, X
76  ROR Zero Page, X
77
78  SEI
79  ADC Absolute, Y
7A
7B
7C
7D  ADC Absolute, X
7E  ROR Absolute, X
7F
80
81  STA (Indirect, X)
82
83
84  STY Zero Page
85  STA Zero Page
86  STX Zero Page
87
88  DEY
89
8A  TXA
8B
8C  STY Absolute
8D  STA Absolute
8E  STX Absolute
8F
90  BCC
91  STA (Indirect), Y
92
93
94  STY Zero Page, X
95  STA Zero Page, X
96  STX Zero Page, Y
97
98  TYA
99  STA Absolute, Y
9A  TXS
9B
9C
9D  STA Absolute, X
9E
9F
A0  LDY Immediate
A1  LDA (Indirect, X)
A2  LDX Immediate
A3
A4  LDY Zero Page
A5  LDA Zero Page
A6  LDX Zero Page
A7
A8  TAY
A9  LDA Immediate
AA  TAX
AB
AC  LDY Absolute
AD  LDA Absolute
AE  LDX Absolute
AF
B0  BCS
B1  LDA (Indirect), Y
B2
B3
B4  LDY Zero Page, X
B5  LDA Zero Page, X
B6  LDX Zero Page, Y
B7
B8  CLV
B9  LDA Absolute, Y
BA  TSX
BB
BC  LDY Absolute, X
BD  LDA Absolute, X
BE  LDX Absolute, Y
BF
C0  CPY Immediate
C1  CMP (Indirect, X)
C2
C3
C4  CPY Zero Page
C5  CMP Zero Page
C6  DEC Zero Page
C7
C8  INY
C9  CMP Immediate
CA  DEX
CB
CC  CPY Absolute
CD  CMP Absolute
CE  DEC Absolute
CF
D0  BNE
D1  CMP (Indirect), Y
D2
D3
D4
D5  CMP Zero Page, X
D6  DEC Zero Page, X
D7
D8  CLD
D9  CMP Absolute, Y
DA
DB
DC
DD  CMP Absolute, X
DE  DEC Absolute, X
DF
E0  CPX Immediate
E1  SBC (Indirect, X)
E2
E3
E4  CPX Zero Page
E5  SBC Zero Page
E6  INC Zero Page
E7
E8  INX
E9  SBC Immediate
EA  NOP
EB
EC  CPX Absolute
ED  SBC Absolute
EE  INC Absolute
EF
F0  BEQ
F1  SBC (Indirect), Y
F2
F3
F4
F5  SBC Zero Page, X
F6  INC Zero Page, X
F7
F8  SED
F9  SBC Absolute, Y
FA
FB
FC
FD  SBC Absolute, X
FE  INC Absolute, X
FF
"""
instructions = []
for line in wiki_inst_dump.split("\n"):
    if len(line) == 2:
        instructions.append(None)
    elif len(line) > 2:
        instructions.append(" ".join(line.split(" ")[1:]).strip())
