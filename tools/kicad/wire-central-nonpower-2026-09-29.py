"""Wire the reviewed saved snapshot, never regenerate the power/CAN sheets.

This is a one-shot migration. TBD safety parts remain explicit design placeholders.
"""
import copy, json, math, runpy, uuid
from pathlib import Path

g=runpy.run_path(str(Path(__file__).with_name('generate-central-placement.py')))
ch,f,q=g['children'],g['first'],g['q']; root=g['ROOT']
dest=root/'hardware/central-board-placement'
out=root/'output/kicad-check/central-nonpower-wiring-2026-09-29'
backup=out/'before/central-board-placement'
libs=g['Libraries'](); expected={}; serial=0
def uid():
    global serial
    serial+=1
    return q(str(uuid.uuid5(uuid.NAMESPACE_URL,'central-nonpower-20260929/'+str(serial))))
def props(s): return {json.loads(p[1]):json.loads(p[2]) for p in ch(s,'property')}
def setprop(s,k,v):
    p=next((p for p in ch(s,'property') if json.loads(p[1])==k),None)
    if p:p[2]=q(v)
    else:s.append(g['prop'](k,v,hide=True))
class Sheet:
    def __init__(self,name):
        self.path=dest/(name+'.kicad_sch'); self.name=name
        assert self.path.read_bytes()==(backup/self.path.name).read_bytes(),'Changed since snapshot: '+name
        self.t=g['parse'](self.path.read_text(encoding='utf-8-sig'))
        self.parts={props(s)['Reference']:s for s in ch(self.t,'symbol')}
    def clear(self):
        self.t[:]=[a for a in self.t if not isinstance(a,list) or a[0] not in ('symbol','wire','junction','label','global_label','no_connect','text','polyline','rectangle')]
    def place(self,ref,x,y,angle=0,libid=None,value=None,footprint=None,template=None):
        if ref in self.parts:s=self.parts[ref]
        else:
            s=copy.deepcopy(self.parts[template or next(iter(self.parts))])
            for n in g['walk'](s):
                if n[0]=='uuid':n[1]=uid()
                if n[0]=='reference':n[1]=q(ref)
            setprop(s,'Reference',ref)
            self.parts[ref]=s
        if libid:f(s,'lib_id')[1]=q(libid)
        libid=json.loads(f(s,'lib_id')[1]); cache=f(self.t,'lib_symbols')
        if not any(a[1]==q(libid) for a in ch(cache,'symbol')):cache.append(libs.get(libid))
        f(s,'at')[1:]=list(map(str,(x,y,angle)))
        s[:]=[a for a in s if not isinstance(a,list) or a[0] not in ('mirror','pin')]
        if value is not None:setprop(s,'Value',value)
        if footprint is not None:setprop(s,'Footprint',footprint)
        setprop(s,'Placement note','Connected schematic; see nonpower wiring review 2026-09-29')
        for p in ch(s,'property'):
            key=json.loads(p[1]); f(p,'at')[1:]=list(map(str,(x,y-7.62 if key=='Reference' else y-5.08,0)))
            if key in ('Reference','Value'):
                p[p.index(f(p,'effects'))]=g['effects'](1.1)
        if s not in ch(self.t,'symbol'):self.t.append(s)
        return s
    def point(self,ref,pin):
        s=self.parts[ref]; at=f(s,'at'); x,y,a=map(float,at[1:]); a=math.radians(a)
        lib=next(a for a in ch(f(self.t,'lib_symbols'),'symbol') if a[1]==f(s,'lib_id')[1])
        p=next(p for p in g['walk'](lib) if p[0]=='pin' and json.loads(f(p,'number')[1])==str(pin))
        px,py,pa=map(float,f(p,'at')[1:]); dx=px*math.cos(a)-py*math.sin(a);dy=-px*math.sin(a)-py*math.cos(a)
        # Outward direction is opposite the library pin's pointing direction.
        d=math.radians(pa+float(at[3])+180)
        return (round(x+dx,4),round(y+dy,4)),(round(math.cos(d)),round(-math.sin(d)))
    def wire(self,a,b):
        if a!=b:self.t.append(['wire',['pts',['xy',*map(str,a)],['xy',*map(str,b)]],['stroke',['width','0'],['type','default']],['uuid',uid()]])
    def label(self,net,p,left=True,global_=False):
        fx=g['effects'](.95);fx.append(['justify','right' if left else 'left'])
        n=['global_label' if global_ else 'label',q(net)]
        if global_:n.append(['shape','bidirectional'])
        n += [['at',*map(str,p),'180' if left else '0'],fx,['uuid',uid()]]
        if global_:n.append(g['prop']('Intersheetrefs','${INTERSHEET_REFS}',*p,hide=True))
        self.t.append(n)
    def connect(self,ref,pin,net,global_=False,length=5.08):
        expected[ref+'.'+str(pin)]=net
        a,d=self.point(ref,pin); b=(round(a[0]+d[0]*length,4),round(a[1]+d[1]*length,4))
        self.wire(a,b)
        self.label(net,b,left=d[0]<=0,global_=global_)
    def nc(self,ref,pin):
        a,_=self.point(ref,pin);self.t.append(['no_connect',['at',*map(str,a)],['uuid',uid()]])
        expected[ref+'.'+str(pin)]=None
    def text(self,msg,x,y,size=1.27):self.t.append(g['text'](msg,x,y,size))
    def write(self,title):
        tb=f(self.t,'title_block');f(tb,'title')[1]=q(title);f(tb,'date')[1]=q('2026-09-29');f(tb,'rev')[1]=q('WIRED DRAFT')
        for n in ch(tb,'comment'):n[2]=q('Nonpower circuits wired; safety TBDs remain. Not for fabrication.')
        self.path.write_text(g['dump'](self.t)+'\n',encoding='utf-8')

