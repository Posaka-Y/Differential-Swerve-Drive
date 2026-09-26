"""Generate reviewable native KiCad 10 sheets for the non-CAN central-board blocks.

The symbols are deliberately embedded in each sheet: opening a sheet does not
depend on a user library table.  Pin numbers are the package pin numbers; a
``REVIEW`` value means the electrical value/package choice is intentionally not
released for purchase.
"""
from pathlib import Path
from uuid import uuid4

OUT = Path(__file__).parent

def u(): return str(uuid4())
def q(s): return str(s).replace('"', "'")

def effects(size=1.27):
    return f'(effects (font (size {size} {size})))'

def prop(name, value, x, y, hide=False):
    # KiCad's property parser is order-sensitive: ``hide`` follows the
    # placement/autoplace flags (rather than the ``at`` clause).
    h = ' (hide yes)' if hide else ''
    return f'(property "{q(name)}" "{q(value)}" (at {x} {y} 0) (show_name no) (do_not_autoplace no){h} {effects()})'

def libsym(name, pins):
    # pin tuple: number, visible pin name, side (L/R), y, electrical type
    body=[]
    for num,pn,side,y,etype in pins:
        x,rot = (-10,0) if side=='L' else (10,180)
        body.append(f'(pin {etype} line (at {x} {y} {rot}) (length 3) (name "{q(pn)}" {effects(1.0)}) (number "{num}" {effects(1.0)}))')
    return f'''(symbol "Central:{q(name)}"
  (pin_names (offset 1.0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
  {prop('Reference', name[0] if name else 'U', 0, 8)} {prop('Value', name, 0, -8)}
  {prop('Footprint','',0,0,True)} {prop('Datasheet','',0,0,True)} {prop('Description','Embedded reference symbol',0,0,True)}
  (symbol "{q(name)}_0_1" (rectangle (start -7 7) (end 7 -7) (stroke (width 0.3) (type default)) (fill (type background))))
  (symbol "{q(name)}_1_1" {' '.join(body)}) (embedded_fonts no))'''

def instance(name, ref, value, x, y, pins, footprint=''):
    uid=u(); ps=' '.join(f'(pin "{n}" (uuid "{u()}"))' for n,*_ in pins)
    return f'''(symbol (lib_id "Central:{q(name)}") (at {x} {y} 0) (unit 1) (body_style 1)
 (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no) (uuid "{uid}")
 {prop('Reference',ref,x,y-9)} {prop('Value',value,x,y+9)} {prop('Footprint',footprint,x,y,True)} {prop('Datasheet','',x,y,True)} {prop('Description','Embedded reference symbol',x,y,True)}
 {ps} (instances (project "central-board-reference" (path "/{uid}" (reference "{ref}") (unit 1)))) )'''

def label(net,x,y):
    # Global labels require an explicit text justification in KiCad 10.
    return f'(global_label "{q(net)}" (shape bidirectional) (at {x} {y} 0) (effects (font (size 1.05 1.05)) (justify left bottom)) (uuid "{u()}"))'

def note(text,x,y,size=1.3):
    return f'(text "{q(text)}" (exclude_from_sim no) (at {x} {y} 0) {effects(size)} (uuid "{u()}"))'

def connect_labels(x,y,pins,nets):
    out=[]
    for pin,net in zip(pins,nets):
        num,pn,side,dy,*_ = pin
        px=x-10 if side=='L' else x+10
        out += [f'(wire (pts (xy {px} {y+dy}) (xy {px + (-5 if side=="L" else 5)} {y+dy})) (stroke (width 0) (type default)) (uuid "{u()}"))', label(net,px + (-5 if side=='L' else 5),y+dy)]
    return out

