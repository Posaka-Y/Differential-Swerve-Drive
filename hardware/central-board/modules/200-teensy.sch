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
Sheet 3 7
Title "200 Teensy 4.1 Carrier and Safety GPIO"
Date "2026-08-04"
Rev "A - HUMAN REVIEW DRAFT"
Comp "Differential Swerve"
Comment1 "Responsibility-based hierarchical schematic"
Comment2 "Global labels connect modules"
$EndDescr
Text Notes 650 700 0    80   ~ 12
200 TEENSY 4.1 SOCKETS (TOP-VIEW PIN MAP)
$Comp
L Connector_Generic:Conn_01x24 J201
U 1 1 1017
P 800 1050
F 0 "J201" H 700 1270 50  0000 C CNN
F 1 "TEENSY LEFT / 68000-224HLF + SOCKET" H 700 1180 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_1x24_P2.54mm_Vertical" H 800 1050 50  0001 C CNN
	1    800 1050
	-1 0 0 1
$EndComp
Wire Wire Line
	1000 1050 1850 1050
Text Label 1850 1050 0    40   ~ 0
GND_CTRL
Wire Wire Line
	1000 1150 1850 1150
Text Label 1850 1150 0    40   ~ 0
CAN2_RX
Wire Wire Line
	1000 1250 1850 1250
Text Label 1850 1250 0    40   ~ 0
CAN2_TX
Wire Wire Line
	1000 1350 1850 1350
Text Label 1850 1350 0    40   ~ 0
MOTOR_PWR_EN
Wire Wire Line
	1000 1450 1850 1450
Text Label 1850 1450 0    40   ~ 0
ESTOP_LOOP_OK_N
Wire Wire Line
	1000 1550 1850 1550
Text Label 1850 1550 0    40   ~ 0
ESTOP1_AUX_OK_N
Wire Wire Line
	1000 1650 1850 1650
Text Label 1850 1650 0    40   ~ 0
ESTOP2_AUX_OK_N
Wire Wire Line
	1000 1750 1850 1750
Text Label 1850 1750 0    40   ~ 0
REARM_SW_N
Wire Wire Line
	1000 1850 1850 1850
Text Label 1850 1850 0    40   ~ 0
STATUS_G_LED
Wire Wire Line
	1000 1950 1850 1950
Text Label 1850 1950 0    40   ~ 0
STATUS_R_LED
Wire Wire Line
	1000 2050 1850 2050
Text Label 1850 2050 0    40   ~ 0
AUX_OUTPUT_EN
Wire Wire Line
	1000 2150 1850 2150
Text Label 1850 2150 0    40   ~ 0
SPI_CS0_N
Wire Wire Line
	1000 2250 1850 2250
Text Label 1850 2250 0    40   ~ 0
SPI_MOSI
Wire Wire Line
	1000 2350 1850 2350
Text Label 1850 2350 0    40   ~ 0
SPI_MISO
Wire Wire Line
	1000 2450 1850 2450
Text Label 1850 2450 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	1000 2550 1850 2550
Text Label 1850 2550 0    40   ~ 0
IO24_A10
Wire Wire Line
	1000 2650 1850 2650
Text Label 1850 2650 0    40   ~ 0
IO25_A11
Wire Wire Line
	1000 2750 1850 2750
Text Label 1850 2750 0    40   ~ 0
IO26_A12
Wire Wire Line
	1000 2850 1850 2850
Text Label 1850 2850 0    40   ~ 0
IO27_A13
Wire Wire Line
	1000 2950 1850 2950
Text Label 1850 2950 0    40   ~ 0
UART7_RX
Wire Wire Line
	1000 3050 1850 3050
Text Label 1850 3050 0    40   ~ 0
UART7_TX
Wire Wire Line
	1000 3150 1850 3150
Text Label 1850 3150 0    40   ~ 0
CAN3_RX
Wire Wire Line
	1000 3250 1850 3250
Text Label 1850 3250 0    40   ~ 0
CAN3_TX
Wire Wire Line
	1000 3350 1850 3350
Text Label 1850 3350 0    40   ~ 0
PWR_5V_FAULT_N
$Comp
L Connector_Generic:Conn_01x24 J202
U 1 1 1018
P 2150 1050
F 0 "J202" H 2050 1270 50  0000 C CNN
F 1 "TEENSY RIGHT / 68000-224HLF + SOCKET" H 2050 1180 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_1x24_P2.54mm_Vertical" H 2150 1050 50  0001 C CNN
	1    2150 1050
	-1 0 0 1
$EndComp
Wire Wire Line
	2350 1050 3200 1050
Text Label 3200 1050 0    40   ~ 0
TP_GPIO33
Wire Wire Line
	2350 1150 3200 1150
Text Label 3200 1150 0    40   ~ 0
UART8_RX
Wire Wire Line
	2350 1250 3200 1250
Text Label 3200 1250 0    40   ~ 0
UART8_TX
Wire Wire Line
	2350 1350 3200 1350
Text Label 3200 1350 0    40   ~ 0
SPI_CS1_N
Wire Wire Line
	2350 1450 3200 1450
Text Label 3200 1450 0    40   ~ 0
TP_GPIO37
Wire Wire Line
	2350 1550 3200 1550
Text Label 3200 1550 0    40   ~ 0
TP_GPIO38
Wire Wire Line
	2350 1650 3200 1650
Text Label 3200 1650 0    40   ~ 0
TP_GPIO39
Wire Wire Line
	2350 1750 3200 1750
