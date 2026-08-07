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
Sheet 7 7
Title "800 Expansion and Test Access"
Date "2026-08-04"
Rev "A - HUMAN REVIEW DRAFT"
Comp "Differential Swerve"
Comment1 "Responsibility-based hierarchical schematic"
Comment2 "Global labels connect modules"
$EndDescr
Text Notes 800 650 0    80   ~ 12
800 EXPANSION / 900 TEST ACCESS
$Comp
L Connector_Generic:Conn_01x04 J801
U 1 1 105F
P 900 1000
F 0 "J801" H 800 1220 50  0000 C CNN
F 1 "I2C0 GH4" H 800 1130 50  0000 C CNN
F 2 "Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal" H 900 1000 50  0001 C CNN
	1    900 1000
	-1 0 0 1
$EndComp
Wire Wire Line
	1100 1000 1700 1000
Text Label 1700 1000 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	1100 1100 1700 1100
Text Label 1700 1100 0    40   ~ 0
GND_CTRL
Wire Wire Line
	1100 1200 1700 1200
Text Label 1700 1200 0    40   ~ 0
I2C0_SDA
Wire Wire Line
	1100 1300 1700 1300
Text Label 1700 1300 0    40   ~ 0
I2C0_SCL
$Comp
L Connector_Generic:Conn_01x04 J802
U 1 1 1060
P 900 1550
F 0 "J802" H 800 1770 50  0000 C CNN
F 1 "I2C1 GH4" H 800 1680 50  0000 C CNN
F 2 "Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal" H 900 1550 50  0001 C CNN
	1    900 1550
	-1 0 0 1
$EndComp
Wire Wire Line
	1100 1550 1700 1550
Text Label 1700 1550 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	1100 1650 1700 1650
Text Label 1700 1650 0    40   ~ 0
GND_CTRL
Wire Wire Line
	1100 1750 1700 1750
Text Label 1700 1750 0    40   ~ 0
I2C1_SDA
Wire Wire Line
	1100 1850 1700 1850
Text Label 1700 1850 0    40   ~ 0
I2C1_SCL
$Comp
L Device:R R801
U 1 1 1061
P 2300 1050
F 0 "R801" H 2200 1270 50  0000 C CNN
F 1 "2.2k DNP" H 2200 1180 50  0000 C CNN
F 2 "" H 2300 1050 50  0001 C CNN
	1    2300 1050
	0 -1 -1 0
$EndComp
Wire Wire Line
	2200 1050 1950 1050
Text Label 1950 1050 0    40   ~ 0
I2C0_SDA
Wire Wire Line
	2400 1050 2650 1050
Text Label 2650 1050 0    40   ~ 0
+3V3_TEENSY
$Comp
L Device:R R802
U 1 1 1062
P 2300 1250
F 0 "R802" H 2200 1470 50  0000 C CNN
F 1 "2.2k DNP" H 2200 1380 50  0000 C CNN
F 2 "" H 2300 1250 50  0001 C CNN
	1    2300 1250
	0 -1 -1 0
$EndComp
Wire Wire Line
	2200 1250 1950 1250
Text Label 1950 1250 0    40   ~ 0
I2C0_SCL
Wire Wire Line
	2400 1250 2650 1250
Text Label 2650 1250 0    40   ~ 0
+3V3_TEENSY
$Comp
L Device:R R803
U 1 1 1063
P 2300 1600
F 0 "R803" H 2200 1820 50  0000 C CNN
F 1 "2.2k DNP" H 2200 1730 50  0000 C CNN
F 2 "" H 2300 1600 50  0001 C CNN
	1    2300 1600
	0 -1 -1 0
$EndComp
Wire Wire Line
	2200 1600 1950 1600
Text Label 1950 1600 0    40   ~ 0
I2C1_SDA
Wire Wire Line
	2400 1600 2650 1600
Text Label 2650 1600 0    40   ~ 0
+3V3_TEENSY
$Comp
L Device:R R804
U 1 1 1064
P 2300 1800
F 0 "R804" H 2200 2020 50  0000 C CNN
F 1 "2.2k DNP" H 2200 1930 50  0000 C CNN
F 2 "" H 2300 1800 50  0001 C CNN
	1    2300 1800
	0 -1 -1 0
$EndComp
Wire Wire Line
	2200 1800 1950 1800
Text Label 1950 1800 0    40   ~ 0
I2C1_SCL
Wire Wire Line
	2400 1800 2650 1800