def sheet(fn,title,comment,parts,notes):
    # A KiCad lib_symbols block may contain each lib_id only once even when a
    # component is instantiated many times.
    unique={}
    for n,_,_,_,_,p,_,_ in parts:
        unique.setdefault(n,p)
    libs='\n'.join(libsym(n,p) for n,p in unique.items())
    objs=[]
    for n,ref,val,x,y,pins,nets,fp in parts:
        objs.append(instance(n,ref,val,x,y,pins,fp)); objs.extend(connect_labels(x,y,pins,nets))
    text='\n'.join(note(*a) for a in notes)
    data=f'''(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") (uuid "{u()}")
 (paper "A4")
 (title_block (title "{q(title)}") (date "2026-09-12") (rev "A - REFERENCE / NOT FOR MANUFACTURE") (company "Differential Swerve") (comment 1 "{q(comment)}"))
 (lib_symbols {libs})
 {text}\n{' '.join(objs)}
 (sheet_instances (path "/" (page "1"))) )\n'''
    (OUT/fn).write_text(data,encoding='utf-8')

# Generic symbols are physical connectivity representations, not placeholders:
# their pins are package/connector positions and attach to named global nets.
P2=[('1','1','L',2,'passive'),('2','2','L',-2,'passive')]
P3=[('1','1','L',4,'passive'),('2','2','L',0,'passive'),('3','3','L',-4,'passive')]
P4=[('1','1','L',5,'passive'),('2','2','L',1.7,'passive'),('3','3','L',-1.7,'passive'),('4','4','L',-5,'passive')]
P6=[(str(i),str(i),'L',7-(i-1)*2.8,'passive') for i in range(1,7)]
R=[('1','1','L',0,'passive'),('2','2','R',0,'passive')]

TPS=[('1','IN','L',5,'power_in'),('2','EN/UVLO','L',2.5,'input'),('3','ILIM','L',0,'input'),('4','dVdT','L',-2.5,'input'),('5','GND','L',-5,'power_in'),('6','FLT_N','R',5,'open_collector'),('7','PGTH','R',2.5,'input'),('8','OVLO','R',0,'input'),('9','OUT','R',-2.5,'power_out'),('10','OUT','R',-5,'power_out')]
parts=[
 ('XT30PW-M','J101','AMASS XT30PW-M',35,45,P2,['+5V_IN','GND_CTRL'],'Connector:AMASS_XT30PW-M'),
 ('TPS259470LRPWR','U101','TPS259470LRPWR',90,45,TPS,['+5V_IN','UVLO_4V43','RILM','DV_DT','GND_CTRL','PWR_5V_FAULT_N','PGTH_REVIEW','OVLO_5V46','+5V_SYS','+5V_SYS'],'Package_DFQFN:Texas_RPW0010A'),
 ('Resistor','R101','750R 1% (ILIM)',55,70,R,['RILM','GND_CTRL'],'Resistor_SMD:R_0603_1608Metric'),
 ('Capacitor','C101','10nF dV/dt',90,72,P2,['DV_DT','GND_CTRL'],'Capacitor_SMD:C_0603_1608Metric'),
 ('Resistor','R102','732k 1% UV/OV high',45,85,R,['+5V_IN','UVLO_4V43'],''),
 ('Resistor','R103','51.1k 1% UV/OV mid',75,85,R,['UVLO_4V43','OVLO_5V46'],''),
 ('Resistor','R104','221k 1% UV/OV low',105,85,R,['OVLO_5V46','GND_CTRL'],''),
 ('Resistor','R105','10k FLT pullup',65,95,R,['PWR_5V_FAULT_N','+3V3_TEENSY'],''),
 ('Capacitor','C102','1uF input bypass',45,105,P2,['+5V_IN','GND_CTRL'],''),
 ('Capacitor','C103','1uF output bypass',75,105,P2,['+5V_SYS','GND_CTRL'],''),
 ('Capacitor','C104','100uF 10V input bulk',105,105,P2,['+5V_IN','GND_CTRL'],''),
 ('Capacitor','C105','470uF 10V star bulk',135,105,P2,['+5V_SYS','GND_CTRL'],''),
 ('PPTC','F101','1206L075/16YR Teensy',130,30,R,['+5V_SYS','+5V_TEENSY_RAW'],'Fuse:Fuse_1206_3216Metric'),
 ('Schottky','D101','PMEG2010EA,115 20V 1A',160,30,R,['+5V_TEENSY_RAW','VIN_TEENSY'],'Diode_SMD:D_SOD-323'),
 ('Schottky','D102','PMEG2010EA,115 20V 1A',160,45,R,['TEENSY_VUSB_PAD','VIN_TEENSY'],'Diode_SMD:D_SOD-323'),
 ('PPTC','F102','1206L050/15YR Expansion',155,45,R,['+5V_SYS','+5V_EXP'],'Fuse:Fuse_1206_3216Metric'),
 ('PPTC','F103','1206L050/15YR Unit1',155,60,R,['+5V_SYS','+5V_UNIT1'],'Fuse:Fuse_1206_3216Metric'),
 ('PPTC','F104','1206L050/15YR Unit2',155,72,R,['+5V_SYS','+5V_UNIT2'],'Fuse:Fuse_1206_3216Metric'),
 ('PPTC','F105','1206L050/15YR Unit3',155,84,R,['+5V_SYS','+5V_UNIT3'],'Fuse:Fuse_1206_3216Metric'),
 ('PPTC','F106','1206L050/15YR ODOM',155,96,R,['+5V_SYS','+5V_ODOM'],'Fuse:Fuse_1206_3216Metric'),
 ('GH2','J102','SM02B-GHS-TB Unit1',190,60,P2,['+5V_UNIT1','GND_CTRL'],'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'),
 ('GH2','J103','SM02B-GHS-TB Unit2',190,72,P2,['+5V_UNIT2','GND_CTRL'],''),
 ('GH2','J104','SM02B-GHS-TB Unit3',190,84,P2,['+5V_UNIT3','GND_CTRL'],''),
 ('GH2','J105','SM02B-GHS-TB ODOM',190,96,P2,['+5V_ODOM','GND_CTRL'],'')]
