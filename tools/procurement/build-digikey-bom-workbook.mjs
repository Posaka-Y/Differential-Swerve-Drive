import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const workspace = process.cwd();
const artifactDir = path.join(workspace, "outputs", "differential-swerve-bom-drive-only-20260907");
const procurementDir = path.join(workspace, "output", "procurement");
const qaDir = path.join(os.tmpdir(), "differential-swerve-bom-qa");
await fs.mkdir(artifactDir, { recursive: true });
await fs.mkdir(procurementDir, { recursive: true });
await fs.mkdir(qaDir, { recursive: true });

const driveBoards = 4;
const odomBoards = 1;

// Prices are DigiKey Japan JPY, tax excluded, checked 2026-09-07.
// unitPrice is the applicable cut-tape/tube tier at orderQty.
const parts = [
  ["コンデンサ","100nF 50V X7R 0603","KEMET","C0603C104K5RACTU","399-C0603C104K5RACTUCT-ND",13,12,100,6.87,"在庫あり","必要64個。100個で単価¥6.87、36個を実装予備","UNIT:C1,C2,C5-C9,C13,C15,C17,C18,C201,C203 / ODOM:C2,C4,C8,C9,C11-C14,C18,C19,C22,C28","https://www.digikey.jp/ja/products/detail/kemet/C0603C104K5RACTU/1465594",""],
  ["コンデンサ","10pF 50V C0G 0603","Samsung Electro-Mechanics","CL10C100JB8NNNC","1276-1027-1-ND",2,2,12,6.20,"在庫あり","10個価格を適用、予備2個","UNIT:C3,C4 / ODOM:C6,C7","https://www.digikey.jp/ja/products/detail/samsung-electro-mechanics/CL10C100JB8NNNC/3886685",""],
  ["コンデンサ","4.7uF 25V X7R 0805","Murata","GRM21BZ71E475KE15K","490-GRM21BZ71E475KE15KCT-ND",1,1,10,28.40,"在庫あり","必要5個＋予備。6個×¥48より10個×¥28.40の方が安い","UNIT:C10 / ODOM:C10","https://www.digikey.jp/ja/products/detail/murata-electronics/GRM21BZ71E475KE15K/17860893",""],
  ["コンデンサ","1uF 25V X7R 0603","TDK","C1608X7R1E105K080AB","445-5956-1-ND",2,1,12,17.80,"在庫あり","必要9個＋予備3個。10個価格を適用","UNIT:C11,C14 / ODOM:C16","https://www.digikey.jp/ja/products/detail/tdk/C1608X7R1E105K080AB/2443997","Taiyo Yuden TMK107B7105KA-T在庫0のため同一定格・同外形へ置換"],
  ["コンデンサ","10nF 50V C0G 0603","TDK","C1608C0G1H103J080AA","445-7404-1-ND",1,0,10,22.30,"在庫あり","必要4個。6個×¥38より10個×¥22.30の方が安い","UNIT:C12","https://www.digikey.jp/ja/products/detail/tdk-corporation/C1608C0G1H103J080AA/2732839","C0G、±5%、50V、0603を維持し、在庫と価格を確認できる品へ置換"],
  ["コンデンサ","10nF 100V X7R 0603","Murata","GRM188R72A103KA01D","490-GRM188R72A103KA01DCT-ND",1,0,10,5.80,"在庫あり","必要4個。6個×¥17より10個×¥5.80の方が安い","UNIT:C16","https://www.digikey.jp/ja/products/detail/murata-electronics/GRM188R72A103KA01D/3845635",""],
  ["コンデンサ","2.2uF 25V X7R 0805","Murata","GCM21BR71E225KA73L","490-4787-1-ND",1,4,10,43.80,"在庫あり","必要8個＋予備2個、10個価格","UNIT:C101 / ODOM:C1,C20,C21,C27","https://www.digikey.jp/ja/products/detail/murata-electronics/GCM21BR71E225KA73L/1641661",""],
  ["コンデンサ","10uF 10V X7R 0805","TDK","C2012X7R1A106K125AC","445-6857-1-ND",2,2,12,32.30,"在庫あり","必要10個＋予備2個、10個価格","UNIT:C202,C204 / ODOM:C3,C5","https://www.digikey.jp/ja/products/detail/tdk/C2012X7R1A106K125AC/2619198",""],
  ["抵抗","120R 1% 0603","YAGEO","RC0603FR-07120RL","311-120HRCT-ND",1,1,10,4.20,"在庫あり","6個を1個価格で買うより10個価格が安い","UNIT:R1 / ODOM:R1","https://www.digikey.jp/ja/products/detail/yageo/RC0603FR-07120RL/726920",""],
  ["抵抗","0R 0603","YAGEO","RC0603JR-070RL","311-0.0GRCT-ND",6,1,50,1.30,"在庫あり","必要25個。50個価格、予備25個","UNIT:R2,R3,R15-R18 / ODOM:R3","https://www.digikey.jp/ja/products/detail/yageo/RC0603JR-070RL/726675",""],
  ["抵抗","10k 1% 0603","YAGEO","RC0603FR-0710KL","311-10.0KHRCT-ND",1,1,10,4.20,"在庫あり","6個を1個価格で買うより10個価格が安い","UNIT:R4 / ODOM:R4","https://www.digikey.jp/ja/products/detail/yageo/RC0603FR-0710KL/726880",""],
  ["抵抗","33k 1% 0603","YAGEO","RC0603FR-0733KL","311-33.0KHRCT-ND",1,0,10,4.20,"在庫あり","必要4個、10個価格で予備6個","UNIT:R13","https://www.digikey.jp/ja/products/detail/yageo/RC0603FR-0733KL/730106",""],
  ["抵抗","22k 1% 0603","YAGEO","RC0603FR-0722KL","311-22.0KHRCT-ND",1,0,10,4.20,"在庫あり","必要4個、10個価格で予備6個","UNIT:R14","https://www.digikey.jp/ja/products/detail/yageo/RC0603FR-0722KL/727056",""],
  ["抵抗","1k 1% 0603","YAGEO","RC0603FR-071KL","311-1.00KHRCT-ND",4,4,25,3.12,"在庫あり","必要20個。25個価格の方が22個より安い","UNIT:R19-R22 / ODOM:R19-R22","https://www.digikey.jp/ja/products/detail/yageo/RC0603FR-071KL/729790",""],
  ["抵抗","100R 1% 0603","YAGEO","RC0603FR-07100RL","311-100HRCT-ND",0,6,10,4.20,"在庫あり","必要6個。10個価格の方が6個より安い","ODOM:R2,R5-R9","https://www.digikey.jp/ja/products/detail/yageo/RC0603FR-07100RL/726888",""],
  ["フィルタ","フェライト 600R@100MHz 0603","Murata","BLM18AG601SN1D","490-1014-1-ND",1,1,10,9.80,"在庫あり","6個を1個価格で買うより10個価格が安い","UNIT:FB1 / ODOM:FB1","https://www.digikey.jp/ja/products/detail/murata-electronics/BLM18AG601SN1D/584225",""],
  ["保護","CAN ESD SOT-23","Texas Instruments","ESD2CAN24DBZRQ1","296-ESD2CAN24DBZRQ1CT-ND",2,1,10,89.50,"在庫あり","必要9個＋予備1個、10個価格","UNIT:D1,D2 / ODOM:D1","https://www.digikey.jp/ja/products/detail/texas-instruments/ESD2CAN24DBZRQ1/16982262",""],
  ["保護","2ch ESD 5.5V SOT-23","Texas Instruments","ESDS452DBZR","296-ESDS452DBZRCT-ND",0,3,4,105.00,"在庫あり","必要3個＋予備1個。10個価格より総額が低い","ODOM:D2-D4","https://www.digikey.jp/ja/products/detail/texas-instruments/ESDS452DBZR/23065579","2ch双方向、5.5V standoff、3pF"],
  ["LED","緑 LED 0603","Lite-On","LTST-C190KGKT","160-1435-1-ND",2,2,12,17.50,"在庫あり","必要10個＋予備2個、10個価格","UNIT:D6,D8 / ODOM:D6,D8","https://www.digikey.jp/ja/products/detail/liteon/LTST-C190KGKT/386815",""],
  ["ダイオード","BAT54S-HF dual Schottky","Comchip Technology","BAT54S-HF","641-BAT54S-HFCT-ND",1,0,10,21.10,"在庫あり","必要4個。6個と10個の差額が1円のため10個","UNIT:D7","https://www.digikey.jp/ja/products/detail/comchip-technology/BAT54S-HF/10443826","onsemi BAT54SLT1GとDiotec BAT54Sが欠品のため、高在庫の同構成・同外形品へ置換"],
  ["LED","黄 LED 0603","Lite-On","LTST-C190KSKT","160-1437-1-ND",1,1,6,25.00,"在庫あり","必要5個＋予備1個。10個価格より総額が低い","UNIT:D9 / ODOM:D9","https://www.digikey.jp/ja/products/detail/liteon/LTST-C190KSKT/386819",""],
  ["LED","赤 LED 0603","Lite-On","LTST-C190KRKT","160-1436-1-ND",1,1,6,23.00,"在庫あり","必要5個＋予備1個。10個価格より総額が低い","UNIT:D10 / ODOM:D10","https://www.digikey.jp/ja/products/detail/liteon/LTST-C190KRKT/386816",""],
  ["コネクタ","JST GH 2極 横向き","JST","SM02B-GHS-TB","455-1564-1-ND",1,1,0,59.00,"手持ち","購入不要（必要5個）","UNIT:J1 / ODOM:J1","https://www.digikey.jp/ja/products/detail/jst-sales-america-inc/SM02B-GHS-TB/807832","手持ち在庫を使用"],
  ["コネクタ","JST GH 3極 横向き","JST","SM03B-GHS-TB","455-SM03B-GHS-TBCT-ND",4,1,20,53.20,"欠品/繰越注文","必要17個＋予備3個、10個価格。実在庫0のため納期確認必須","UNIT:J2-J5 / ODOM:J2","https://www.digikey.jp/ja/products/detail/jst-sales-america-inc/SM03B-GHS-TB/807787","2026-09-07確認時に在庫0、標準リードタイム16週。完全同一footprintの在庫品なし"],
  ["コネクタ","JST GH 6極 横向き","JST","SM06B-GHS-TB","455-1568-1-ND",1,0,0,83.00,"手持ち","購入不要（必要4個）","UNIT:J6","https://www.digikey.jp/ja/products/detail/jst-sales-america-inc/SM06B-GHS-TB/807790","手持ち在庫を使用"],
  ["コネクタ","JST GH 6極 垂直","JST","BM06B-GHS-TBT","455-BM06B-GHS-TBTCT-ND",1,1,0,78.00,"手持ち","購入不要（必要5個）","UNIT:J7 / ODOM:J8","https://www.digikey.jp/ja/products/detail/jst-sales-america-inc/BM06B-GHS-TBT/807804","手持ち在庫を使用"],
  ["コネクタ","JST XH 4極 垂直","JST","B4B-XH-AM","455-B4B-XH-AM-ND",0,3,4,30.00,"在庫あり","必要3個＋予備1個","ODOM:J4-J6","https://www.digikey.jp/ja/products/detail/jst-sales-america-inc/B4B-XH-AM/1651035",""],
  ["コネクタ","JST XH 8極 垂直","JST","B8B-XH-AM","455-2232-ND",0,1,2,52.00,"在庫あり","必要1個＋予備1個","ODOM:J7","https://www.digikey.jp/ja/products/detail/jst-sales-america-inc/B8B-XH-AM/1651030",""],
  ["スイッチ","SPDT スライドスイッチ","C&K/Littelfuse","JS102011SAQN","401-1999-1-ND",1,1,6,150.00,"在庫あり","必要5個＋予備1個","UNIT:SW1 / ODOM:SW1","https://www.digikey.jp/ja/products/detail/c-k/JS102011SAQN/1640095",""],
  ["スイッチ","3極 DIPスイッチ SMD","Same Sky","DS04-254-1-03BK-SMT","2223-DS04-254-1-03BK-SMT-ND",1,1,6,204.00,"在庫あり","必要5個＋予備1個。10個価格より総額が低い","UNIT:SW3 / ODOM:SW3","https://www.digikey.jp/ja/products/detail/same-sky-formerly-cui-devices/DS04-254-1-03BK-SMT/11310852","A6S-3104-H在庫0。pad中心列間8.9mm、縦pitch2.54mm、推奨pad 1.1×1.5mmが既存KiCad footprintと一致"],
  ["電源IC","Ideal diode 1.5A SC-70-6","Texas Instruments","LM66100DCKT","296-53540-1-ND",1,1,6,160.00,"在庫あり","必要5個＋予備1個。10個価格より6個の総額が安い","UNIT:U1 / ODOM:U5","https://www.digikey.jp/ja/products/detail/texas-instruments/LM66100DCKT/10273182","DCKRと同一IC・同一SC-70-6、梱包数量だけ異なる"],
  ["電源IC","3.3V LDO SOT-223","Texas Instruments","TLV76133DCYR","296-TLV76133DCYRCT-ND",1,1,6,98.00,"在庫あり","必要5個＋予備1個。10個価格より6個の総額が安い","UNIT:U2 / ODOM:U2","https://www.digikey.jp/ja/products/detail/texas-instruments/TLV76133DCYR/18716472","TLV1117LV33DCYR生産中止のため、同一ピン配置・セラミック安定品へ置換"],
  ["通信IC","CAN transceiver with VIO","Texas Instruments","TCAN1051VDRQ1","296-44228-1-ND",2,1,10,318.80,"在庫あり","必要9個＋予備1個、10個価格","UNIT:U3,U5 / ODOM:U4","https://www.digikey.jp/ja/products/detail/texas-instruments/TCAN1051VDRQ1/6052110",""],
  ["ロジックIC","Dual Schmitt buffer SOT-23-6","Texas Instruments","SN74LVC2G17DBVT","296-26621-1-ND",0,3,4,201.00,"在庫あり","必要3個＋予備1個。10個価格より4個の総額が安い","ODOM:U3,U7,U9","https://www.digikey.jp/ja/products/detail/texas-instruments/SN74LVC2G17DBVT/2255079","DBVRと同一IC・同一SOT-23-6、梱包数量だけ異なる"],
  ["水晶","8MHz 8pF 500R 3225-4pad","Fox Electronics","FC3BAEBDI8.0-T1","631-FC3BAEBDI8.0-T1CT-ND",1,1,6,98.00,"在庫あり","必要5個＋予備1個。10個価格より6個の総額が安い","UNIT:Y1 / ODOM:Y1","https://www.digikey.jp/ja/products/detail/fox-electronics/FC3BAEBDI8-0-T1/21293019","ECS元品欠品。8MHz、CL=8pF、ESR=500Ω、3225-4pad一致。AEC-Q200"],
  ["手持ち","Drive MCU LQFP64","STMicroelectronics","STM32G474RET6","497-STM32G474RET6-ND",1,0,0,0,"手持ち10個","購入不要（4個使用）","UNIT:U4","https://www.digikey.jp/ja/products/detail/stmicroelectronics/STM32G474RET6/10326780",""],
  ["手持ち","Odometry MCU LQFP64","STMicroelectronics","STM32F405RGT6","497-STM32F405RGT6-ND",0,1,0,0,"研究室在庫","購入不要（1個使用）","ODOM:U1","https://www.digikey.jp/ja/products/detail/stmicroelectronics/STM32F405RGT6/1851915",""],
  ["手持ち","IMU 8pin breakout","TDK InvenSense","ICM-42688-P breakout","",0,1,0,0,"購入済み","基板J7へ接続する別モジュール","ODOM:J7接続","","基板実装部品ではない"],
];