# S02B: keep saved socket, labels, placement and complete RC circuit.
s=Sheet('S02B_star_teensy-1')
a,b=s.parts['D212'],s.parts['D213']
aa,bb=copy.deepcopy(f(a,'at')),copy.deepcopy(f(b,'at'))
for part,new in [(a,bb),(b,aa)]:
    old=f(part,'at');dx=float(new[1])-float(old[1]);dy=float(new[2])-float(old[2]);old[:]=new
    for p in ch(part,'property'):
        at=f(p,'at');at[1]=str(float(at[1])+dx);at[2]=str(float(at[2])+dy)
s.write('Teensy 4.1 / REARM / RUN ERR PWR indicators')

# S04 safety circuits: labels join functional blocks, with series monitor drawn continuously.
s=Sheet('S04_safety-1');s.clear()
s.text('E-STOP LOOP / COIL DRIVER',290,18,2.54)
s.text('24 V LOOP & EXTERNAL CONNECTORS',135,35,1.8)
for r,x,y,l,v,nets in [
 ('J403',105,60,None,None,['+24V_CTRL_IN','GND_24V_RETURN']),
 ('J401',255,65,'Connector_Generic:Conn_01x04','TBD E-stop 4pin',['ESTOP_LOOP_OUT','ESTOP_LOOP_RETURN','ESTOP_LED_24V','GND_CTRL_LED']),
 ('J402',410,60,None,None,['ESTOP_LOOP_RETURN','COIL_NEG'])]:
    s.place(r,x,y,libid=l,value=v,footprint='' if r=='J401' else None,template='J403')
    for i,n in enumerate(nets,1):s.connect(r,i,n)
s.text('J401: 1 OUT -> NC1 11-12 -> NC2 11-12 -> 2 RETURN\n3 LED supply -> X1/X2 (polarity verify); 4 LED return\nButtons / contactor are external to this board.',265,94)
for ref,x,y,v,a,b in [('F401',90,125,None,'+24V_CTRL_IN','ESTOP_LOOP_OUT'),('F402',265,125,'TBD LED branch fuse','+24V_CTRL_IN','ESTOP_LED_24V')]:
    s.place(ref,x,y,90,libid='Device:Fuse' if ref=='F402' else None,value=v,footprint='' if ref=='F402' else None,template='F401')
    s.connect(ref,1,a);s.connect(ref,2,b)