notes=[('A / B1 - 5V INPUT, eFUSE AND STAR DISTRIBUTION',105,15,2),('VUSB-VIN PAD MUST BE CUT. System 5V -> F101 -> D101 -> VIN; VUSB pad -> D102 -> VIN.',105,115,1.2),('TPS259470 internal back-to-back FET provides reverse-polarity/RCB. SD-25B-5 must be adjusted and sealed at 5.00V.',105,122,1.1),('R102/R103/R104 set UVLO typ 4.43V and OVLO typ 5.46V. All 5V branch LEDs/TPs are required on PCB.',105,129,1.1)]
sheet('POWER_A_B1.kicad_sch','Central Board Power A/B1','5V eFuse, diode-OR and protected star branches',parts,notes)

LTV=[('1','A1','L',7,'input'),('2','K1','L',5,'input'),('3','A2','L',3,'input'),('4','K2','L',1,'input'),('5','A3','L',-1,'input'),('6','K3','L',-3,'input'),('7','A4','L',-5,'input'),('8','K4','L',-7,'input'),('9','E1','R',7,'passive'),('10','C1','R',5,'open_collector'),('11','E2','R',3,'passive'),('12','C2','R',1,'open_collector'),('13','E3','R',-1,'passive'),('14','C3','R',-3,'open_collector'),('15','E4','R',-5,'passive'),('16','C4','R',-7,'open_collector')]
MOS=[('1','G','L',0,'input'),('2','S','R',-3,'passive'),('3','D','R',3,'passive')]
parts=[
 ('CTRL24','J10','24V_CTRL_IN',30,40,P2,['+24V_CTRL_IN','GND_CTRL'],''),('MicroFit6','J11','43650-0600 ESTOP_CTRL',35,75,P6,['ESTOP_LOOP_OUT','ESTOP_LOOP_RETURN','ESTOP_LED_24V','GND_CTRL','ESTOP1_AUX_RETURN','ESTOP2_AUX_RETURN'],'Connector_Molex:Molex_Micro-Fit_3.0_43650-0600_1x06_P3.00mm_Horizontal'),
 ('Fuse','F10','250mA safety loop',75,35,R,['+24V_CTRL_IN','ESTOP_LOOP_OUT'],''),('Fuse','F11','250mA LED/AUX',75,45,R,['+24V_CTRL_IN','ESTOP_LED_24V'],''),
 ('LTV-847S','U10','LTV-847S 4ch isolation',110,68,LTV,['ESTOP_LOOP_RETURN','OPTO1_K','ESTOP1_AUX_RETURN','OPTO2_K','ESTOP2_AUX_RETURN','OPTO3_K','+24V_CTRL_IN','OPTO4_K','GND_CTRL','ESTOP_LOOP_OK_N','GND_CTRL','ESTOP1_AUX_OK_N','GND_CTRL','ESTOP2_AUX_OK_N','GND_CTRL','ESTOP_SPARE_OK_N'],''),
 ('Resistor','R10','2k2 CH1A',60,60,R,['ESTOP_LOOP_RETURN','OPTO1_MID'],''),('Resistor','R11','2k2 CH1B',80,60,R,['OPTO1_MID','OPTO1_K'],''),('Resistor','R12','2k2 CH2A',60,70,R,['ESTOP1_AUX_RETURN','OPTO2_MID'],''),('Resistor','R13','2k2 CH2B',80,70,R,['OPTO2_MID','OPTO2_K'],''),('Resistor','R14','2k2 CH3A',60,80,R,['ESTOP2_AUX_RETURN','OPTO3_MID'],''),('Resistor','R15','2k2 CH3B',80,80,R,['OPTO3_MID','OPTO3_K'],''),
 ('Diode','D11','1N4148W CH1 reverse',75,52,R,['OPTO1_K','ESTOP_LOOP_RETURN'],''),('Diode','D12','1N4148W CH2 reverse',75,74,R,['OPTO2_K','ESTOP1_AUX_RETURN'],''),('Diode','D13','1N4148W CH3 reverse',75,86,R,['OPTO3_K','ESTOP2_AUX_RETURN'],''),
 ('Resistor','R16','10k CH1 pullup',145,84,R,['ESTOP_LOOP_OK_N','+3V3_TEENSY'],''),('Resistor','R17','10k CH2 pullup',165,84,R,['ESTOP1_AUX_OK_N','+3V3_TEENSY'],''),('Resistor','R18','10k CH3 pullup',185,84,R,['ESTOP2_AUX_OK_N','+3V3_TEENSY'],''),('Resistor','R19','10k CH4 pullup',205,84,R,['ESTOP_SPARE_OK_N','+3V3_TEENSY'],''),
 ('Contactor','J12','KILIGEN E228 coil external',165,38,P2,['ESTOP_LOOP_RETURN','CONTACTOR_COIL_NEG'],''),('IRLML0100TRPBF','Q1','IRLML0100TRPBF',165,68,MOS,['MOTOR_PWR_EN_G','GND_CTRL','CONTACTOR_COIL_NEG'],'Package_TO_SOT_SMD:SOT-23'),('Resistor','R20','100R gate',140,60,R,['MOTOR_PWR_EN','MOTOR_PWR_EN_G'],''),('Resistor','R21','47k gate pulldown',140,72,R,['MOTOR_PWR_EN_G','GND_CTRL'],''),('TVS','D10','coil TVS REVIEW',195,50,R,['ESTOP_LOOP_RETURN','CONTACTOR_COIL_NEG'],''),
 ('Divider','R22','100k 0.1%',175,100,R,['MOTOR_24V','MOTOR_SENSE_DIV'],''),('Divider','R23','100k 0.1%',195,100,R,['MOTOR_SENSE_DIV','MOTOR_SENSE_LO'],''),('Divider','R24','20k 0.1%',215,100,R,['MOTOR_SENSE_LO','GND_CTRL'],''),('Resistor','R25','1k ADC series',215,112,R,['MOTOR_SENSE_LO','MOTOR_PWR_SENSE'],''),('Capacitor','C10','10nF ADC filter',235,112,P2,['MOTOR_PWR_SENSE','GND_CTRL'],'')]