// ODOM board and its parts are already ordered. The current cart is only for four drive boards.
// Each entry is chosen from the published quantity tiers with a practical assembly spare.
const driveOnlySelections = {
  "C0603C104K5RACTU": [60, 7.96, "必要52個＋予備8個。50個価格を適用"],
  "CL10C100JB8NNNC": [10, 6.20, "必要8個＋予備2個。10個価格を適用"],
  "GRM21BZ71E475KE15K": [5, 48.00, "必要4個＋予備1個。10個購入より総額が低い"],
  "C1608X7R1E105K080AB": [10, 17.80, "必要8個＋予備2個。10個価格を適用"],
  "C1608C0G1H103J080AA": [10, 22.30, "必要4個。少数購入より10個の総額が安い"],
  "GRM188R72A103KA01D": [10, 5.80, "必要4個。少数購入より10個の総額が安い"],
  "GCM21BR71E225KA73L": [5, 73.00, "必要4個＋予備1個。10個購入より総額が低い"],
  "C2012X7R1A106K125AC": [10, 32.30, "必要8個＋予備2個。10個価格を適用"],
  "RC0603FR-07120RL": [10, 4.20, "必要4個。少数購入より10個の総額が安い"],
  "RC0603JR-070RL": [25, 1.48, "必要24個＋予備1個。25個価格を適用"],
  "RC0603FR-0710KL": [10, 4.20, "必要4個。少数購入より10個の総額が安い"],
  "RC0603FR-0733KL": [10, 4.20, "必要4個。少数購入より10個の総額が安い"],
  "RC0603FR-0722KL": [10, 4.20, "必要4個。少数購入より10個の総額が安い"],
  "RC0603FR-071KL": [25, 3.12, "必要16個＋予備9個。20個購入より25個の総額が安い"],
  "BLM18AG601SN1D": [5, 17.00, "必要4個＋予備1個。10個購入より総額が低い"],
  "ESD2CAN24DBZRQ1": [10, 89.50, "必要8個＋予備2個。10個価格を適用"],
  "LTST-C190KGKT": [10, 17.50, "必要8個＋予備2個。10個価格を適用"],
  "BAT54S-HF": [10, 21.10, "必要4個。6個購入との差額1円なので10個"],
  "LTST-C190KSKT": [5, 25.00, "必要4個＋予備1個"],
  "LTST-C190KRKT": [5, 23.00, "必要4個＋予備1個"],
  "SM03B-GHS-TB": [20, 53.20, "必要16個＋予備4個。10個価格。欠品のため納期確認必須"],
  "JS102011SAQN": [5, 150.00, "必要4個＋予備1個"],
  "DS04-254-1-03BK-SMT": [5, 204.00, "必要4個＋予備1個"],
  "LM66100DCKT": [5, 160.00, "必要4個＋予備1個"],
  "TLV76133DCYR": [5, 98.00, "必要4個＋予備1個"],
  "TCAN1051VDRQ1": [10, 318.80, "必要8個＋予備2個。10個価格を適用"],
  "FC3BAEBDI8.0-T1": [5, 98.00, "必要4個＋予備1個"],
};