Text Label 2650 1800 0    40   ~ 0
+3V3_TEENSY
$Comp
L Connector_Generic:Conn_01x03 J811
U 1 1 1065
P 900 2200
F 0 "J811" H 800 2420 50  0000 C CNN
F 1 "UART7 GH3" H 800 2330 50  0000 C CNN
F 2 "Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal" H 900 2200 50  0001 C CNN
	1    900 2200
	-1 0 0 1
$EndComp
Wire Wire Line
	1100 2200 1700 2200
Text Label 1700 2200 0    40   ~ 0
UART7_TX
Wire Wire Line
	1100 2300 1700 2300
Text Label 1700 2300 0    40   ~ 0
UART7_RX
Wire Wire Line
	1100 2400 1700 2400
Text Label 1700 2400 0    40   ~ 0
GND_CTRL
$Comp
L Connector_Generic:Conn_01x03 J812
U 1 1 1066
P 900 2650
F 0 "J812" H 800 2870 50  0000 C CNN
F 1 "UART8 GH3" H 800 2780 50  0000 C CNN
F 2 "Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal" H 900 2650 50  0001 C CNN
	1    900 2650
	-1 0 0 1
$EndComp
Wire Wire Line
	1100 2650 1700 2650
Text Label 1700 2650 0    40   ~ 0
UART8_TX
Wire Wire Line
	1100 2750 1700 2750
Text Label 1700 2750 0    40   ~ 0
UART8_RX
Wire Wire Line
	1100 2850 1700 2850
Text Label 1700 2850 0    40   ~ 0
GND_CTRL
$Comp
L Connector_Generic:Conn_01x07 J821
U 1 1 1067
P 900 3100
F 0 "J821" H 800 3320 50  0000 C CNN
F 1 "SPI GH7" H 800 3230 50  0000 C CNN
F 2 "Connector_JST:JST_GH_SM07B-GHS-TB_1x07-1MP_P1.25mm_Horizontal" H 900 3100 50  0001 C CNN
	1    900 3100
	-1 0 0 1
$EndComp
Wire Wire Line
	1100 3100 1700 3100
Text Label 1700 3100 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	1100 3200 1700 3200
Text Label 1700 3200 0    40   ~ 0
GND_CTRL
Wire Wire Line
	1100 3300 1700 3300
Text Label 1700 3300 0    40   ~ 0
SPI_SCK
Wire Wire Line
	1100 3400 1700 3400
Text Label 1700 3400 0    40   ~ 0
SPI_MOSI
Wire Wire Line
	1100 3500 1700 3500
Text Label 1700 3500 0    40   ~ 0
SPI_MISO
Wire Wire Line
	1100 3600 1700 3600
Text Label 1700 3600 0    40   ~ 0
SPI_CS0_N
Wire Wire Line
	1100 3700 1700 3700
Text Label 1700 3700 0    40   ~ 0
SPI_CS1_N
$Comp
L Connector_Generic:Conn_01x10 J831
U 1 1 1068
P 3400 1000
F 0 "J831" H 3300 1220 50  0000 C CNN
F 1 "GPIO/ADC GH10 - 3V3 ONLY" H 3300 1130 50  0000 C CNN
F 2 "Connector_JST:JST_GH_SM10B-GHS-TB_1x10-1MP_P1.25mm_Horizontal" H 3400 1000 50  0001 C CNN
	1    3400 1000
	-1 0 0 1
$EndComp
Wire Wire Line
	3600 1000 4300 1000
Text Label 4300 1000 0    40   ~ 0
GND_CTRL
Wire Wire Line
	3600 1100 4300 1100
Text Label 4300 1100 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	3600 1200 4300 1200
Text Label 4300 1200 0    40   ~ 0
IO20_A6
Wire Wire Line
	3600 1300 4300 1300
Text Label 4300 1300 0    40   ~ 0
IO21_A7
Wire Wire Line
	3600 1400 4300 1400
Text Label 4300 1400 0    40   ~ 0
IO24_A10
Wire Wire Line
	3600 1500 4300 1500
Text Label 4300 1500 0    40   ~ 0
IO25_A11
Wire Wire Line
	3600 1600 4300 1600
Text Label 4300 1600 0    40   ~ 0
IO26_A12
Wire Wire Line
	3600 1700 4300 1700
Text Label 4300 1700 0    40   ~ 0
IO27_A13
Wire Wire Line
	3600 1800 4300 1800
Text Label 4300 1800 0    40   ~ 0
IO40_A16
Wire Wire Line
	3600 1900 4300 1900
Text Label 4300 1900 0    40   ~ 0
IO41_A17
Text Notes 3300 2150 0    45   ~ 12
Add 100R series resistor in each of the eight GPIO lines near Teensy.
$Comp
L Connector_Generic:Conn_01x03 J841
U 1 1 1069
P 3400 2500
F 0 "J841" H 3300 2720 50  0000 C CNN
F 1 "AUX DRIVER ENABLE" H 3300 2630 50  0000 C CNN
F 2 "Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal" H 3400 2500 50  0001 C CNN
	1    3400 2500
	-1 0 0 1