notes=[('D - 24V HARD E-STOP, CONTACTOR DRIVE AND MOTOR-BUS SENSE',110,15,2),('HARD SAFETY PATH: CTRL24 -> F10 -> ESTOP_LOOP_OUT -> two panel NC contacts -> RETURN -> coil+. Firmware is monitoring only.',110,122,1.05),('LTV-847S pin mapping verified: A/K=1/2,3/4,5/6,7/8; E/C=9/10,11/12,13/14,15/16. Each used input has 2x2k2 + reverse diode.',110,129,1.05),('LTV-847S footprint is deliberately blank: verify the wide 2.54mm-pitch SMD package against the purchased reel before creating a custom footprint.',110,136,1.05),('Q1 default OFF: 100R gate resistor + 47k pulldown. Coil TVS voltage/type is REVIEW; do not fit 1N4007-only clamp.',110,143,1.05)]
sheet('SAFETY_D.kicad_sch','Central Board Safety D','Hardwired E-stop loop, isolated diagnostics and contactor driver',parts,notes)

parts=[('GH4','J20','Matek I2C-INA-BM',100,52,P4,['GND_CTRL','I2C0_SDA','I2C0_SCL','+5V_SYS'],'Connector_JST:JST_GH_BM04B-GHS-TBT_1x04-1MP_P1.25mm_Horizontal')]
notes=[('E - EXTERNAL BATTERY VOLTAGE / CURRENT MONITOR',110,15,2),('Purchased Matek I2C-INA-BM is external: BAT+ -> module -> ESC+/load. No main current flows through central PCB.',110,100,1.2),('J20 JST-GH 4pin: 1=GND, 2=I2C0_SDA, 3=I2C0_SCL, 4=+5V_SYS (module supply is 4-9V).',110,107,1.1),('Default I2C address 69 / 0x45; jumpers permit 68 / 0x44 or 65 / 0x41. No ALERT wire in this interface.',110,114,1.1),('REVIEW BEFORE POWER: verify module I2C pull-up voltage is 3.3V-safe for Teensy; never apply 5V to GPIO.',110,121,1.1),('Matek stated limits: 0-85V, 150A continuous, 204.8A burst, 200uohm typ shunt. Check wiring and thermal rise.',110,128,1.1)]
sheet('MONITORING_E.kicad_sch','Central Board Monitoring E','Matek I2C-INA-BM external power monitor',parts,notes)