for (const p of parts) {
  const selection = driveOnlySelections[p[3]];
  if (selection) {
    p[7] = selection[0];
    p[8] = selection[1];
    p[10] = selection[2];
  } else if (p[5] === 0) {
    p[7] = 0;
    p[8] = 0;
    p[9] = "ODOM発注済み";
    p[10] = "ODOM用は発注済みのため今回購入なし";
  }
}

// Stock and price-break snapshot used by the detailed selection audit.
// prices = [1, 10, 25, 50, 100] unit prices in JPY before tax; null means no published tier at that quantity.
const audit = {
  "C0603C104K5RACTU": {stock:7005521, prices:[22,11.60,null,7.96,6.87], footprint:"C_0603_1608Metric", electrical:"100nF ±10%, 50V, X7R", fit:"一致", decision:"採用", note:"64個必要。100個価格で十分な実装予備を確保"},
  "CL10C100JB8NNNC": {stock:321481, prices:[17,6.20,null,4.12,3.53], footprint:"C_0603_1608Metric", electrical:"10pF ±5%, 50V, C0G/NP0", fit:"一致", decision:"採用", note:"HSE負荷容量。誘電体と容量を変更しない"},
  "GRM21BZ71E475KE15K": {stock:10502, prices:[48,28.40,null,20.66,18.23], footprint:"C_0805_2012Metric", electrical:"4.7uF ±10%, 25V, X7R", fit:"一致", decision:"採用", note:"6個より10個の総額が安い"},
  "C1608X7R1E105K080AB": {stock:259236, prices:[32,17.80,null,12.58,10.98], footprint:"C_0603_1608Metric", electrical:"1uF ±10%, 25V, X7R", fit:"一致", decision:"採用（置換）", note:"TMK107B7105KA-T在庫0。容量・誘電体・電圧・外形一致"},
  "C1608C0G1H103J080AA": {stock:95498, prices:[38,22.30,null,16.08,14.13], footprint:"C_0603_1608Metric", electrical:"10nF ±5%, 50V, C0G/NP0", fit:"一致", decision:"採用（置換）", note:"仕様を維持し、DigiKey在庫と数量価格を確認できる品へ変更"},
  "GRM188R72A103KA01D": {stock:419642, prices:[17,5.80,null,3.86,3.29], footprint:"C_0603_1608Metric", electrical:"10nF ±10%, 100V, X7R", fit:"一致", decision:"採用", note:"6個より10個の総額が安い"},
  "GCM21BR71E225KA73L": {stock:252899, prices:[73,43.80,null,32.44,28.93], footprint:"C_0805_2012Metric", electrical:"2.2uF ±10%, 25V, X7R", fit:"一致", decision:"採用", note:"F405 VCAPを含む。必要8個＋予備2個"},
  "C2012X7R1A106K125AC": {stock:344771, prices:[54,32.30,null,23.52,20.83], footprint:"C_0805_2012Metric", electrical:"10uF ±10%, 10V, X7R", fit:"一致", decision:"採用", note:"必要10個＋予備2個"},
  "RC0603FR-07120RL": {stock:19927, prices:[17,4.20,3.20,2.54,2.07], footprint:"R_0603_1608Metric", electrical:"120Ω ±1%, 0.1W", fit:"一致", decision:"採用", note:"CAN終端抵抗"},
  "RC0603JR-070RL": {stock:6131058, prices:[17,1.90,1.48,1.30,1.12], footprint:"R_0603_1608Metric", electrical:"0Ω jumper", fit:"一致", decision:"採用", note:"必要25個。50個で予備25個"},
  "RC0603FR-0710KL": {stock:2912992, prices:[17,4.20,3.12,2.50,2.03], footprint:"R_0603_1608Metric", electrical:"10kΩ ±1%, 0.1W", fit:"一致", decision:"採用", note:"必要5個。10個価格"},
  "RC0603FR-0733KL": {stock:365410, prices:[17,4.20,3.16,2.52,2.06], footprint:"R_0603_1608Metric", electrical:"33kΩ ±1%, 0.1W", fit:"一致", decision:"採用", note:"必要4個。10個価格"},
  "RC0603FR-0722KL": {stock:4633, prices:[17,4.20,3.12,2.50,2.03], footprint:"R_0603_1608Metric", electrical:"22kΩ ±1%, 0.1W", fit:"一致", decision:"採用", note:"必要4個。10個価格"},
  "RC0603FR-071KL": {stock:4068534, prices:[17,4.20,3.12,2.50,2.03], footprint:"R_0603_1608Metric", electrical:"1kΩ ±1%, 0.1W", fit:"一致", decision:"採用", note:"必要20個。25個価格"},
  "RC0603FR-07100RL": {stock:1142640, prices:[17,4.20,3.12,2.50,2.03], footprint:"R_0603_1608Metric", electrical:"100Ω ±1%, 0.1W", fit:"一致", decision:"採用", note:"必要6個。10個価格"},
  "BLM18AG601SN1D": {stock:1716062, prices:[17,9.80,8.52,7.66,6.87], footprint:"L_0603_1608Metric", electrical:"600Ω@100MHz, 500mA, DCR≤0.38Ω", fit:"一致", decision:"採用", note:"VDDAフィルタ"},
  "ESD2CAN24DBZRQ1": {stock:255314, prices:[145,89.50,null,65.62,57.84], footprint:"SOT-23", electrical:"2ch双方向, 24V standoff, 3pF", fit:"一致", decision:"採用", note:"CAN用AEC-Q101品"},
  "ESDS452DBZR": {stock:2153, prices:[105,65,null,47.24,41.47], footprint:"SOT-23", electrical:"2ch双方向, 5.5V standoff, 3pF", fit:"一致", decision:"採用", note:"AMT102 A/B入力用。必要3個＋予備1個"},
  "LTST-C190KGKT": {stock:1893679, prices:[25,17.50,null,null,12.05], footprint:"LED_0603_1608Metric", electrical:"緑, Vf typ 2.15V, 20mA test", fit:"一致", decision:"採用", note:"必要10個＋予備2個"},
  "BAT54S-HF": {stock:306288, prices:[35,21.10,null,null,13.03], footprint:"SOT-23", electrical:"dual series, 30V, 200mA/diode", fit:"一致", decision:"採用（置換）", note:"onsemi/Diotec品欠品。Comchip公式DSで直列2素子構成とpin配列を照合"},
  "LTST-C190KSKT": {stock:361422, prices:[25,17.30,null,null,11.89], footprint:"LED_0603_1608Metric", electrical:"黄, Vf typ 2.1V, 20mA test", fit:"一致", decision:"採用", note:"必要5個＋予備1個"},
  "LTST-C190KRKT": {stock:770130, prices:[23,16.30,null,null,11.23], footprint:"LED_0603_1608Metric", electrical:"赤, Vf typ 2.0V, 20mA test", fit:"一致", decision:"採用", note:"必要5個＋予備1個"},
  "SM02B-GHS-TB": {stock:null, prices:[59,null,null,null,null], footprint:"JST_GH_SM02B-GHS-TB Horizontal", electrical:"2極, 1.25mm, 1A/50V", fit:"現物手持ち", decision:"購入不要", note:"必要5個を現物で確認"},
  "SM03B-GHS-TB": {stock:0, prices:[62,52.10,null,null,44.20], footprint:"JST_GH_SM03B-GHS-TB Horizontal", electrical:"3極, 1.25mm, 1A/50V", fit:"専用品・一致", decision:"繰越注文", note:"在庫0。向き違い代替は既存PCBに不適合"},
  "SM06B-GHS-TB": {stock:null, prices:[83,null,null,null,null], footprint:"JST_GH_SM06B-GHS-TB Horizontal", electrical:"6極, 1.25mm, 1A/50V", fit:"現物手持ち", decision:"購入不要", note:"必要4個を現物で確認"},
  "BM06B-GHS-TBT": {stock:null, prices:[78,null,null,null,null], footprint:"JST_GH_BM06B-GHS-TBT Vertical", electrical:"6極, 1.25mm, 1A/50V", fit:"現物手持ち", decision:"購入不要", note:"必要5個を現物で確認"},
  "B4B-XH-AM": {stock:2415, prices:[30,25.60,null,null,21.71], footprint:"JST_XH_B4B-XH-AM Vertical THT", electrical:"4極, 2.50mm, 3A/250V", fit:"一致", decision:"採用", note:"必要3個＋予備1個"},
  "B8B-XH-AM": {stock:3610, prices:[52,44.30,null,null,37.55], footprint:"JST_XH_B8B-XH-AM Vertical THT", electrical:"8極, 2.50mm, 3A/250V", fit:"一致", decision:"採用", note:"必要1個＋予備1個"},
  "JS102011SAQN": {stock:56976, prices:[150,128.10,119.24,null,106.37], footprint:"DifferentialSwerve:JS102011SAQN", electrical:"SPDT ON-ON, 300mA@6VDC", fit:"専用footprint一致", decision:"採用", note:"CAN終端切替。必要5個＋予備1個"},
  "DS04-254-1-03BK-SMT": {stock:1546, prices:[204,170.50,null,149.72,141.29], footprint:"Omron A6S 3-pole footprint (8.9mm row)", electrical:"3極SPST, 25mA@24VDC", fit:"ランド一致", decision:"採用（置換）", note:"推奨pad外端10.4/内端7.4mm→中心列間8.9mm、縦2.54mm。既存pad 1.5×1.1mmと一致"},
  "LM66100DCKT": {stock:1456, prices:[160,114.30,103,null,90.62], footprint:"SOT-363 / SC-70-6", electrical:"1.5–5.5V, 1.5A ideal diode", fit:"一致", decision:"採用", note:"DCKR/DCKTは梱包差のみ"},
  "TLV76133DCYR": {stock:673, prices:[98,68.90,61.56,null,53.59], footprint:"SOT-223-3, tab=pin2", electrical:"3.3V fixed, 1A, Vin max 18V", fit:"pin 1=GND, 2/tab=OUT, 3=IN", decision:"採用（置換）", note:"旧TLV1117LV33DCYRと実装pin配置一致。セラミック出力安定"},
  "TCAN1051VDRQ1": {stock:2643, prices:[429,318.80,291.32,null,261.07], footprint:"SOIC-8 3.9×4.9mm P1.27", electrical:"CAN FD 2Mbps, VIO, 4.5–5.5V", fit:"一致", decision:"採用", note:"必要9個＋予備1個、10個価格"},
  "SN74LVC2G17DBVT": {stock:24627, prices:[201,145.60,131.68,null,116.47], footprint:"SOT-23-6", electrical:"dual Schmitt buffer, 1.65–5.5V", fit:"一致", decision:"採用", note:"DBVR/DBVTは梱包差のみ"},
  "FC3BAEBDI8.0-T1": {stock:178, prices:[98,85.20,80.44,77.16,73.97], footprint:"Crystal 3225-4Pin 3.2×2.5mm", electrical:"8MHz, CL=8pF, ESR max 500Ω", fit:"一致", decision:"採用（置換）", note:"ECS元品欠品。周波数・CL・ESR・外形一致"},
  "STM32G474RET6": {stock:null, prices:[null,null,null,null,null], footprint:"LQFP-64 10×10mm P0.5", electrical:"手持ち", fit:"一致", decision:"購入不要", note:"4個使用"},
  "STM32F405RGT6": {stock:null, prices:[null,null,null,null,null], footprint:"LQFP-64 10×10mm P0.5", electrical:"研究室在庫", fit:"一致", decision:"購入不要", note:"1個使用"},
  "ICM-42688-P breakout": {stock:null, prices:[null,null,null,null,null], footprint:"別モジュール（基板J7へ接続）", electrical:"購入済み", fit:"基板実装外", decision:"購入不要", note:"コネクタ接続するモジュール"},
};

