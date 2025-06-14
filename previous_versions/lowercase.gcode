G21        ; Set units to millimeters
G91        ; Incremental positioning
G1 F1500   ; Feedrate

; --- LETTER a ---
G0 X10 Y5
M3
G3 X-10 Y0 R5
G3 X10 Y0 R5
G1 X0 Y-5
M5
G0 X5 Y0

; --- LETTER b ---
M3
G1 X5 Y0
G3 X0 Y10 R5
G3 X-5 Y-5 R5
M5
G0 X0 Y-5
M3
G1 X0 Y20
M5
G0 X15 Y-20

; --- LETTER c ---
G0 X10 Y7.5
M3
G3 X-5 Y2.5 R5
G3 X0 Y-10 R5
G3 X5 Y2.5 R5
M5
G0 X5 Y-2.5

; --- LETTER d ---
G0 X10 Y5
M3
G2 X-5 Y-5 R5
G2 X0 Y10 R5
G2 X5 Y-5 R5
M5
G0 X0 Y-5
M3
G1 X0 Y20
M5
G0 X5 Y-20

; --- LETTER e ---
G0 X0 Y5
M3
G1 X10 Y0
G3 X-10 Y0 R5
G3 X5 Y-5 R5
G1 X5 Y0
M5
G0 X5 Y0

; --- LETTER f ---
G0 X5 Y0
M3
G1 X0 Y12
G2 X5 Y5 R5
G1 X2 Y0
M5
G0 X-10 Y-7
M3
G1 X10 Y0
M5
G0 X3 Y-10

; --- LETTER g ---
G0 X10 Y5
M3
G2 X-5 Y-5 R5
G2 X0 Y10 R5
G2 X5 Y-5 R5
G1 X0 Y-8
G2 X-10 Y0 R5
M5
G0 X15 Y3

; --- LETTER h ---
G0 X10 Y0
M3
G1 X0 Y5
G3 X-10 Y0 R5
G1 X0 Y-5
G1 X0 Y20
M5
G0 X15 Y-20

; --- LETTER i ---
G0 X5 Y0
M3
G1 X0 Y10
M5
G0 X0 Y2
M3
G1 X0 Y2
M5
G0 X10 Y-14

; --- LETTER j ---
G0 X0 Y-3
M3
G3 X10 Y0 R5
G1 X0 Y13
M5
G0 X0 Y2
M3 
G1 X0 Y2
M5
G0 X5 Y-14

; --- LETTER k ---
M3
G1 X0 Y20
M5
G0 X8 Y-8
M3
G1 X-8 Y-6
G1 X8 Y-6
M5
G0 X7 Y0

; --- LETTER l ---
G0 X5 Y0
M3
G1 X0 Y18
M5
G0 X10 Y-18

; --- LETTER m ---
G0 X0 Y12
M3
G1 X0 Y-12
G1 X0 Y8
G2 X5 Y0 R2.5
G1 X0 Y-8
G1 X0 Y8
G2 X5 Y0 R2.5
G1 X0 Y-8
M5
G0 X5 Y0

; --- LETTER n ---
G0 X0 Y12
M3
G1 X0 Y-12
G1 X0 Y6
G2 X10 Y0 R5
G1 X0 Y-6
M5
G0 X5 Y0

; --- LETTER o ---
G0 X0 Y5
M3
G1 X0 Y1
G2 X10 Y0 R5
G1 X0 Y-1
G2 X-10 Y0 R5
M5
G0 X15 Y-5

; --- LETTER p ---
G0 X0 Y-8
M3
G1 X0 Y18
G1 X0 Y-5
G2 X10 Y0 R5
G2 X-10 Y0 R5
M5
G0 X15 Y-5

; --- LETTER q ---
G0 X10 Y-8
M3
G1 X0 Y18
G1 X0 Y-5
G3 X-10 Y0 R5
G3 X10 Y0 R5
M5
G0 X5 Y-5

; --- LETTER r ---
M3
G1 X0 Y12
G1 X0 Y-7
G2 X7.5 Y4.33 R5
M5
G0 X7.5 Y-9.33

