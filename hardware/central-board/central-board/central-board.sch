EESchema Schematic File Version 4
LIBS:power
LIBS:device
LIBS:Connector_Generic
LIBS:Switch
LIBS:Transistor_FET
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 7
Title "Teensy 4.1 Central Board - Module Index"
Date "2026-08-04"
Rev "A - HUMAN REVIEW DRAFT"
Comp "Differential Swerve"
Comment1 "Responsibility-based hierarchical schematic"
Comment2 "Global labels connect modules"
$EndDescr
Text Notes 700 650 0    90   ~ 18
CENTRAL BOARD RESPONSIBILITY MAP
Text Notes 700 900 0    50   ~ 12
Open each child sheet and review its inputs, outputs, protection and TBD gates independently.
$Sheet
S 900 1300 2800 1400
U 7001
F0 "100 100 Power Input and 5V Distribution" 60
F1 "modules/100-power.sch" 50
$EndSheet
$Sheet
S 4400 1300 2800 1400
U 7002
F0 "200 200 Teensy 4.1 Carrier and Safety GPIO" 60
F1 "modules/200-teensy.sch" 50
$EndSheet
$Sheet
S 7900 1300 2800 1400
U 7003
F0 "300-500 300-500 CAN Communication" 60
F1 "modules/300-can.sch" 50
$EndSheet
$Sheet
S 900 3600 2800 1400
U 7004
F0 "600 600 E-stop and Contactor Safety" 60
F1 "modules/600-safety.sch" 50
$EndSheet
$Sheet
S 4400 3600 2800 1400
U 7005
F0 "700 700 Battery and Motor Power Monitoring" 60
F1 "modules/700-monitoring.sch" 50
$EndSheet
$Sheet
S 7900 3600 2800 1400
U 7006
F0 "800-900 800 Expansion and Test Access" 60
F1 "modules/800-expansion.sch" 50
$EndSheet
Text Notes 900 5800 0    55   ~ 12
Cross-module nets use global labels: +5V_SYS, +5V_TEENSY, +3V3_TEENSY, GND_CTRL, CANx_TX/RX, safety and I2C signals.
Text Notes 900 6050 0    55   ~ 12
PCB gate: replace pin-explicit generic IC symbols, close every TBD, save as current .kicad_sch, then reach ERC 0.
$EndSCHEMATC