const workbook = Workbook.create();
const summary = workbook.worksheets.add("サマリー");
const order = workbook.worksheets.add("統合発注BOM");
const drive = workbook.worksheets.add("駆動基板_4枚");
const odom = workbook.worksheets.add("ODOM基板_1枚");
const notes = workbook.worksheets.add("判断根拠と注意");
const auditSheet = workbook.worksheets.add("在庫価格Footprint監査");

const navy = "#17365D";
const blue = "#D9EAF7";
const pale = "#F4F7FA";
const orange = "#FCE4D6";
const green = "#E2F0D9";
const gray = "#E7E6E6";
const border = { preset: "all", style: "thin", color: "#C8D0D8" };

function setTitle(sheet, range, text) {
  const cell = sheet.getRange(range.split(":")[0]);
  cell.values = [[text]];
  sheet.getRange(range).format.fill = navy;
  sheet.getRange(range).format.font = { bold: true, color: "#FFFFFF", size: 16 };
  sheet.getRange("1:1").format.rowHeight = 30;
  cell.format.verticalAlignment = "center";
}

function styleHeader(range) {
  range.format.fill = navy;
  range.format.font = { bold: true, color: "#FFFFFF" };
  range.format.wrapText = true;
  range.format.verticalAlignment = "center";
  range.format.borders = border;
}

