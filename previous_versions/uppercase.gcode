G21        ; Set units to millimeters
G91        ; Incremental positioning
G1 F1500   ; Feedrate

G0 X0 Y0

; --- LETTER A ---
M3
G1 X5 Y20
G1 X5 Y-20
G0 X-7.5 Y10
M3
G1 X5 Y0
M5
G0 X7.5 Y-10

; --- LETTER B ---
M3
G1 X0 Y20
G1 X5 Y0
G2 X0 Y-10 R5
G1 X-5 Y0
G1 X5 Y0
G2 X0 Y-10 R5
G1 X-5 Y0
M5
G0 X15 Y0

; --- LETTER C ---
G0 X10 Y20
M3
G3 X-10 Y-10 R10
G3 X10 Y-10 R10
M5
G0 X5 Y0

; --- LETTER D ---
M3
G1 X0 Y20
G2 X0 Y-20 R10
M5
G0 X15 Y0

; --- LETTER E ---
M3
G1 X0 Y20
G1 X10 Y0
G0 X-10 Y-10
M3
G1 X10 Y0
G0 X-10 Y-10
M3
G1 X10 Y0
M5
G0 X5 Y0

; --- LETTER F ---
M3
G1 X0 Y20
G1 X10 Y0
G0 X-10 Y-10
M3
G1 X10 Y0
M5
G0 X5 Y-10

; --- LETTER G ---
G0 X10 Y20
M3
G3 X-10 Y-10 R10
G3 X10 Y-10 R10
G1 X0 Y10
G1 X-5 Y0
M5
G0 X10 Y-10

; --- LETTER H ---
M3
G1 X0 Y20
M5
G0 X10 Y0
M3
G1 X0 Y-20
M5
G0 X-10 Y10
M3
G1 X10 Y0
M5
G0 X5 Y-10

; --- LETTER I ---
G0 X5 Y0
M3
G1 X0 Y20
M5
G0 X10 Y-20

; --- LETTER J ---
G0 X10 Y20
M3
G1 X0 Y-15
G2 X-10 Y0 R5
G1 X0 Y2.5
M5
G0 X15 Y-7.5

; --- LETTER K---
M3
G1 X0 Y20
M5
G0 X10 Y0
M3
G1 X-10 Y-10
G1 X10 Y-10
M5
G0 X5 Y0

; --- LETTER L ---
M3
G1 X0 Y20
G1 X0 Y-20
G1 X10 Y0
M5
G0 X5 Y0

; --- LETTER M ---
M3
G1 X0 Y20
G1 X5 Y-10
G1 X5 Y10
G1 X0 Y-20
M5
G0 X5 Y0

; --- LETTER N---
M3
G1 X0 Y20
G1 X10 Y-20
G1 X0 Y20
M5
G0 X5 Y-20

; --- LETTER O ---
G0 X0 Y5
M3
G1 X0 Y10
G2 X10 Y0 R5
G1 X0 Y-10
G2 X-10 Y0 R5
M5
G0 X15 Y-5

; --- LETTER P ---
M3
G1 X0 Y20
G1 X5 Y0
G2 X0 Y-10 R5
G1 X-5 Y0
M5
G0 X15 Y-10

; --- LETTER Q ---
G0 X0 Y5
M3
G1 X0 Y10
G2 X10 Y0 R5
G1 X0 Y-10
G2 X-10 Y0 R5
M5
G0 X5 Y0
M3
G1 X5 Y-5
M5
G0 X5 Y0

; --- LETTER R ---
M3
G1 X0 Y20
G1 X5 Y0
G2 X0 Y-10 R5
G1 X-5 Y0
G1 X10 Y-10
M5
G0 X5 Y0

; --- LETTER S ---
M3
G1 X5 Y0
G3 X0 Y10 R5
G2 X0 Y10 R5
G1 X5 Y0
M5
G0 X5 Y-20

; --- LETTER T ---
G0 X5 Y0
M3
G1 X0 Y20
M5 
G0 X-5 Y0
M3
G1 X10 Y0
M5
G0 X5 Y-20

; --- LETTER U ---
G0 X0 Y20
M3
G1 X0 Y-15
G3 X10 Y0 R5
G1 X0 Y15
M5
G0 X5 Y-20

; --- LETTER V ---
G0 X0 Y20
M3
G1 X5 Y-20
G1 X5 Y20
M5
G0 X5 Y-20

; --- LETTER W ---
G0 X0 Y20
M3
G1 X2.5 Y-20
G1 X2.5 Y10
G1 X2.5 Y-10
G1 X2.5 Y20
M5
G0 X5 Y-20

; --- LETTER X ---
G0 X0 Y0
M3
G1 X10 Y20
M5
G0 X-10 Y0
M3
G1 X10 Y-20
M5
G0 X5 Y0

; --- LETTER Y ---
G0 X0 Y20
M3
G1 X5 Y-10
G1 X5 Y10
M5
G1 X-5 Y-10
M3
G1 X0 Y-10
M5
G0 X10 Y0

; --- LETTER Z ---
G0 X0 Y20
M3
G1 X10 Y0
G1 X-10 Y-20
G1 X10 Y0
M5
G0 X5 Y0

