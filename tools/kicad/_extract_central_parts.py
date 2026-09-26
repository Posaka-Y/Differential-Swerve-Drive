import json
from pathlib import Path

sheets=[]
def sheet(id,title):
    s={'id':id,'title':title,'parts':[]}; sheets.append(s); return s['parts']
def add(ref,value,lib,fp='',note='',status='documented'):
    p.append(dict(ref=ref,value=value,lib_id=lib,footprint=fp,note=note,status=status))
RFP='Resistor_SMD:R_0603_1608Metric'; CFP='Capacitor_SMD:C_0603_1608Metric'
def r(ref,value,note='',status='documented'):add(ref,value,'Device:R',RFP,note,status)
def c(ref,value,note='',fp=CFP,status='documented'):add(ref,value,'Device:C',fp,note,status)
def gh(ref,n,note='',status='documented'):
    add(ref,f'SM{n:02}B-GHS-TB',f'Connector_Generic:Conn_01x{n:02}',f'Connector_JST:JST_GH_SM{n:02}B-GHS-TB_1x{n:02}-1MP_P1.25mm_Horizontal',note,status)
def tp(ref,net,signal=False):add(ref,net,'Connector:TestPoint','TestPoint:TestPoint_Pad_D1.5mm' if signal else 'DifferentialSwerve:Harwin_S1751-46R','Signal pad' if signal else 'S1751-46R')
p=sheet('S02A_power_input','5V input / eFuse / USB diode OR')
add('J101','XT30PW-M','Connector_Generic:Conn_01x02','Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal')
add('J102','VUSB pickup TBD','Connector:TestPoint',note='引出し方法とfootprint未確定',status='unresolved')
add('U101','TPS259470LRPWR','CentralPlacement:TPS259470LRPWR',note='正本10pin表に基づく自作symbol。RPW land pattern未確定、footprint空欄',status='footprint_unresolved')
for i,v in enumerate(['750','732k','51.1k','221k','10k','0'],101):r(f'R{i}',v,'dVdt series proposal: 0R for 10nF, 100R if >10nF' if i==106 else '', 'provisional' if i==106 else 'documented')
c('C101','100uF 10V','MPN/package TBD',fp='',status='unresolved')
c('C102','1uF','C1608X7R1E105K080AB');c('C103','1uF','C1608X7R1E105K080AB')
c('C104','470uF 10V low-ESR','MPN/package TBD',fp='',status='unresolved');c('C105','10nF','C1608C0G1H103J080AA')
for i in [101,102]:add(f'D{i}','PMEG2010EA,115','Device:D_Schottky','Diode_SMD:D_SOD-323')
for i,n in enumerate(['+5V_RAW','+5V_SYS','VIN_TEENSY','GND_CTRL','PWR_5V_FAULT_N'],101):tp(f'TP{i}',n,i==105)
p=sheet('S02B_star_teensy','Star power / Teensy / indicators')
for i in range(201,207):
    add(f'F{i}','1206L075/16YR' if i==205 else '1206L050/15YR','Device:Polyfuse','Fuse:Fuse_1206_3216Metric','Rating review pending' if i>=205 else '', 'provisional' if i>=205 else 'documented')
    add(f'D{i}','LTST-C190KGKT','Device:LED','LED_SMD:LED_0603_1608Metric');r(f'R{i}','1.5k')
    if i<=204:gh(f'J{i}',2,'1=5V branch / 2=GND')