s.text('F401 / F402: current rating, breaking capacity and footprints TBD\nLED measurement: 24 V / ~0.3 W (~12.5 mA); quantity not confirmed',235,148)

s.text('NC LOOP MONITOR (LOW = LOOP ENERGIZED)',130,172,1.8)
s.place('R401',65,195,90);s.place('R402',90,195,90);s.place('U401',120,197.54)
s.connect('R401',1,'ESTOP_LOOP_RETURN')
for r1,p1,r2,p2,net in [('R401',2,'R402',1,'MONITOR_SERIES'),('R402',2,'U401',1,'MONITOR_LED_A')]:
    a,_=s.point(r1,p1);b,_=s.point(r2,p2);s.wire(a,b);s.label(net,((a[0]+b[0])/2,a[1]),False)
    expected[r1+'.'+str(p1)]=net;expected[r2+'.'+str(p2)]=net
s.connect('U401',2,'GND_CTRL_LED');s.connect('U401',3,'GND_CTRL');s.connect('U401',4,'ESTOP_LOOP_OK_N',True)
s.place('D401',85,229,90);s.connect('D401',1,'MONITOR_LED_A');s.connect('D401',2,'GND_CTRL_LED')
s.place('R409',188,223);s.connect('R409',1,'+3V3_TEENSY',True);s.connect('R409',2,'ESTOP_LOOP_OK_N',True)
s.place('TP401',190,257);s.connect('TP401',1,'ESTOP_LOOP_OK_N',True)
s.place('TP406',80,257);s.connect('TP406',1,'GND_CTRL_LED')
s.text('R401 + R402 = 4.4k total. D401 is reverse-parallel with optocoupler LED.\nLoop indication does not verify main contact opening / welding.',135,280)

s.text('5 V BUFFER -> 100 V MOSFET / DEFAULT OFF',420,172,1.8)
s.place('U402',350,210);s.connect('U402',1,'GND_CTRL');s.connect('U402',2,'MOTOR_PWR_EN',True)
s.connect('U402',3,'GND_CTRL');s.connect('U402',5,'+5V_SYS',True)
s.place('R414',405,210,90);a,_=s.point('U402',4);b,_=s.point('R414',1);s.wire(a,b);s.label('COIL_BUFFER_OUT',(380,210),False)
expected['U402.4']=expected['R414.1']='COIL_BUFFER_OUT'
s.place('Q401',475,210);a,_=s.point('R414',2);b,_=s.point('Q401',1);s.wire(a,b);s.label('COIL_GATE',(430,210),False)
expected['R414.2']=expected['Q401.1']='COIL_GATE'
s.connect('Q401',3,'COIL_NEG');s.connect('Q401',2,'GND_24V_RETURN')
for r,x,n in [('R413',315,'MOTOR_PWR_EN'),('R415',425,'COIL_GATE')]:
    s.place(r,x,265);s.connect(r,1,n,r=='R413');s.connect(r,2,'GND_CTRL' if r=='R413' else 'GND_24V_RETURN')
s.place('C401',520,265);s.connect('C401',1,'+5V_SYS',True);s.connect('C401',2,'GND_CTRL')

