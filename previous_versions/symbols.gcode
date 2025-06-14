G21        ; Set units to millimeters
G91        ; Incremental positioning
G1 F1500   ; Feedrate

; --- . ---
M3
G1 X0 Y1
M5
G0 X5 Y-1

; --- , ---
G0 X0 Y-4
M3
G3 X5 Y5 R5
G1 X0 Y2
M5
G0 X5 Y-3

; --- < ---
G0 X8 Y16
M3
G1 X-8 Y-8
G1 X8 Y-8
M5
G0 X7 Y0

; --- > ---
G0 X0 Y16
M3
G1 X8 Y-8
G1 X-8 Y-8
M5
G0 X15 Y0

; --- / ---
M3
G1 X10 Y20
M5
G0 X5 Y-20

; --- \ ---
G0 X0 Y20
M3
G1 X10 Y-20
M5
G0 X5 Y0

; --- ? ---
G0 X5 Y0
M3
G1 X0 Y1
M5
G0 X0 Y4
M3
G1 X0 Y3
G3 X0 Y12 R6
G3 X-6 Y-6 R6
M5
G0 X16 Y-14

; --- ; ---
G0 X0 Y-4
M3
G3 X5 Y5 R5
G1 X0 Y2
M5
G0 X0 Y5
M3
G1 X0 Y1
M5
G0 X5 Y-9

; --- : ---
M3
G1 X0 Y1
M5
G0 X0 Y9
M3
G1 X0 Y1
M5
G0 X5 Y-11

; --- ' ---
G0 X0 Y15
M3
G3 X5 Y5 R5
M5
G0 X5 Y-20

; --- " ---
G0 X0 Y15
M3
G3 X5 Y5 R5
M5
G0 X0 Y-5
M3
G3 X5 Y5 R5
M5
G0 X5 Y-20

; --- [ ---
G0 X5 Y0
M3
G1 X-5 Y0
G1 X0 Y20
G1 X5 Y0
M5
G0 X5 Y-20

; --- ] ---
M3
G1 X5 Y0
G1 X0 Y20
G1 X-5 Y0
M5
G0 X10 Y-20

; --- { ---
G0 X5 Y0
M3
G2 X-3 Y6 R6
G3 X-2 Y4 R4
G3 X2 Y4 R4
G2 X3 Y6 R6
M5
G0 X5 Y-20

; --- } ---
M3
G3 X3 Y6 R6
G2 X2 Y4 R4
G2 X-2 Y4 R4
G3 X-3 Y6 R6
M5
G0 X10 Y-20

; --- | ---
M3
G1 X0 Y20
M5
G0 X5 Y-20

; --- ` ---
G0 X0 Y20
M3
G1 X2 Y-2
M5
G0 X3 Y-18

; --- ~ ---
G0 X0 Y10
M3
G2 X4 Y0 R2
G3 X4 Y0 R2
M5
G0 X7 Y-10

; --- ! ---
M3
G1 X0 Y1
M5
G0 X0 Y3
M3
G1 X0 Y16
M5
G0 X10 Y-20

; --- @ ---
G0 X7.5 Y0
M3
G1 X-2.5 Y0
G2 X-5 Y5 R5
G1 X0 Y10
G2 X10 Y0 R5
G1 X0 Y-10
G2 X-2 Y0 R1
G1 X0 Y6
G3 X-5 Y0 R2.5
G1 X0 Y-5
G3 X5 Y0 R2.5
M5
G0 X7 Y-6

; --- # ---
G0 X1 Y0
M3
G1 X2 Y20
M5
G0 X5 Y0
M3
G1 X-2 Y-20
M5
G0 X-7 Y6
M3
G1 X10 Y0
M5
G0 X1 Y8
M3
G1 X-10 Y0
M5
G0 X15 Y-14

; --- $ ---
G0 X0 Y2
M3
G1 X5 Y0
G3 X0 Y8 R4
G2 X0 Y8 R4
G1 X5 Y0
M5
G0 X-3 Y2
M3
G1 X-4 Y-20
M5
G0 X12 Y0

; --- % ---
M3
G1 X10 Y20
M5
G0 X-7 Y-5
M3
G1 X0 Y1
M5
G0 X4 Y-11
M3
G1 X0 Y-1
M5
G0 X8 Y-4

; --- ^ ---
G0 X0 Y14
M3
G1 X5 Y6
G1 X5 Y-6
M5
G0 X10 Y-14

; --- & ---
G0 X7 Y0
M3
G1 X-6 Y14
G2 X0 Y5 R5
G2 X5 Y0 R5
G2 X0 Y-5 R5
G1 X-6 Y-8
G3 X0 Y-5 R5
G3 X5 Y0 R5
G3 X2.5 Y2.5 R5
G1 X1 Y2
M5
G0 X6.5 Y-5.5

; --- * ---
G0 X5 Y12 
M3
G1 X0 Y8
M5
G0 X-4 Y-8
M3
G1 X8 Y8
M5
G0 X0 Y-8
M3
G1 X-8 Y8
M5
G0 X14 Y-20

; --- ( ---
G0 X5 Y0
M3
G2 X0 Y20 R15
M5
G0 X5 Y-20

; --- ) ---
M3
G3 X0 Y20 R15
M5
G0 X10 Y-20

; --- - ---
G0 X2 Y10
M3
G1 X6 Y0
M5
G0 X2 Y-10

; --- _ ---
M3
G1 X10 Y0
M5
G0 X5 Y0

; --- = ---
G0 X1 Y12
M3
G1 X8 Y0
M5
G0 X0 Y-4
M3
G1 X-8 Y0
M5
G0 X14 Y-8

; --- + ---
G0 X5 Y4
M3
G1 X0 Y12
M5
G0 X-5 Y-6
M3
G1 X10 Y0
M5
G0 X5 Y-10