for (const s of [summary, order, drive, odom, notes, auditSheet]) {
  s.showGridLines = false;
  s.freezePanes.freezeRows(1);
}

setTitle(summary, "A1:H1", "Differential Swerve — 駆動基板 DigiKey調達サマリー");
summary.mergeCells("A1:H1");
summary.getRange("A3:B10").values = [
  ["価格・在庫確認日", "2026-09-07 (JST)"],
  ["今回の発注対象", `駆動モジュール基板 ${driveBoards}枚（実機3＋丸ごと予備1）。ODOM基板は発注済み`],
  ["購入行数", null],
  ["税抜部品概算", null],
  ["消費税10%参考", null],
  ["税込概算", null],
  ["送料", "DigiKey通常商品6,000円以上のため無料見込み（確定はカート）"],
  ["欠品行", null],
];
summary.getRange("B5").formulas = [["=COUNTIF('統合発注BOM'!$I$4:$I$200,\">0\")"]];
summary.getRange("B6").formulas = [["=ROUND(SUM('統合発注BOM'!$L$4:$L$200),2)"]];
summary.getRange("B7").formulas = [["=ROUND(B6*10%,2)"]];
summary.getRange("B8").formulas = [["=ROUND(B6+B7,2)"]];
summary.getRange("B10").formulas = [["=COUNTIF('統合発注BOM'!$M$4:$M$200,\"欠品/繰越注文\")"]];
summary.getRange("A3:A10").format.fill = blue;
summary.getRange("A3:A10").format.font = { bold: true, color: "#17365D" };
summary.getRange("A3:B10").format.borders = border;
summary.getRange("B6:B8").setNumberFormat("¥#,##0.00");
summary.getRange("A12:H12").values = [["重要", "対象", "状態", "対応", "", "", "", ""]];
styleHeader(summary.getRange("A12:H12"));
summary.mergeCells("D13:H13"); summary.mergeCells("D14:H14"); summary.mergeCells("D15:H15"); summary.mergeCells("D16:H16");
summary.getRange("A13:D16").values = [
  ["要確認","SM03B-GHS-TB","欠品/繰越注文","DigiKeyカートで入荷日を確認。代替はフットプリントが変わるため未採用"],
  ["置換済","1uF / 10nF C0G / BAT54S / LDO / DIP / 水晶","在庫品へ変更","容量・定格・誘電体・外形またはpin配置を照合済み"],
  ["発注済み","ODOM基板1枚分","今回の購入数は0","内訳シートは組立確認用として残す"],
  ["手持ち","GHコネクタ","2極横・6極横・6極垂直","SM02B、SM06B、BM06BをDigiKey発注から除外"],
];
summary.getRange("A13:H16").format.borders = border;
summary.getRange("A13:H13").format.fill = orange;
summary.getRange("A14:H16").format.fill = green;
summary.getRange("A18:H21").values = [
  ["使い方","1","統合発注BOMのオレンジ行（SM03）の納期をカートで確認","","","","", ""],
  ["","2","CSVをDigiKey BOM Managerへアップロード","","","","", ""],
  ["","3","税込概算・在庫・価格を最終確認して発注","","","","", ""],
  ["","4","ODOM発注済み品と手持ちMCU・GHコネクタは発注対象外","","","","", ""],
];
summary.mergeCells("C18:H18"); summary.mergeCells("C19:H19"); summary.mergeCells("C20:H20"); summary.mergeCells("C21:H21");
summary.getRange("A18:B21").format.fill = pale;
summary.getRange("A18:H21").format.borders = border;
summary.getRange("A1:H25").format.wrapText = true;
summary.getRange("A1:H25").format.verticalAlignment = "center";
summary.getRange("A:A").format.columnWidth = 18;
summary.getRange("B:B").format.columnWidth = 30;
summary.getRange("C:C").format.columnWidth = 26;
summary.getRange("D:H").format.columnWidth = 18;

