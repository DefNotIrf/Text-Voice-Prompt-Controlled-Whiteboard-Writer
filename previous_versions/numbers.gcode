G21        ; Set units to millimeters
G91        ; Incremental positioning
G1 F1500   ; Feedrate

; --- ZERO ---
G0 X0 Y5
M3
G1 X0 Y10
G2 X10 Y0 R5
G1 X0 Y-10
G2 X-10 Y0 R5
M5
G0 X15 Y-5

['G1 X0 Y5', 'M3', 'G1 X0 Y10', 'G2 X10 Y0 R5', 'G1 X0 Y-10', 'G2 X-10 Y0 R5', 'M5', 'G0 X15 Y-5']


; --- ONE ---
G0 X5 Y0
M3
G1 X0 Y20
G1 X-3 Y-3
M5
G0 X13 Y-17

['G0 X5 Y0', 'M3', 'G1 X0 Y20', 'G1 X-3 Y-3', 'M5', 'G0 X13 Y-17']

; --- TWO ---
G0 X0 Y15
M3 
G2 X10 Y0 R5
G1 X-10 Y-15
G1 X10 Y0
M5
G0 X5 Y0

['G0 X0 Y15', 'M3', 'G2 X10 Y0 R5', 'G1 X-10 Y-15', 'G1 X10 Y0', 'M5', 'G0 X5 Y0']

; --- THREE ---
G0 X0 Y20
M3 
G1 X5 Y0
G2 X0 Y-10 R5
G1 X-5 Y0
G1 X5 Y0
G2 X0 Y-10 R5
G1 X-5 Y0
M5
G0 X15 Y0

['G0 X0 Y20', 'M3', 'G1 X5 Y0', 'G2 X0 Y-10 R5', 'G1 X-5 Y0', 'G1 X5 Y0', 'G2 X0 Y-10 R5', 'G1 X-5 Y0', 'M5', 'G0 X15 Y0']

; --- FOUR ---
G0 X8 Y0
M3
G1 X0 Y20
G1 X-8 Y-15
G1 X10 Y0
M5
G0 X5 Y-5

['G0 X8 Y0', 'M3', 'G1 X0 Y20', 'G1 X-8 Y-15', 'G1 X10 Y0', 'M5', 'G0 X5 Y-5']

; --- FIVE ---
M3
G1 X4 Y0 
G3 X0 Y12 R6
G1 X-4 Y0
G1 X0 Y8
G1 X10 Y0
M5
G0 X5 Y-20

['M3', 'G1 X4 Y0', 'G3 X0 Y12 R6', 'G1 X-4 Y0', 'G1 X0 Y8', 'G1 X10 Y0', 'M5', 'G0 X5 Y-20']

; --- SIX ---
G0 X10 Y20
M3
G3 X-10 Y-10 R10
G1 X0 Y-5
G3 X10 Y0 R5
G3 X-10 Y0 R5
M5
G0 X15 Y-5 

['G0 X10 Y20', 'M3', 'G3 X-10 Y-10 R10', 'G1 X0 Y-5', 'G3 X10 Y0 R5', 'G3 X-10 Y0 R5', 'M5', 'G0 X15 Y-5']

; --- SEVEN ---
G0 X0 Y20
M3
G1 X10 Y0
G1 X-5 Y-20
M5
G0 X10 Y0

['G0 X0 Y20', 'M3', 'G1 X10 Y0', 'G1 X-5 Y-20', 'M5', 'G0 X10 Y0']

; --- EIGHT ---
G0 X5 Y0
M3
G3 X0 Y10 R5
G2 X0 Y10 R5
G2 X0 Y-10 R5
G3 X0 Y-10 R5
M5
G0 X10 Y0

['G0 X5 Y0', 'M3', 'G3 X0 Y10 R5', 'G2 X0 Y10 R5', 'G2 X0 Y-10 R5', 'G3 X0 Y-10 R5', 'M5', 'G0 X10 Y0']

; --- NINE ---
M3
G3 X10 Y10 R10
G1 X0 Y5
G3 X-10 Y0 R5
G3 X10 Y0 R5
M5
G0 X5 Y-15

['M3', 'G3 X10 Y10 R10', 'G1 X0 Y5', 'G3 X-10 Y0 R5', 'G3 X10 Y0 R5', 'M5', 'G0 X5 Y-15']

numbers_gcode = {
    '0': ['G1 X0 Y5', 'M3', 'G1 X0 Y10', 'G2 X10 Y0 R5', 'G1 X0 Y-10', 'G2 X-10 Y0 R5', 'M5', 'G0 X15 Y-5'],
    '1': ['G0 X5 Y0', 'M3', 'G1 X0 Y20', 'G1 X-3 Y-3', 'M5', 'G0 X13 Y-17'],
    '2': ['G0 X0 Y15', 'M3', 'G2 X10 Y0 R5', 'G1 X-10 Y-15', 'G1 X10 Y0', 'M5', 'G0 X5 Y0'],
    '3': ['G0 X0 Y20', 'M3', 'G1 X5 Y0', 'G2 X0 Y-10 R5', 'G1 X-5 Y0', 'G1 X5 Y0', 'G2 X0 Y-10 R5', 'G1 X-5 Y0', 'M5', 'G0 X15 Y0'],
    '4': ['G0 X8 Y0', 'M3', 'G1 X0 Y20', 'G1 X-8 Y-15', 'G1 X10 Y0', 'M5', 'G0 X5 Y-5'],
    '5': ['M3', 'G1 X4 Y0', 'G3 X0 Y12 R6', 'G1 X-4 Y0', 'G1 X0 Y8', 'G1 X10 Y0', 'M5', 'G0 X5 Y-20'],
    '6': ['G0 X10 Y20', 'M3', 'G3 X-10 Y-10 R10', 'G1 X0 Y-5', 'G3 X10 Y0 R5', 'G3 X-10 Y0 R5', 'M5', 'G0 X15 Y-5'],
    '7': ['G0 X0 Y20', 'M3', 'G1 X10 Y0', 'G1 X-5 Y-20', 'M5', 'G0 X10 Y0'],
    '8': ['G0 X5 Y0', 'M3', 'G3 X0 Y10 R5', 'G2 X0 Y10 R5', 'G2 X0 Y-10 R5', 'G3 X0 Y-10 R5', 'M5', 'G0 X10 Y0'],
    '9': ['M3', 'G3 X10 Y10 R10', 'G1 X0 Y5', 'G3 X-10 Y0 R5', 'G3 X10 Y0 R5', 'M5', 'G0 X5 Y-15']
}
