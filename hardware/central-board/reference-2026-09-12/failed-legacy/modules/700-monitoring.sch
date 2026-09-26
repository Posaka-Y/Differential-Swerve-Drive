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
Sheet 6 7
Title "700 Battery and Motor Power Monitoring"
Date "2026-08-04"
Rev "A - HUMAN REVIEW DRAFT"
Comp "Differential Swerve"
Comment1 "Responsibility-based hierarchical schematic"
Comment2 "Global labels connect modules"
$EndDescr
Text Label 1100 1250 0    40   ~ 0
CONTACTOR_GATE
Text Label 1100 1350 0    40   ~ 0
GND_24V
Text Label 1100 1450 0    40   ~ 0
CONTACTOR_COIL_N
Text Notes 700 650 0    80   ~ 12
700 BATTERY MONITOR (EXTERNAL KELVIN SHUNT)
$Comp
L Connector_Generic:Conn_01x02 J701
U 1 1 105E
P 900 1050
F 0 "J701" H 800 1270 50  0000 C CNN
F 1 "SHUNT KELVIN INPUT" H 800 1180 50  0000 C CNN
F 2 "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal" H 900 1050 50  0001 C CNN
	1    900 1050
	-1 0 0 1
$EndComp
Wire Wire Line
	1000 1050 1700 1050
Text Label 1700 1050 0    40   ~ 0
SHUNT_BAT
Wire Wire Line
	1000 1150 1700 1150
Text Label 1700 1150 0    40   ~ 0
SHUNT_LOAD
$Comp
L Connector_Generic:Conn_01x10 U701
U 1 1 105F
P 1900 950
F 0 "U701" H 1800 1170 50  0000 C CNN
F 1 "INA238AIDGSR" H 1800 1080 50  0000 C CNN
F 2 "Package_SO:VSSOP-10_3x3mm_P0.5mm" H 1900 950 50  0001 C CNN
	1    1900 950
	-1 0 0 1
$EndComp
Wire Wire Line
	2000 950 2750 950
Text Label 2750 950 0    40   ~ 0
GND_CTRL
Wire Wire Line
	2000 1050 2750 1050
Text Label 2750 1050 0    40   ~ 0
GND_CTRL
Wire Wire Line
	2000 1150 2750 1150
Text Label 2750 1150 0    40   ~ 0
BAT_MON_ALERT_N
Wire Wire Line
	2000 1250 2750 1250
Text Label 2750 1250 0    40   ~ 0
I2C0_SDA
Wire Wire Line
	2000 1350 2750 1350
Text Label 2750 1350 0    40   ~ 0
I2C0_SCL
Wire Wire Line
	2000 1450 2750 1450
Text Label 2750 1450 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	2000 1550 2750 1550
Text Label 2750 1550 0    40   ~ 0
GND_CTRL
Wire Wire Line
	2000 1650 2750 1650
Text Label 2750 1650 0    40   ~ 0
BAT_VBUS
Wire Wire Line
	2000 1750 2750 1750
Text Label 2750 1750 0    40   ~ 0
SHUNT_LOAD
Wire Wire Line
	2000 1850 2750 1850
Text Label 2750 1850 0    40   ~ 0
SHUNT_BAT
Text Notes 1800 2100 0    40   ~ 12
U701 pin order 1..10: A1,A0,ALERT,SDA,SCL,VS,GND,VBUS,IN-,IN+.
$Comp
L Device:R R701
U 1 1 1060
P 3050 1300
F 0 "R701" H 2950 1520 50  0000 C CNN
F 1 "1k" H 2950 1430 50  0000 C CNN
F 2 "" H 3050 1300 50  0001 C CNN
	1    3050 1300
	0 -1 -1 0
$EndComp
Wire Wire Line
	2950 1300 2700 1300
Text Label 2700 1300 0    40   ~ 0
SHUNT_LOAD
Wire Wire Line
	3150 1300 3400 1300
Text Label 3400 1300 0    40   ~ 0
BAT_VBUS
$Comp
L Device:C C701
U 1 1 1061
P 3050 1550
F 0 "C701" H 2950 1770 50  0000 C CNN
F 1 "100n" H 2950 1680 50  0000 C CNN
F 2 "" H 3050 1550 50  0001 C CNN
	1    3050 1550
	0 -1 -1 0
$EndComp
Wire Wire Line
	2950 1550 2700 1550
Text Label 2700 1550 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	3150 1550 3400 1550
Text Label 3400 1550 0    40   ~ 0
GND_CTRL
$Comp
L Device:R R702
U 1 1 1062
P 3050 1800
F 0 "R702" H 2950 2020 50  0000 C CNN
F 1 "10k" H 2950 1930 50  0000 C CNN
F 2 "" H 3050 1800 50  0001 C CNN
	1    3050 1800
	0 -1 -1 0
$EndComp
Wire Wire Line
	2950 1800 2700 1800
Text Label 2700 1800 0    40   ~ 0
BAT_MON_ALERT_N
Wire Wire Line
	3150 1800 3400 1800
Text Label 3400 1800 0    40   ~ 0
+3V3_TEENSY
Text Notes 700 2400 0    45   ~ 12
MANDATORY: fusible resistors/small fuses at the battery-side origins of BOTH Kelvin sense wires; board-side resistors cannot protect the harness.
Text Notes 700 2520 0    45   ~ 12
100A/75mV shunt dissipates 5.17W at 83A. Confirm continuous/peak current and thermal mounting before purchase.
$EndSCHEMATC