setTitle(order, "A1:Q1", "今回発注BOM — 駆動モジュール基板4枚");
order.mergeCells("A2:Q2");
order.getRange("A2").values = [["今回の購入数量は駆動基板4枚分のみ。ODOMは発注済み。価格は税抜JPY。URLは価格/在庫の再確認用。"]];
order.getRange("A2").format.fill = blue;
order.getRange("A2").format.wrapText = true;
const headers = ["分類","品名/仕様","メーカー","メーカー品番","DigiKey品番","駆動/枚","ODOM/枚(発注済)","今回必要数","今回発注数","駆動分余剰","単価(税抜)","小計(税抜)","在庫状態","数量判断","使用箇所","参照URL","備考"];
order.getRange("A3:Q3").values = [headers];
styleHeader(order.getRange("A3:Q3"));
const orderValues = parts.map(p => [p[0],p[1],p[2],p[3],p[4],p[5],p[6],null,p[7],null,p[8],null,p[9],p[10],p[11],p[12],p[13]]);
order.getRange(`A4:Q${3 + orderValues.length}`).values = orderValues;
for (let r = 4; r <= 3 + orderValues.length; r++) {
  order.getRange(`H${r}`).formulas = [[`=F${r}*${driveBoards}`]];
  order.getRange(`J${r}`).formulas = [[`=IF(I${r}=0,0,I${r}-H${r})`]];
  order.getRange(`L${r}`).formulas = [[`=ROUND(I${r}*K${r},2)`]];
}
const orderLast = 3 + orderValues.length;
order.getRange(`A4:Q${orderLast}`).format.borders = border;
order.getRange(`F4:J${orderLast}`).setNumberFormat("0");
order.getRange(`K4:L${orderLast}`).setNumberFormat("¥#,##0.00");
order.getRange(`A4:Q${orderLast}`).format.wrapText = true;
order.getRange(`A4:Q${orderLast}`).format.verticalAlignment = "center";
for (let r = 4; r <= orderLast; r++) {
  if (parts[r-4][9].includes("欠品")) order.getRange(`A${r}:Q${r}`).format.fill = orange;
  else if (parts[r-4][0] === "手持ち" || parts[r-4][9].includes("手持ち") || parts[r-4][9].includes("発注済み")) order.getRange(`A${r}:Q${r}`).format.fill = gray;
  else if (r % 2 === 0) order.getRange(`A${r}:Q${r}`).format.fill = "#F8FAFC";
}
order.freezePanes.freezeRows(3);
order.freezePanes.freezeColumns(5);
order.getRange("3:3").format.rowHeight = 38;
order.getRange(`4:${orderLast}`).format.rowHeight = 32;
const widths = [12,30,20,28,29,9,9,9,9,9,13,14,16,35,38,42,32];
widths.forEach((w, i) => order.getRangeByIndexes(0, i, orderLast, 1).format.columnWidth = w);