SRV=[('1','IO1','L',4.5,'bidirectional'),('2','GND','L',1.5,'power_in'),('3','IO2','L',-1.5,'bidirectional'),('4','IO3','L',-4.5,'bidirectional'),('5','VCC','R',2,'power_in'),('6','IO4','R',-2,'bidirectional')]
parts=[('GH4','J30','I2C0 GH4',25,35,P4,['+3V3_TEENSY','GND_CTRL','I2C0_SDA_EXT','I2C0_SCL_EXT'],''),('GH4','J31','I2C1 GH4',25,65,P4,['+3V3_TEENSY','GND_CTRL','I2C1_SDA_EXT','I2C1_SCL_EXT'],''),('GH3','J32','UART7 GH3',25,95,P3,['GND_CTRL','UART7_TX_EXT','UART7_RX_EXT'],''),('GH3','J33','UART8 GH3',25,115,P3,['GND_CTRL','UART8_TX_EXT','UART8_RX_EXT'],''),('SRV05-4','U30','SRV05-4 REVIEW maker',65,45,SRV,['I2C0_SDA_EXT','GND_CTRL','I2C0_SCL_EXT','I2C1_SDA_EXT','+3V3_TEENSY','I2C1_SCL_EXT'],'Package_TO_SOT_SMD:SOT-23-6'),('SRV05-4','U31','SRV05-4 REVIEW maker',65,105,SRV,['UART7_TX_EXT','GND_CTRL','UART7_RX_EXT','UART8_TX_EXT','+3V3_TEENSY','UART8_RX_EXT'],''),('GH7','J34','SPI GH7',125,35,[('1','1','L',8,'passive'),('2','2','L',5.3,'passive'),('3','3','L',2.6,'passive'),('4','4','L',0,'passive'),('5','5','L',-2.6,'passive'),('6','6','L',-5.3,'passive'),('7','7','L',-8,'passive')],['+3V3_TEENSY','GND_CTRL','SPI_SCK_EXT','SPI_MOSI_EXT','SPI_MISO_EXT','SPI_CS0_N_EXT','SPI_CS1_N_EXT'],''),('SRV05-4','U32','SRV05-4 SPI 1',170,30,SRV,['SPI_SCK_EXT','GND_CTRL','SPI_MOSI_EXT','SPI_MISO_EXT','+3V3_TEENSY','SPI_CS0_N_EXT'],''),('SRV05-4','U33','SRV05-4 SPI 2',170,55,SRV,['SPI_CS1_N_EXT','GND_CTRL','NC_SRV33','NC_SRV34','+3V3_TEENSY','NC_SRV36'],''),('GH10','J35','GPIO/ADC GH10',125,100,[(str(i),str(i),'L',12-(i-1)*2.65,'passive') for i in range(1,11)],['+3V3_TEENSY','GND_CTRL','IO20_A6_EXT','IO21_A7_EXT','IO24_A10_EXT','IO25_A11_EXT','IO26_A12_EXT','IO27_A13_EXT','IO40_A16_EXT','IO41_A17_EXT'],''),('SRV05-4','U34','SRV05-4 GPIO 1',175,90,SRV,['IO20_A6_EXT','GND_CTRL','IO21_A7_EXT','IO24_A10_EXT','+3V3_TEENSY','IO25_A11_EXT'],''),('SRV05-4','U35','SRV05-4 GPIO 2',175,115,SRV,['IO26_A12_EXT','GND_CTRL','IO27_A13_EXT','IO40_A16_EXT','+3V3_TEENSY','IO41_A17_EXT'],''),
 ('Resistor','R40','100R I2C0 SDA',80,135,R,['I2C0_SDA','I2C0_SDA_EXT'],''),('Resistor','R41','100R I2C0 SCL',110,135,R,['I2C0_SCL','I2C0_SCL_EXT'],''),('Resistor','R42','100R I2C1 SDA',140,135,R,['I2C1_SDA','I2C1_SDA_EXT'],''),('Resistor','R43','100R I2C1 SCL',170,135,R,['I2C1_SCL','I2C1_SCL_EXT'],''),
 ('Resistor','R44','2k2 I2C0 SDA pullup',80,145,R,['+3V3_TEENSY','I2C0_SDA_PU'],''),('SolderJumper','SJ40','OPEN=external pullup',110,145,P2,['I2C0_SDA_PU','I2C0_SDA'],''),('Resistor','R45','2k2 I2C0 SCL pullup',140,145,R,['+3V3_TEENSY','I2C0_SCL_PU'],''),('SolderJumper','SJ41','OPEN=external pullup',170,145,P2,['I2C0_SCL_PU','I2C0_SCL'],''),
 ('Resistor','R46','2k2 I2C1 SDA pullup',80,155,R,['+3V3_TEENSY','I2C1_SDA_PU'],''),('SolderJumper','SJ42','OPEN=external pullup',110,155,P2,['I2C1_SDA_PU','I2C1_SDA'],''),('Resistor','R47','2k2 I2C1 SCL pullup',140,155,R,['+3V3_TEENSY','I2C1_SCL_PU'],''),('SolderJumper','SJ43','OPEN=external pullup',170,155,P2,['I2C1_SCL_PU','I2C1_SCL'],''),
 ('Resistor','R48','100R UART7 TX',80,165,R,['UART7_TX','UART7_TX_EXT'],''),('Resistor','R49','100R UART7 RX',110,165,R,['UART7_RX','UART7_RX_EXT'],''),('Resistor','R50','100R UART8 TX',140,165,R,['UART8_TX','UART8_TX_EXT'],''),('Resistor','R51','100R UART8 RX',170,165,R,['UART8_RX','UART8_RX_EXT'],''),
 ('Resistor','R52','100R SPI SCK',80,175,R,['SPI_SCK','SPI_SCK_EXT'],''),('Resistor','R53','100R SPI MOSI',110,175,R,['SPI_MOSI','SPI_MOSI_EXT'],''),('Resistor','R54','100R SPI MISO',140,175,R,['SPI_MISO','SPI_MISO_EXT'],''),('Resistor','R55','100R SPI CS0',170,175,R,['SPI_CS0_N','SPI_CS0_N_EXT'],''),('Resistor','R56','100R SPI CS1',200,175,R,['SPI_CS1_N','SPI_CS1_N_EXT'],''),
 ('Resistor','R57','100R GPIO A6',80,185,R,['IO20_A6','IO20_A6_EXT'],''),('Resistor','R58','100R GPIO A7',110,185,R,['IO21_A7','IO21_A7_EXT'],''),('Resistor','R59','100R GPIO A10',140,185,R,['IO24_A10','IO24_A10_EXT'],''),('Resistor','R60','100R GPIO A11',170,185,R,['IO25_A11','IO25_A11_EXT'],''),('Resistor','R61','100R GPIO A12',80,195,R,['IO26_A12','IO26_A12_EXT'],''),('Resistor','R62','100R GPIO A13',110,195,R,['IO27_A13','IO27_A13_EXT'],''),('Resistor','R63','100R GPIO A16',140,195,R,['IO40_A16','IO40_A16_EXT'],''),('Resistor','R64','100R GPIO A17',170,195,R,['IO41_A17','IO41_A17_EXT'],''),
 ('Button','SW30','REARM physical button',220,35,P2,['REARM_SW_N','GND_CTRL'],''),('Resistor','R30','10k REARM pullup',220,48,R,['REARM_SW_N','+3V3_TEENSY'],''),('Capacitor','C30','100nF debounce',220,60,P2,['REARM_SW_N','GND_CTRL'],'')]