# Explicit unfitted design blocks: no invented selected part / manufacturing footprint.
custom={'lib_id':'CentralPlacement:CoilClamp_TBD','value':'CLAMP TBD','custom_pins':[{'number':1,'name':'COIL_POS'},{'number':2,'name':'COIL_NEG'}]}
libs.add_custom(custom)
s.place('X401',465,115,libid=custom['lib_id'],value='CLAMP TBD',footprint='',template='J403')
s.connect('X401',1,'ESTOP_LOOP_RETURN');s.connect('X401',2,'COIL_NEG')
s.text('X401: clamp topology / part / release time TBD',465,141)
returnblock={'lib_id':'CentralPlacement:ReturnJoin_TBD','value':'RETURN JOIN TBD','custom_pins':[{'number':1,'name':'LOGIC'},{'number':2,'name':'LED'},{'number':3,'name':'COIL'}]}
libs.add_custom(returnblock)
s.place('X402',140,333,libid=returnblock['lib_id'],value='RETURN JOIN TBD',footprint='',template='J403')
for pin,net in [(1,'GND_CTRL'),(2,'GND_CTRL_LED'),(3,'GND_24V_RETURN')]:s.connect('X402',pin,net,net=='GND_CTRL')
s.text('X402 is an unresolved return-connection interface, NOT a conductive net tie.\nJoin location / routing must be resolved before hardware use.\nDriver requires a defined logic-to-coil return reference.',350,330)
s.text('Unresolved: J401/J402/J403 selection; F401/F402; X401 clamp; X402 return connection.\nNo coil operation / fabrication release until these items are resolved.',295,372,1.5)
s.write('E-stop NC loop monitor / coil driver / explicit TBD interfaces')

# Publish custom symbols for ERC library consistency.
sympath=dest/'CentralPlacement.kicad_sym';sym=g['parse'](sympath.read_text(encoding='utf-8-sig'))
for libid,lib in libs.custom.items():
    lib=copy.deepcopy(lib);lib[1]=q(libid.split(':')[1]);sym.append(lib)
sympath.write_text(g['dump'](sym)+'\n',encoding='utf-8')

# S05: six functional cells, named stubs avoid unreadable cross-sheet wire bundles.
s=Sheet('S05_io-1');s.clear()
s.text('EXTERNAL I/O | 3.3 V SIGNALS | GPIO VCC SELECTOR IS POWER ONLY',295,16,2.2)
s.text('Global labels connect to Teensy. *_EXT labels are connector-side nets after 100 ohm resistors.',295,24)
groups=[
 ('I2C0 / I2C1',100,45,[(511,'I2C0_SDA'),(512,'I2C0_SCL'),(513,'I2C1_SDA'),(514,'I2C1_SCL')],501),
 ('UART7 / UART8',295,45,[(521,'UART7_TX'),(522,'UART7_RX'),(523,'UART8_TX'),(524,'UART8_RX')],502),
 ('SPI',490,45,[(531,'SPI_SCK'),(532,'SPI_MOSI'),(533,'SPI_MISO'),(534,'SPI_CS0_N'),(535,'SPI_CS1_N')],503),
 ('GPIO PORTS 1 / 2',100,245,[(541,'IO20_A6'),(542,'IO21_A7'),(543,'IO24_A10'),(544,'IO25_A11')],505),
 ('GPIO PORTS 3 / 4',295,245,[(545,'IO26_A12'),(546,'IO27_A13'),(547,'IO40_A16'),(548,'IO41_A17')],506)]
for title,x,y,signals,tvs in groups:
    s.text(title,x,y,1.8)
    for i,(num,net) in enumerate(signals):
        r='R'+str(num);s.place(r,x,y+20+i*13,90);s.connect(r,1,net,True);s.connect(r,2,net+'_EXT')
    uy=y+100;s.place('U'+str(tvs),x,uy)
    # Move reference/value outside the tall TVS symbol.
    for p in ch(s.parts['U'+str(tvs)],'property'):
        if json.loads(p[1]) in ('Reference','Value'):f(p,'at')[1:]=list(map(str,(x+24,uy-14 if json.loads(p[1])=='Reference' else uy-11,0)))
    for pin,(_,net) in zip((1,3,4,6),signals):s.connect('U'+str(tvs),pin,net+'_EXT')
    s.connect('U'+str(tvs),5,'+3V3_TEENSY',True);s.connect('U'+str(tvs),2,'GND_CTRL',True)