function fillBoardSheet(sheet, title, perIndex, count) {
  setTitle(sheet, "A1:H1", title);
  sheet.getRange("A2:H2").values = [["分類","品名/仕様","メーカー品番","使用箇所","1枚あたり","枚数","合計必要数","調達区分"]];
  styleHeader(sheet.getRange("A2:H2"));
  const refPrefix = perIndex === 5 ? "UNIT:" : "ODOM:";
  const filtered = parts.filter(p => p[perIndex] > 0).map(p => {
    const boardRef = p[11].split(" / ").find(ref => ref.startsWith(refPrefix)) ?? p[11];
    const procurement = perIndex === 6 ? "発注済み" : ((p[0] === "手持ち" || p[7] === 0) ? "手持ち" : "今回発注");
    return [p[0],p[1],p[3],boardRef,p[perIndex],count,null,procurement];
  });
  const last = 2 + filtered.length;
  sheet.getRange(`A3:H${last}`).values = filtered;
  for (let r = 3; r <= last; r++) sheet.getRange(`G${r}`).formulas = [[`=E${r}*F${r}`]];
  sheet.getRange(`A3:H${last}`).format.borders = border;
  sheet.getRange(`A3:H${last}`).format.wrapText = true;
  sheet.getRange(`A3:H${last}`).format.verticalAlignment = "center";
  sheet.getRange(`E3:G${last}`).setNumberFormat("0");
  sheet.getRange("2:2").format.rowHeight = 32;
  sheet.getRange(`3:${last}`).format.rowHeight = 24;
  sheet.freezePanes.freezeRows(2);
  const ws = [12,32,30,42,12,9,13,14];
  ws.forEach((w,i) => sheet.getRangeByIndexes(0,i,last,1).format.columnWidth = w);
}
fillBoardSheet(drive, "駆動モジュール基板 — 4枚分（実機3＋予備1）", 5, driveBoards);
fillBoardSheet(odom, "ODOM基板 — 1枚分（発注済み・組立確認用）", 6, odomBoards);

setTitle(notes, "A1:D1", "数量判断・置換・組立時の注意");
notes.getRange("A3:D3").values = [["項目","判断","理由","次の確認"]];
styleHeader(notes.getRange("A3:D3"));
notes.getRange("A4:D17").values = [
  ["基板枚数","今回発注は駆動4枚のみ","駆動は3ユニット実装＋基板単位の完全予備1枚。ODOMは発注済み","枚数を変える場合は今回発注BOMのF列と発注数を再調整"],
  ["受動部品","必要数＋2〜6個、安価品は価格境界まで","紛失・はんだ不良・再作業を吸収","0603は向き/定数を仕分けしてから実装"],
  ["高価なIC/スイッチ","基本は必要数＋1個","死蔵を避けながら初期不良と実装ミスを1回吸収","開封時にロットと向きを確認"],
  ["LM66100DCKT","採用","DCKRとDCKTは同じLM66100・SC-70-6で梱包数量だけ違う","DigiKeyカットテープ品番を使用"],
  ["SN74LVC2G17DBVT","採用","DBVRとDBVTは同じTI品・SOT-23-6で梱包数量だけ違う","1番ピンを確認"],
  ["FC3BAEBDI8.0-T1","採用","元ECS品欠品。8MHz、CL=8pF、ESR=500R、3225 4padが一致","初号機で発振開始と周波数を確認"],
  ["BAT54S-HF (Comchip)","採用","onsemi/Diotec品欠品。直列2ダイオード、30V、200mA、SOT-23、同一ピン構成","初号機でD7向きとクランプ動作を確認"],
  ["TLV76133DCYR","採用","TLV1117LV33DCYR生産中止。SOT-223同一ピン配置、1A、セラミック出力コンデンサ対応","初号機で3.3V、温度、負荷変動を確認"],
  ["DS04-254-1-03BK-SMT","採用","A6S-3104-H在庫0。推奨ランドの列間8.9mm・縦pitch 2.54mm・pad 1.5x1.1mmが既存KiCad footprintと一致","シルクはA6S名称のままだが実装ランドは一致。ON方向を実装前に確認"],
  ["SM03B-GHS-TB","繰越注文","確認時DigiKey在庫0。形状違いの代替は基板に合わないため未採用","発注前にカート納期確認。急ぐ場合は別在庫元を探す"],
  ["ODOM DNP","C15,C17,C23-C26は購入・実装しない","KiCad回路図でDNP指定","組立指示にもDNPを残す"],
  ["発注対象外","ODOM一式、STM32G474RET6×4、GH 2極横/6極横/6極垂直（必要数を満たす前提）","発注済み/手持ちのためCSVから除外","駆動用GHは必要数4/4/4個を満たすか現物確認"],
  ["価格","DigiKey Japan税抜JPY、2026-09-07時点","価格と在庫は変動する","カート取込後に最終総額を再確認"],
  ["BOM範囲","基板実装部品のみ","GH/XH相手側ハウジング・圧着端子・ケーブル、PCB、ステンシル、はんだ材料は含めない","ハーネス長と本数の確定後に別BOM化"],
];
notes.getRange("A4:D17").format.borders = border;
notes.getRange("A4:D17").format.wrapText = true;
notes.getRange("A4:D17").format.verticalAlignment = "top";
notes.getRange("4:17").format.rowHeight = 34;
notes.getRange("A:A").format.columnWidth = 24;
notes.getRange("B:B").format.columnWidth = 26;
notes.getRange("C:C").format.columnWidth = 52;
notes.getRange("D:D").format.columnWidth = 46;
notes.freezePanes.freezeRows(3);