notes=[('F / F1 - PROTECTED REUSABLE EXPANSION',115,15,2),('All external logic is 3.3V ONLY. Each SRV05-4: pin 5 = +3V3_TEENSY and pin 2 = GND_CTRL.',115,205,1.05),('Every external signal is TVS-protected on the header side and has a 100R series part. I2C pullups are 2k2 + normally-open solder jumpers.',115,212,1.05),('Activity LED tap pads are DNP in Rev.A: direct UART/CAN taps would display idle-HIGH, not meaningful traffic. No new Teensy GPIO.',115,219,1.05),('Teensy external 3.3V budget: 100mA total Rev.A. SRV05-4 manufacturer/second source requires confirmation before BOM release.',115,226,1.05)]
sheet('EXPANSION_F_F1.kicad_sch','Central Board Expansion F/F1','Protected I2C UART SPI GPIO and re-arm interface',parts,notes)

# Parser smoke-test fixture; it is deliberately removed after development and
# never a deliverable.
sheet('_native_smoke.kicad_sch','Native smoke','parser check', [('Test','R999','test',100,100,R,['NET_A','NET_B'],'')], [('SMOKE',100,50,2)])
OUT.joinpath('_empty_smoke.kicad_sch').write_text('(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") (uuid "'+u()+'") (paper "A4") (lib_symbols) (sheet_instances (path "/" (page "1"))))\n', encoding='utf-8')
OUT.joinpath('_lib_smoke.kicad_sch').write_text('(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") (uuid "'+u()+'") (paper "A4") (lib_symbols '+libsym('Test',R)+') (sheet_instances (path "/" (page "1"))))\n', encoding='utf-8')
# Narrow parser fixtures retained only while repairing this generator.
OUT.joinpath('_instance_smoke.kicad_sch').write_text('(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") (uuid "'+u()+'") (paper "A4") (lib_symbols '+libsym('Test',R)+' ) '+instance('Test','R999','test',100,100,R)+' (sheet_instances (path "/" (page "1"))))\n', encoding='utf-8')
OUT.joinpath('_label_smoke.kicad_sch').write_text('(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") (uuid "'+u()+'") (paper "A4") (lib_symbols '+libsym('Test',R)+' ) '+instance('Test','R999','test',100,100,R)+' '+ ' '.join(connect_labels(100,100,R,['NET_A','NET_B'])) +' (sheet_instances (path "/" (page "1"))))\n', encoding='utf-8')
OUT.joinpath('_bare_label_smoke.kicad_sch').write_text('(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") (uuid "'+u()+'") (paper "A4") (lib_symbols '+libsym('Test',R)+' ) '+instance('Test','R999','test',100,100,R)+' '+label('NET_A', 80, 100)+' (sheet_instances (path "/" (page "1"))))\n', encoding='utf-8')

print('generated', *[p.name for p in OUT.glob('*.kicad_sch')])