Text Label 3200 1750 0    40   ~ 0
IO40_A16
Wire Wire Line
	2350 1850 3200 1850
Text Label 3200 1850 0    40   ~ 0
IO41_A17
Wire Wire Line
	2350 1950 3200 1950
Text Label 3200 1950 0    40   ~ 0
GND_CTRL
Wire Wire Line
	2350 2050 3200 2050
Text Label 3200 2050 0    40   ~ 0
SPI_SCK
Wire Wire Line
	2350 2150 3200 2150
Text Label 3200 2150 0    40   ~ 0
MOTOR_PWR_SENSE
Wire Wire Line
	2350 2250 3200 2250
Text Label 3200 2250 0    40   ~ 0
BAT_MON_ALERT_N
Wire Wire Line
	2350 2350 3200 2350
Text Label 3200 2350 0    40   ~ 0
I2C1_SCL
Wire Wire Line
	2350 2450 3200 2450
Text Label 3200 2450 0    40   ~ 0
I2C1_SDA
Wire Wire Line
	2350 2550 3200 2550
Text Label 3200 2550 0    40   ~ 0
I2C0_SDA
Wire Wire Line
	2350 2650 3200 2650
Text Label 3200 2650 0    40   ~ 0
I2C0_SCL
Wire Wire Line
	2350 2750 3200 2750
Text Label 3200 2750 0    40   ~ 0
IO20_A6
Wire Wire Line
	2350 2850 3200 2850
Text Label 3200 2850 0    40   ~ 0
IO21_A7
Wire Wire Line
	2350 2950 3200 2950
Text Label 3200 2950 0    40   ~ 0
CAN1_TX
Wire Wire Line
	2350 3050 3200 3050
Text Label 3200 3050 0    40   ~ 0
CAN1_RX
Wire Wire Line
	2350 3150 3200 3150
Text Label 3200 3150 0    40   ~ 0
+3V3_TEENSY
Wire Wire Line
	2350 3250 3200 3250
Text Label 3200 3250 0    40   ~ 0
GND_CTRL
Wire Wire Line
	2350 3350 3200 3350
Text Label 3200 3350 0    40   ~ 0
+5V_TEENSY
Text Notes 650 3600 0    45   ~ 12
J201 socket pads 1..24 = Teensy GND,0..12,3V3,24..32.
Text Notes 650 3700 0    45   ~ 12
J202 socket pads 25..48 = Teensy 33..41,GND,13..23,3V3,GND,VIN.
Text Notes 650 3800 0    50   ~ 12
MECHANICAL: two 1x24 sockets, 17.78mm row spacing; keep entire underside free of parts/exposed pads.
Text Notes 650 3910 0    50   ~ 12
ASSEMBLY: cut Teensy VUSB-VIN link before simultaneous external 5V and USB connection.
$Comp
L Device:R R201
U 1 1 1019
P 1300 4200
F 0 "R201" H 1200 4420 50  0000 C CNN
F 1 "47k" H 1200 4330 50  0000 C CNN
F 2 "" H 1300 4200 50  0001 C CNN
	1    1300 4200
	0 -1 -1 0
$EndComp
Wire Wire Line
	1200 4200 950 4200
Text Label 950 4200 0    40   ~ 0
MOTOR_PWR_EN
Wire Wire Line
	1400 4200 1650 4200
Text Label 1650 4200 0    40   ~ 0
GND_CTRL
$Comp
L Device:R R202
U 1 1 101A
P 1300 4400
F 0 "R202" H 1200 4620 50  0000 C CNN
F 1 "47k" H 1200 4530 50  0000 C CNN
F 2 "" H 1300 4400 50  0001 C CNN
	1    1300 4400
	0 -1 -1 0
$EndComp
Wire Wire Line
	1200 4400 950 4400
Text Label 950 4400 0    40   ~ 0
AUX_OUTPUT_EN
Wire Wire Line
	1400 4400 1650 4400
Text Label 1650 4400 0    40   ~ 0
GND_CTRL
$Comp
L Device:R R203
U 1 1 101B
P 2600 4200
F 0 "R203" H 2500 4420 50  0000 C CNN
F 1 "10k" H 2500 4330 50  0000 C CNN
F 2 "" H 2600 4200 50  0001 C CNN
	1    2600 4200
	0 -1 -1 0
$EndComp
Wire Wire Line
	2500 4200 2250 4200
Text Label 2250 4200 0    40   ~ 0
REARM_SW_N
Wire Wire Line
	2700 4200 2950 4200
Text Label 2950 4200 0    40   ~ 0
+3V3_TEENSY
$Comp
L Switch:SW_Push SW201
U 1 1 101C
P 2600 4500
F 0 "SW201" H 2500 4720 50  0000 C CNN
F 1 "REARM (BOARD LOCAL OPTION)" H 2500 4630 50  0000 C CNN
F 2 "Button_Switch_THT:SW_PUSH_6mm" H 2600 4500 50  0001 C CNN
	1    2600 4500
	0 -1 -1 0
$EndComp
Wire Wire Line
	2500 4500 2250 4500
Text Label 2250 4500 0    40   ~ 0
REARM_SW_N
Wire Wire Line
	2700 4500 2950 4500
Text Label 2720 4500 0    40   ~ 0
GND_CTRL
Text Notes 650 4700 0    45   ~ 12
REARM location is open: populate SW201 only if board-local operation is accepted; otherwise use panel connector.
$EndSCHEMATC
