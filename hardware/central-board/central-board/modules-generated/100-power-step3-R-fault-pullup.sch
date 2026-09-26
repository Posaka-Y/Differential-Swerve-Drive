EESchema Schematic File Version 4
LIBS:Device
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "Step3: FAULT pull-up"
Date "2026-09-14"
Rev "A - DRAFT"
Comp "Differential Swerve"
$EndDescr
$Comp
L Device:R R105
U 1 1 5F000003
P 2000 1000
F 0 "R105" H 1900 1220 50  0000 C CNN
F 1 "10k" H 1900 1130 50  0000 C CNN
F 2 "" H 2000 1000 50  0001 C CNN
	1    2000 1000
	0    -1   -1   0
$EndComp
Wire Wire Line
	1900 1000 1650 1000
Text Label 1650 1000 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	2100 1000 2350 1000
Text Label 2350 1000 0    40   ~ 0
PWR_5V_FAULT_N
$EndSCHEMATC