add('J210','Teensy 4.1 socket','CentralPlacement:Teensy41_Socket','DifferentialSwerve:Teensy41_Socket_2x24','単一48pinは旧J210/J211の代替。列中心間15.24mm、pad順は転記資料3.2。socket実物/ドリル照合は未完了', 'mechanical_review')
for i,v in [(211,'LTST-C190KGKT'),(212,'LTST-C190KRKT'),(213,'LTST-C190KGKT')]:add(f'D{i}',v,'Device:LED','LED_SMD:LED_0603_1608Metric');r(f'R{i}','1.5k' if i==213 else '1k')
r('R214','10k');c('C211','100nF');c('C212','100nF','Socket bypass proposal',status='provisional')
add('SW211','REARM switch TBD','Switch:SW_Push',note='型番/基板またはパネル配置未確定',status='unresolved')
for i,n in enumerate(['+5V_UNIT1','+5V_UNIT2','+5V_UNIT3','+5V_ODOM','+5V_TEENSY_F','+5V_EXP','+3V3_TEENSY','GND_CTRL'],211):tp(f'TP{i}',n)
for x,name in [(1,'Sensor'),(2,'Expansion'),(3,'Drive')]:
    p=sheet(f'S03_CAN{x}',f'CAN{x} {name}')
    base=300+x*10
    add(f'U{base+1}','TCAN1051VDRQ1','DifferentialSwerve:TCAN1051VDRQ1','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
    add(f'D{base+1}','ESD2CAN24DBZRQ1','DifferentialSwerve:ESD2CAN24DBZRQ1','Package_TO_SOT_SMD:SOT-23')
    for k in [1,2]:c(f'C{base+k}','100nF');gh(f'J{base+k}',3,'1=COMM_A / 2=COMM_B / 3=GND; 2 ports/bus is provisional',status='port_count_provisional');tp(f'TP{base+k}','COMM_A' if k==1 else 'COMM_B')
    r(f'R{base+1}','120');add(f'SW{base+1}','JS102011SAQN','DifferentialSwerve:JS102011SAQN','DifferentialSwerve:JS102011SAQN','ON方向はPCB/シルクで要確認')
    if x==2:gh('J323',4,'1=5V_EXP / 2=GND / 3=COMM_A / 4=COMM_B')
p=sheet('S04_safety','E-stop monitoring / central coil driver')
add('J401','43650-0600','Connector_Generic:Conn_01x06','Connector_Molex:Molex_Micro-Fit_3.0_43650-0600_1x06_P3.00mm_Horizontal')
for ref,note in [('J402','暫定1=COIL_POS / 2=COIL_NEG'),('J403','暫定1=24V_CTRL_IN / 2=GND_24V_RETURN')]:add(ref,'TBD 2pin','Connector_Generic:Conn_01x02',note=note+'; 正式MPN/pin順/key未確定',status='unresolved')
add('U401','LTV-847S','Isolator:LTV-847S',note='4 units all required. footprint未確定; SMDIP-16_W9.53mm候補を実物照合する',status='footprint_unresolved')
for i in range(401,409):r(f'R{i}','2.2k','Spare channel implementation provisional' if i>=407 else '')
for i in range(409,413):r(f'R{i}','10k','Spare channel implementation provisional' if i==412 else '')
for i in range(401,405):add(f'D{i}','1N4148W','Diode:1N4148W','Diode_SMD:D_SOD-123','Spare channel implementation provisional' if i==404 else '')
add('U402','SN74AHCT1G125DBVR','74xGxx:74AHCT1G125','Package_TO_SOT_SMD:SOT-23-5','2026-09-23 PDF候補、DBV:1=OE_N 2=A 3=GND 4=Y 5=VCC。symbol pin要照合',status='provisional')
add('Q401','IRLML0100TRPBF','Transistor_FET:IRLML0100','Package_TO_SOT_SMD:SOT-23','2026-09-23 PDF基本案:1=G 2=S 3=D',status='provisional')
r('R413','100k','Input pulldown, PDF candidate',status='provisional');r('R414','100','Gate resistor, PDF candidate',status='provisional');r('R415','100k','Gate pulldown, PDF candidate',status='provisional');c('C401','100nF','U402 bypass, PDF candidate',status='provisional')
add('F401','TBD coil fuse','Device:Fuse',note='定格/型番/配置未確定',status='unresolved')
for i,n in enumerate(['ESTOP_LOOP_OK_N','ESTOP1_AUX_OK_N','ESTOP2_AUX_OK_N','SPARE_24V_IN','SPARE_OK_N','GND_CTRL_LED'],401):tp(f'TP{i}',n,True)
p=sheet('S05_io','Matek battery monitor / expansion I/O')
for i,n in [(501,4),(502,4),(503,4),(504,3),(505,3),(506,7),(507,10)]:gh(f'J{i}',n,'J507 GH10 format/pin order proposal' if i==507 else '',status='provisional' if i==507 else 'documented')
for i in range(501,507):add(f'U{i}','SRV05-4','Power_Protection:SRV05-4','Package_TO_SOT_SMD:SOT-23-6','Manufacturer not fixed; pin1/3/4/6=IO,2=GND,5=3V3; verify library')
for seq in [range(511,515),range(521,525),range(531,536),range(541,549)]:
    for i in seq:r(f'R{i}','100')
for i in range(551,555):r(f'R{i}','2.2k')
for i in range(501,505):add(f'JP{i}','Pullup enable N.O.','Jumper:SolderJumper_2_Open','Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm')
tp('TP501','GND_CTRL')
data={'scope':'Symbol placement only; no wires, net labels, NC flags or power flags. Library names are candidates requiring existence/pin check. No part selections made.', 'sources':['docs/electrical/CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md','docs/electrical/CENTRAL_BOARD_REV1_PDF_CHANGELOG_2026-09-23.md','tmp/pdfs/build_central_board_rev1_schematic_2026_09_23.py','docs/ARCHITECTURE_DECISIONS.md'], 'sheets':sheets, 'excluded_unresolved':[{'item':'D4xx coil clamp','reason':'Topology/polarity/value/MPN undecided; textual placeholder only, do not select diode/TVS symbol'},{'item':'COMM LED','reason':'GPIO/implementation undecided; no part Ref fixed'},{'item':'LED branch protection','reason':'F402 revival/rating/MPN undecided'}], 'conflicts':['中央の最終正本は専用CAN GH3。2026-09-23 V2作業ログの後発CAN2pin指定は駆動V2対象確認中で中央の変更承認ではない。','旧S04 J402=別体driver5線/CONTACTOR_STATUS_Nは撤回。中央コイルdriverとJ402コイル2線へ更新。','旧中央モニタINA238回路/shuntはMatek I2Cモジュールへ置換、中央へ配置しない。','旧Teensy 1x24 x2のRefを単一J210へ統合。列中心15.24mm。']}
for sh in sheets:
    for part in sh['parts']:
        if part['ref']=='Q401':
            part['lib_id']='CentralPlacement:IRLML0100TRPBF'
            part['custom_pins']=[{'number':str(i),'name':name,'type':typ} for i,name,typ in [(1,'G','input'),(2,'S','passive'),(3,'D','passive')]]
        if part['ref']=='U101':
            part['custom_pins']=[{'number':str(i),'name':name,'type':typ} for i,name,typ in [(1,'EN/UVLO','input'),(2,'OVLO','input'),(3,'AUXOFF','open_collector'),(4,'FLT','open_collector'),(5,'IN','power_in'),(6,'OUT','power_out'),(7,'dVdt','passive'),(8,'GND','power_in'),(9,'ILM','passive'),(10,'ITIMER','passive')]]
            part['note']+='; pin表出典: 転記リファレンス3.1、TI TPS25947 SLVSFC9C Rev.C DS照合済み記載'
        if part['ref']=='J210':
            names=['GND','0','1','2','3','4','5','6','7','8','9','10','11','12','3.3V','24/A10','25/A11','26/A12','27/A13','28','29','30','31','32','33','34','35','36','37','38','39','40/A16','41/A17','GND','13','14/A0','15/A1','16/A2','17/A3','18/A4','19/A5','20/A6','21/A7','22/A8','23/A9','3.3V','GND','VIN']
            part['custom_pins']=[{'number':str(i),'name':name,'type':'passive'} for i,name in enumerate(names,1)]
            part['note']+='; socket contacts are passive; firmware signal directions are separate design data'
out=Path(__file__).with_name('central-placement-parts.json');out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'{out}: {len(sheets)} sheets, {sum(len(s["parts"]) for s in sheets)} parts')
