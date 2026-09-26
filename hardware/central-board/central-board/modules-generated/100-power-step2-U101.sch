EESchema Schematic File Version 4
LIBS:Connector_Generic
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "Step2: U101 TPS259470 eFuse"
Date "2026-09-14"
Rev "A - DRAFT"
Comp "Differential Swerve"
$EndDescr
$Comp
L Connector_Generic:Conn_01x10 U101
U 1 1 5F000002
P 2350 1000
F 0 "U101" H 2250 1650 50  0000 C CNN
F 1 "TPS259470LRPWR" H 2250 1560 50  0000 C CNN
F 2 "Package_DFN_QFN:WQFN-10-1EP_2x2mm_P0.5mm_EP0.75x1.6mm" H 2350 1000 50  0001 C CNN
	1    2350 1000
	-1   0    0    1
$EndComp
Wire Wire Line
	2550 1000 3100 1000
Text Label 3100 1000 0    40   ~ 0
EN_UVLO
Wire Wire Line
	2550 1100 3100 1100
Text Label 3100 1100 0    40   ~ 0
OVLO
Wire Wire Line
	2550 1200 3100 1200
Text Label 3100 1200 0    40   ~ 0
AUXOFF
Wire Wire Line
	2550 1300 3100 1300
Text Label 3100 1300 0    40   ~ 0
PWR_5V_FAULT_N
Wire Wire Line
	2550 1400 3100 1400
Text Label 3100 1400 0    40   ~ 0
+5V_FUSED_IN
Wire Wire Line
	2550 1500 3100 1500
Text Label 3100 1500 0    40   ~ 0
+5V_PROT
Wire Wire Line
	2550 1600 3100 1600
Text Label 3100 1600 0    40   ~ 0
DVDT
Wire Wire Line
	2550 1700 3100 1700
Text Label 3100 1700 0    40   ~ 0
GND_CTRL
Wire Wire Line
	2550 1800 3100 1800
Text Label 3100 1800 0    40   ~ 0
ILM
Wire Wire Line
	2550 1900 3100 1900
Text Label 3100 1900 0    40   ~ 0
ITIMER
$EndSCHEMATC