; --- LETTER s ---
M3
G1 X5 Y0
G3 X0 Y5 R2.5
G1 X-2.5 Y0
G2 X0 Y5 R2.5
G1 X5 Y0
M5
G0 X5 Y-10

; --- LETTER t ---
G0 X0 Y10
M3 
G1 X10 Y0
M5
G0 X-6 Y6
M3
G1 X0 Y-13
G3 X2.5 Y-2.5 R2.5
G1 X3 Y0
M5
G0 X8 Y0

; --- LETTER u ---
G0 X0 Y10
M3
G1 X0 Y-5
G3 X10 Y0 R5
G1 X0 Y5
G1 X0 Y-10
M5
G0 X5 Y0

; --- LETTER v ---
G0 X0 Y10
M3
G1 X5 Y-10
G1 X5 Y10
M5
G0 X5 Y-10

; --- LETTER w ---
G0 X0 Y10
M3
G1 X2.5 Y-10
G1 X2.5 Y10
G1 X2.5 Y-10
G1 X2.5 Y10
M5
G0 X5 Y-10

; --- LETTER x ---
M3
G1 X10 Y10
M5
G0 X0 Y-10
M3
G1 X-10 Y10
M5
G0 X15 Y-10

; --- LETTER y ---
G0 X0 Y10
M3
G1 X0 Y-5
G3 X10 Y0 R5
G1 X0 Y5
G1 X0 Y-13
G2 X-10 Y0 R5
M5
G0 X15 Y3

; --- LETTER z ---
G0 X0 Y10
M3
G1 X10 Y0
G1 X-10 Y-10
G1 X10 Y0
M5
G0 X5 Y0