setTitle(auditSheet, "A1:S1", "在庫・数量価格・フットプリント監査");
auditSheet.mergeCells("A2:S2");
auditSheet.getRange("A2").values = [["今回発注は駆動基板4枚分のみ。ODOMは発注済み。DigiKey Japanの在庫・税抜JPYは2026-09-07確認。"]];
auditSheet.getRange("A2").format.fill = blue;
auditSheet.getRange("A2").format.wrapText = true;
const auditHeaders = ["分類","使用箇所","メーカー品番","DigiKey品番","今回必要数","今回発注数","駆動分余剰","在庫数","1個単価","10個単価","25個単価","50個単価","100個単価","採用単価","実装フットプリント","Footprint照合","電気仕様照合","選定結果","根拠・注意 / 参照URL"];
auditSheet.getRange("A3:S3").values = [auditHeaders];
styleHeader(auditSheet.getRange("A3:S3"));
const auditRows = parts.map(p => {
  const a = audit[p[3]] ?? {stock:null, prices:[null,null,null,null,null], footprint:"未登録", electrical:"未登録", fit:"要確認", decision:"要確認", note:"監査情報なし"};
  const needed = p[5] * driveBoards;
  const decision = p[5] === 0 ? "ODOM発注済み" : a.decision;
  return [p[0], p[11], p[3], p[4], needed, p[7], p[7] === 0 ? 0 : p[7] - needed, a.stock, ...a.prices, p[8], a.footprint, a.fit, a.electrical, decision, `${a.note}\n${p[12]}`];
});
const auditLast = 3 + auditRows.length;
auditSheet.getRange(`A4:S${auditLast}`).values = auditRows;
auditSheet.getRange(`A4:S${auditLast}`).format.borders = border;
auditSheet.getRange(`A4:S${auditLast}`).format.wrapText = true;
auditSheet.getRange(`A4:S${auditLast}`).format.verticalAlignment = "top";
auditSheet.getRange(`E4:H${auditLast}`).setNumberFormat("#,##0");
auditSheet.getRange(`I4:N${auditLast}`).setNumberFormat("¥#,##0.00");
auditSheet.getRange("3:3").format.rowHeight = 38;
auditSheet.getRange(`4:${auditLast}`).format.rowHeight = 42;
auditSheet.freezePanes.freezeRows(3);
auditSheet.freezePanes.freezeColumns(4);
const auditWidths = [12,38,29,30,9,9,9,13,12,12,12,12,12,12,34,20,34,18,60];
auditWidths.forEach((w, i) => auditSheet.getRangeByIndexes(0, i, auditLast, 1).format.columnWidth = w);
for (let r = 4; r <= auditLast; r++) {
  const result = auditRows[r - 4][17];
  if (result === "繰越注文") auditSheet.getRange(`A${r}:S${r}`).format.fill = orange;
  else if (result === "購入不要" || result === "ODOM発注済み") auditSheet.getRange(`A${r}:S${r}`).format.fill = gray;
  else if (String(result).includes("置換")) auditSheet.getRange(`A${r}:S${r}`).format.fill = green;
  else if (r % 2 === 0) auditSheet.getRange(`A${r}:S${r}`).format.fill = "#F8FAFC";
}

// DigiKey BOM Manager upload CSV: omit parts already on hand.
const csvRows = [["DigiKey Part Number","Quantity","Customer Reference"]];
for (const p of parts) {
  if (p[7] <= 0 || !p[4]) continue;
  const unitRef = p[11].split(" / ").find(ref => ref.startsWith("UNIT:")) ?? p[11];
  csvRows.push([p[4], String(p[7]), unitRef]);
}
const csv = csvRows.map(row => row.map(v => `"${String(v).replaceAll('"','""')}"`).join(",")).join("\r\n") + "\r\n";
const csvPath = path.join(procurementDir, "digikey-bom-drive4-only-2026-09-07.csv");
await fs.writeFile(csvPath, csv, "utf8");

workbook.recalculate();
const inspection = await workbook.inspect({ kind: "table", sheetId: "サマリー", range: "A1:H21", include: "values,formulas", maxChars: 5000, tableMaxRows: 21, tableMaxCols: 8 });
console.log(inspection.ndjson ?? inspection);
const errorScan = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, maxChars: 5000 });
console.log(errorScan.ndjson ?? errorScan);

for (const sheetName of ["サマリー","統合発注BOM","駆動基板_4枚","ODOM基板_1枚","判断根拠と注意","在庫価格Footprint監査"]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(qaDir, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const out = await SpreadsheetFile.exportXlsx(workbook);
const xlsxPath = path.join(artifactDir, "Differential-Swerve_DigiKey-BOM_Drive4_2026-09-07.xlsx");
await out.save(xlsxPath);
console.log(JSON.stringify({ xlsxPath, csvPath, qaDir }));
