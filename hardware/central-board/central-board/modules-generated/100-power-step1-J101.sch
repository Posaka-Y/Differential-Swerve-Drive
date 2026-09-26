EESchema Schematic File Version 4
LIBS:Connector_Generic
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "Step1: J101 XT30 5V Input"
Date "2026-09-14"
Rev "A - DRAFT"
Comp "Differential Swerve"
$EndDescr
$Comp
L Connector_Generic:Conn_01x02 J101
U 1 1 5F000001
P 900 1100
F 0 "J101" H 800 1320 50  0000 C CNN
F 1 "XT30PW-M 5V INPUT" H 800 1230 50  0000 C CNN
F 2 "Connector_AMASS:AMASS_XT30PW-M_1x02_P5.00mm_Horizontal" H 900 1100 50  0001 C CNN
	1    900 1100
	-1   0    0    1
$EndComp
Wire Wire Line
	1100 1100 1400 1100
Text Label 1400 1100 0    40   ~ 0
+5V_RAW
Wire Wire Line
	1100 1200 1400 1200
Text Label 1400 1200 0    40   ~ 0
GND_CTRL
$EndSCHEMATC