lc_letters_gcode = {
    'a': ['G0 X10 Y5', 'M3', 'G3 X-10 Y0 R5', 'G3 X10 Y0 R5', 'G1 X0 Y-5', 'M5', 'G0 X5 Y0'],
    'b': ['M3', 'G1 X5 Y0', 'G3 X0 Y10 R5', 'G3 X-5 Y-5 R5', 'M5', 'G0 X0 Y-5', 'M3', 'G1 X0 Y20', 'M5', 'G0 X15 Y-20'],
    'c': ['G0 X10 Y7.5', 'M3', 'G3 X-5 Y2.5 R5', 'G3 X0 Y-10 R5', 'G3 X5 Y2.5 R5', 'M5', 'G0 X5 Y-2.5'],
    'd': ['G0 X10 Y5', 'M3', 'G2 X-5 Y-5 R5', 'G2 X0 Y10 R5', 'G2 X5 Y-5 R5', 'M5', 'G0 X0 Y-5', 'M3', 'G1 X0 Y20', 'M5', 'G0 X5 Y-20'],
    'e': ['G0 X0 Y5', 'M3', 'G1 X10 Y0', 'G3 X-10 Y0 R5', 'G3 X5 Y-5 R5', 'G1 X5 Y0', 'M5', 'G0 X5 Y0'],
    'f': ['G0 X5 Y0', 'M3', 'G1 X0 Y12', 'G2 X5 Y5 R5', 'G1 X2 Y0', 'M5', 'G0 X-10 Y-7', 'M3', 'G1 X10 Y0', 'M5', 'G0 X3 Y-10'],
    'g': ['G0 X10 Y5', 'M3', 'G2 X-5 Y-5 R5', 'G2 X0 Y10 R5', 'G2 X5 Y-5 R5', 'G1 X0 Y-8', 'G2 X-10 Y0 R5', 'M5', 'G0 X15 Y3'],
    'h': ['G0 X10 Y0', 'M3', 'G1 X0 Y5', 'G3 X-10 Y0 R5', 'G1 X0 Y-5', 'G1 X0 Y20', 'M5', 'G0 X15 Y-20'],
    'i': ['G0 X5 Y0', 'M3', 'G1 X0 Y10', 'M5', 'G0 X0 Y2', 'M3', 'G1 X0 Y2', 'M5', 'G0 X10 Y-14'],
    'j': ['G0 X0 Y-3', 'M3', 'G3 X10 Y0 R5', 'G1 X0 Y13', 'M5', 'G0 X0 Y2', 'M3', 'G1 X0 Y2', 'M5', 'G0 X5 Y-14'],
    'k': ['M3', 'G1 X0 Y20', 'M5', 'G0 X8 Y-8', 'M3', 'G1 X-8 Y-6', 'G1 X8 Y-6', 'M5', 'G0 X7 Y0'],
    'l': ['G0 X5 Y0', 'M3', 'G1 X0 Y18', 'M5', 'G0 X10 Y-18'],
    'm': ['G0 X0 Y12', 'M3', 'G1 X0 Y-12', 'G1 X0 Y8', 'G2 X5 Y0 R2.5', 'G1 X0 Y-8', 'G1 X0 Y8', 'G2 X5 Y0 R2.5', 'G1 X0 Y-8', 'M5', 'G0 X5 Y0'],
    'n': ['G0 X0 Y12', 'M3', 'G1 X0 Y-12', 'G1 X0 Y6', 'G2 X10 Y0 R5', 'G1 X0 Y-6', 'M5', 'G0 X5 Y0'],
    'o': ['G0 X0 Y5', 'M3', 'G1 X0 Y1', 'G2 X10 Y0 R5', 'G1 X0 Y-1', 'G2 X-10 Y0 R5', 'M5', 'G0 X15 Y-5'],
    'p': ['G0 X0 Y-8', 'M3', 'G1 X0 Y18', 'G1 X0 Y-5', 'G2 X10 Y0 R5', 'G2 X-10 Y0 R5', 'M5', 'G0 X15 Y-5'],
    'q': ['G0 X10 Y-8', 'M3', 'G1 X0 Y18', 'G1 X0 Y-5', 'G3 X-10 Y0 R5', 'G3 X10 Y0 R5', 'M5', 'G0 X5 Y-5'],
    'r': ['M3', 'G1 X0 Y12', 'G1 X0 Y-7', 'G2 X7.5 Y4.33 R5', 'M5', 'G0 X7.5 Y-9.33'],
    's': ['M3', 'G1 X5 Y0', 'G3 X0 Y5 R2.5', 'G1 X-2.5 Y0', 'G2 X0 Y5 R2.5', 'G1 X5 Y0', 'M5', 'G0 X5 Y-10'],
    't': ['G0 X0 Y10', 'M3', 'G1 X10 Y0', 'M5', 'G0 X-6 Y6', 'M3', 'G1 X0 Y-13', 'G3 X2.5 Y-2.5 R2.5', 'G1 X3 Y0', 'M5', 'G0 X8 Y0'],
    'u': ['G0 X0 Y10', 'M3', 'G1 X0 Y-5', 'G3 X10 Y0 R5', 'G1 X0 Y5', 'G1 X0 Y-10', 'M5', 'G0 X5 Y0'],
    'v': ['G0 X0 Y10', 'M3', 'G1 X5 Y-10', 'G1 X5 Y10', 'M5', 'G0 X5 Y-10'],
    'w': ['G0 X0 Y10', 'M3', 'G1 X2.5 Y-10', 'G1 X2.5 Y10', 'G1 X2.5 Y-10', 'G1 X2.5 Y10', 'M5', 'G0 X5 Y-10'],
    'x': ['M3', 'G1 X10 Y10', 'M5', 'G0 X0 Y-10', 'M3', 'G1 X-10 Y10', 'M5', 'G0 X15 Y-10'],
    'y': ['G0 X0 Y10', 'M3', 'G1 X0 Y-5', 'G3 X10 Y0 R5', 'G1 X0 Y5', 'G1 X0 Y-13', 'G2 X-10 Y0 R5', 'M5', 'G0 X15 Y3'],
    'z': ['G0 X0 Y10', 'M3', 'G1 X10 Y0', 'G1 X-10 Y-10', 'G1 X10 Y0', 'M5', 'G0 X5 Y0']
}