uc_letters_gcode = {
    'A': ['M3', 'G1 X5 Y20', 'G1 X5 Y-20', 'G0 X-7.5 Y10', 'M3', 'G1 X5 Y0', 'M5', 'G0 X7.5 Y-10'],
    'B': ['M3', 'G1 X0 Y20', 'G1 X5 Y0', 'G2 X0 Y-10 R5', 'G1 X-5 Y0', 'G1 X5 Y0', 'G2 X0 Y-10 R5', 'G1 X-5 Y0', 'M5', 'G0 X15 Y0'],
    'C': ['G0 X10 Y20', 'M3', 'G3 X-10 Y-10 R10', 'G3 X10 Y-10 R10', 'M5', 'G0 X5 Y0'],
    'D': ['M3', 'G1 X0 Y20', 'G2 X0 Y-20 R10', 'M5', 'G0 X15 Y0'],
    'E': ['M3', 'G1 X0 Y20', 'G1 X10 Y0', 'G0 X-10 Y-10', 'M3', 'G1 X10 Y0', 'G0 X-10 Y-10', 'M3', 'G1 X10 Y0', 'M5', 'G0 X5 Y0'],
    'F': ['M3', 'G1 X0 Y20', 'G1 X10 Y0', 'G0 X-10 Y-10', 'M3', 'G1 X10 Y0', 'M5', 'G0 X5 Y-10'],
    'G': ['G0 X10 Y20', 'M3', 'G3 X-10 Y-10 R10', 'G3 X10 Y-10 R10', 'G1 X0 Y10', 'G1 X-5 Y0', 'M5', 'G0 X10 Y-10'],
    'H': ['M3', 'G1 X0 Y20', 'M5', 'G0 X10 Y0', 'M3', 'G1 X0 Y-20', 'M5', 'G0 X-10 Y10', 'M3', 'G1 X10 Y0', 'M5', 'G0 X5 Y-10'],
    'I': ['G0 X5 Y0', 'M3', 'G1 X0 Y20', 'M5', 'G0 X10 Y-20'],
    'J': ['G0 X10 Y20', 'M3', 'G1 X0 Y-15', 'G2 X-10 Y0 R5', 'G1 X0 Y2.5', 'M5', 'G0 X15 Y-7.5'],
    'K': ['M3', 'G1 X0 Y20', 'M5', 'G0 X10 Y0', 'M3', 'G1 X-10 Y-10', 'G1 X10 Y-10', 'M5', 'G0 X5 Y0'],
    'L': ['M3', 'G1 X0 Y20', 'G1 X0 Y-20', 'G1 X10 Y0', 'M5', 'G0 X5 Y0'],
    'M': ['M3', 'G1 X0 Y20', 'G1 X5 Y-10', 'G1 X5 Y10', 'G1 X0 Y-20', 'M5', 'G0 X5 Y0'],
    'N': ['M3', 'G1 X0 Y20', 'G1 X10 Y-20', 'G1 X0 Y20', 'M5', 'G0 X5 Y-20'],
    'O': ['G0 X0 Y5', 'M3', 'G1 X0 Y10', 'G2 X10 Y0 R5', 'G1 X0 Y-10', 'G2 X-10 Y0 R5', 'M5', 'G0 X15 Y-5'],
    'P': ['M3', 'G1 X0 Y20', 'G1 X5 Y0', 'G2 X0 Y-10 R5', 'G1 X-5 Y0', 'M5', 'G0 X15 Y-10'],
    'Q': ['G0 X0 Y5', 'M3', 'G1 X0 Y10', 'G2 X10 Y0 R5', 'G1 X0 Y-10', 'G2 X-10 Y0 R5', 'M5', 'G0 X5 Y0', 'M3', 'G1 X5 Y-5', 'M5', 'G0 X5 Y0'],
    'R': ['M3', 'G1 X0 Y20', 'G1 X5 Y0', 'G2 X0 Y-10 R5', 'G1 X-5 Y0', 'G1 X10 Y-10', 'M5', 'G0 X5 Y0'],
    'S': ['M3', 'G1 X5 Y0', 'G3 X0 Y10 R5', 'G2 X0 Y10 R5', 'G1 X5 Y0', 'M5', 'G0 X5 Y-20'],
    'T': ['G0 X5 Y0', 'M3', 'G1 X0 Y20', 'M5', 'G0 X-5 Y0', 'M3', 'G1 X10 Y0', 'M5', 'G0 X5 Y-20'],
    'U': ['G0 X0 Y20', 'M3', 'G1 X0 Y-15', 'G3 X10 Y0 R5', 'G1 X0 Y15', 'M5', 'G0 X5 Y-20'],
    'V': ['G0 X0 Y20', 'M3', 'G1 X5 Y-20', 'G1 X5 Y20', 'M5', 'G0 X5 Y-20'],
    'W': ['G0 X0 Y20', 'M3', 'G1 X2.5 Y-20', 'G1 X2.5 Y10', 'G1 X2.5 Y-10', 'G1 X2.5 Y20', 'M5', 'G0 X5 Y-20'],
    'X': ['G0 X0 Y0', 'M3', 'G1 X10 Y20', 'M5', 'G0 X-10 Y0', 'M3', 'G1 X10 Y-20', 'M5', 'G0 X5 Y0'],
    'Y': ['G0 X0 Y20', 'M3', 'G1 X5 Y-10', 'G1 X5 Y10', 'M5', 'G1 X-5 Y-10', 'M3', 'G1 X0 Y-10', 'M5', 'G0 X10 Y0'],
    'Z': ['G0 X0 Y20', 'M3', 'G1 X10 Y0', 'G1 X-10 Y-20', 'G1 X10 Y0', 'M5', 'G0 X5 Y0']
}