$EndComp
Wire Wire Line
	3600 2500 4300 2500
Text Label 4300 2500 0    40   ~ 0
AUX_OUTPUT_EN
Wire Wire Line
	3600 2600 4300 2600
Text Label 4300 2600 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	3600 2700 4300 2700
Text Label 4300 2700 0    40   ~ 0
GND_CTRL
$Comp
L Connector_Generic:Conn_01x02 J842
U 1 1 106A
P 3400 2950
F 0 "J842" H 3300 3170 50  0000 C CNN
F 1 "EXTERNAL REARM SW" H 3300 3080 50  0000 C CNN
F 2 "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal" H 3400 2950 50  0001 C CNN
	1    3400 2950
	-1 0 0 1
$EndComp
Wire Wire Line
	3600 2950 4300 2950
Text Label 4300 2950 0    40   ~ 0
REARM_SW_N
Wire Wire Line
	3600 3050 4300 3050
Text Label 4300 3050 0    40   ~ 0
GND_CTRL
$Comp
L Connector_Generic:Conn_01x06 J851
U 1 1 106B
P 3400 3350
F 0 "J851" H 3300 3570 50  0000 C CNN
F 1 "5V EXPANSION POWER" H 3300 3480 50  0000 C CNN
F 2 "Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal" H 3400 3350 50  0001 C CNN
	1    3400 3350
	-1 0 0 1
$EndComp
Wire Wire Line
	3600 3350 4300 3350
Text Label 4300 3350 0    40   ~ 0
+5V_EXP
Wire Wire Line
	3600 3450 4300 3450
Text Label 4300 3450 0    40   ~ 0
GND_CTRL
Wire Wire Line
	3600 3550 4300 3550
Text Label 4300 3550 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	3600 3650 4300 3650
Text Label 4300 3650 0    40   ~ 0
GND_CTRL
Wire Wire Line
	3600 3750 4300 3750
Text Label 4300 3750 0    40   ~ 0
NC
Wire Wire Line
	3600 3850 4300 3850
Text Label 4300 3850 0    40   ~ 0
NC
$Comp
L Connector_Generic:Conn_01x08 J901
U 1 1 106C
P 5700 1000
F 0 "J901" H 5600 1220 50  0000 C CNN
F 1 "TEST POINT HEADER" H 5600 1130 50  0000 C CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical" H 5700 1000 50  0001 C CNN
	1    5700 1000
	-1 0 0 1
$EndComp
Wire Wire Line
	5900 1000 6550 1000
Text Label 6550 1000 0    40   ~ 0
GND_CTRL
Wire Wire Line
	5900 1100 6550 1100
Text Label 6550 1100 0    40   ~ 0
+5V_SYS
Wire Wire Line
	5900 1200 6550 1200
Text Label 6550 1200 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	5900 1300 6550 1300
Text Label 6550 1300 0    40   ~ 0
TP_GPIO33
Wire Wire Line
	5900 1400 6550 1400
Text Label 6550 1400 0    40   ~ 0
TP_GPIO37
Wire Wire Line
	5900 1500 6550 1500
Text Label 6550 1500 0    40   ~ 0
TP_GPIO38
Wire Wire Line
	5900 1600 6550 1600
Text Label 6550 1600 0    40   ~ 0
TP_GPIO39
Wire Wire Line
	5900 1700 6550 1700
Text Label 6550 1700 0    40   ~ 0
PWR_5V_FAULT_N
Text Notes 800 4300 0    60   ~ 12
REVIEW GATES BEFORE PCB:
Text Notes 800 4450 0    45   ~ 12
1) close all TBD ratings/values; 2) confirm rearm location; 3) check eFuse thresholds worst-case;
Text Notes 800 4570 0    45   ~ 12
4) verify E-stop coil release waveform; 5) confirm source-end shunt fuses; 6) ERC pin-type cleanup after symbol finalization.
Text Notes 800 4800 0    45   ~ 12
Teensy underside keepout, USB/microSD/Program access and 11mm-class stacking clearance are PCB constraints.
Text Notes 800 5050 0    45   ~ 12
Net naming: COMM_A/B are harness abstraction; CANH/CANL are physical transceiver nets.
Text Notes 800 5300 0    50   ~ 12
THIS IS A REVIEW DRAFT. Generic pin-explicit symbols are intentional where final custom library symbols are not yet frozen.
$EndSCHEMATC