def connector(ref,x,y,nets,four=False):
    s.place(ref,x,y,libid='Connector_Generic:Conn_01x04' if four else None,value='SM04B-GHS-TB' if four else None,
        footprint='Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal' if four else None,template='J502')
    # Connector body has room on right; keep field text off closely spaced pin labels.
    for p in ch(s.parts[ref],'property'):
        if json.loads(p[1]) in ('Reference','Value'):
            f(p,'at')[1:]=list(map(str,(x+10,y-6 if json.loads(p[1])=='Reference' else y-3,0)))
            f(p,'effects').append(['justify','left'])
    for i,n in enumerate(nets,1):s.connect(ref,i,n,n in ('+3V3_TEENSY','+5V_SYS','GND_CTRL'))
connector('J501',90,187,['GND_CTRL','I2C0_SDA_EXT','I2C0_SCL_EXT','+5V_SYS'])
connector('J502',170,187,['+3V3_TEENSY','GND_CTRL','I2C0_SDA_EXT','I2C0_SCL_EXT'])
connector('J503',170,210,['+3V3_TEENSY','GND_CTRL','I2C1_SDA_EXT','I2C1_SCL_EXT'])
connector('J504',300,187,['GND_CTRL','UART7_TX_EXT','UART7_RX_EXT'])
connector('J505',300,213,['GND_CTRL','UART8_TX_EXT','UART8_RX_EXT'])
connector('J506',490,202,['+3V3_TEENSY','GND_CTRL','SPI_SCK_EXT','SPI_MOSI_EXT','SPI_MISO_EXT','SPI_CS0_N_EXT','SPI_CS1_N_EXT'])
for ref,x,y,a,b in [('J507',95,380,'IO20_A6','IO21_A7'),('J508',195,380,'IO24_A10','IO25_A11'),('J509',290,380,'IO26_A12','IO27_A13'),('J510',390,380,'IO40_A16','IO41_A17')]:
    connector(ref,x,y,['VCC_GPIO_EXT','GND_CTRL',a+'_EXT',b+'_EXT'],True)

# Remaining SPI protection channel, pullups and selector occupy right lower cell.
s.text('OPTIONS / ADDITIONAL SPI PROTECTION',495,245,1.6)
s.place('U504',500,280)
for p in ch(s.parts['U504'],'property'):
    if json.loads(p[1]) in ('Reference','Value'):f(p,'at')[1:]=list(map(str,(525,266 if json.loads(p[1])=='Reference' else 269,0)))
s.connect('U504',1,'SPI_CS1_N_EXT');[s.nc('U504',p) for p in (3,4,6)]
s.connect('U504',5,'+3V3_TEENSY',True);s.connect('U504',2,'GND_CTRL',True)
for i,net in enumerate(('I2C0_SDA','I2C0_SCL','I2C1_SDA','I2C1_SCL')):
    y=313+i*16;r='R'+str(551+i);jp='JP'+str(501+i)
    s.place(jp,450,y);s.place(r,520,y,90)
    s.connect(jp,1,'+3V3_TEENSY',True);s.connect(jp,2,'PU_'+net)
    s.connect(r,1,'PU_'+net);s.connect(r,2,net,True)
s.place('JP505',490,387)
for i,n in enumerate(('+3V3_TEENSY','VCC_GPIO_EXT','+5V_EXP'),1):s.connect('JP505',i,n,n!='VCC_GPIO_EXT')
s.place('TP501',35,220);s.connect('TP501',1,'GND_CTRL',True)
s.text('JP501-504 OPEN by default (optional 2.2k pullups)\nJP505: 1-2 = 3.3V default; 2-3 = 5V; ONE shunt only\nGPIO signals remain 3.3V. Total external 3.3V budget: 100mA.',295,405,1.1)
s.write('External I2C / UART / SPI / GPIO 4 ports')
(out/'expected-pins.json').write_text(json.dumps(expected,indent=2)+'\n',encoding='utf-8')
for p in backup.glob('*.kicad_sch'):
    if p.name.startswith(('S02A','S03')):assert p.read_bytes()==(dest/p.name).read_bytes(),p.name
print('Written three sheets. Power and CAN files unchanged. Pin expectations:',len(expected))
