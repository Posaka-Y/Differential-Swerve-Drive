# Project progress

プロジェクト全体の進捗ログ。セッション終了時に新しいエントリを**上に**追記する。
ファームウェア固有の進捗は `firmware/PROGRESS.md` に書く。

記載フォーマット:

```text
## YYYY-MM-DD
### やったこと
### 現在の状態
### 次の作業
```

---

## 2026-08-07 (ラジコン操作による走行動作を確認)

### やったこと

- ユーザー実施のラジコン試験で、無線操作から機体の走行動作まで成立したことを確認した。
- 操作入力から走行系までの統合経路が実機でつながったため、開発段階を単体・空走中心の確認から、接地状態の安全性・再現性・負荷評価へ進める。
- 試験結果の扱いと次段階の確認項目を`docs/testing/RC_DRIVE_TEST_2026-08-07.md`へ記録した。

### 現在の状態

- ラジコン操作による走行成立は確認済み。ただし、速度、走行時間、試験路面、battery条件、実施maneuver、電圧・電流・温度の定量logは未記録であり、性能または安全の受入試験完了とは扱わない。
- 高速走行・急制動へ進む前に、通信断、送信機停止、CAN timeout、E-stop、再起動時の不意再始動防止を確認する必要がある。

### 次の作業

1. 低速で前後・左右・旋回・斜行・並進旋回を正逆実施し、再現性とunit方向／steer反転を確認する。
2. battery A/B電圧・電流、contactor後motor bus電圧、C620 rpm/current/temperature、指令値、停止時刻を同一時系列で記録する。
3. 通常減速、送信機断、CAN断、E-stop、電源再投入を分けて試験し、安全状態遷移を確認する。
4. 25%から段階的に速度を上げ、急制動時の回生energyからbrake resistorとchopper要件を決める。

## 2026-08-06 (主電源遮断方式の再確認)

### やったこと

- C620主電源の遮断をMOSFET式solid-state switchへ置換する案を比較した。
- 回生時にOFF状態で双方向遮断するにはback-to-back MOSFET、high-side gate driver、並列均流、熱・SOA・短絡保護が必要になるため、Rev.Aの主遮断は機械式コンタクタを継続すると再確認した。
- `POWER_DISTRIBUTION_AND_ESTOP.md`に残っていたKILIGEN E228の採用／不採用の矛盾を、2026-07-26の実績根拠付き採用決定へ統一した。

### 現在の状態

- 主遮断はKILIGEN E228、コイル駆動はTeensy制御のlow-side MOSFETとする。
- prechargeと回生brake chopperは独立MOSFET回路として検討を続け、主遮断機能は担わせない。
- E228には正式なDC負荷遮断datasheetがないため、約83Aの過去実績を超えないこと、接点状態、実負荷時の温度確認が残る。

### 次の作業

1. E228主接点の摩耗・ピッティング・溶着兆候を目視確認する。
2. 負荷試験logから最大・連続電流を確認し、E228の約83A実績範囲内か判定する。
3. 独立precharge／brake chopper基板の回路要件と抵抗定格を確定する。

## 2026-08-05 (中央Teensy基板 I/O・回生制動仕様の再検討を保存)

### やったこと

- 中央基板の通信port、汎用GPIO、battery監視、contactor後監視、回生brake chopperについて対話で整理した。
- 旧I/O案を確定仕様として進めず、`SCHEMATIC_DESIGN_OPEN_ITEMS.md`のCTR-16を再オープンし、CTR-21〜25へ検討内容を保存した。
- 現時点の候補として、CAN1/2/3各GH3 x1、I2C x2、UART x1、USB-CDC、2信号単位のGH4 GPIO port、load側bus電圧監視、独立analog comparator式chopperを記録した。
- battery A/Bの市販I2C sensor x2、部室在庫`BM14270AMUV-LBE2`、chopper用既製current sensor moduleの案を記録した。

### 現在の状態

- 上記はすべて未確定の検討メモ。中央基板requirements、Teensy pin assignment、architecture decisions、KiCad回路図には反映していない。
- 特にCAN connector数、I2C sensor型番/address、UART/SPI/GPIO port数、INA238を残すか、chopperをRev.Aへ含めるかが未確定。

### 次の作業

1. 対話を再開し、中央基板の外部接続機器一覧から通信port数を1項目ずつ確定する。
2. battery sensorとchopper current sensor moduleの型番を確認する。
3. 全項目の合意後にrequirements、pin assignment、architecture decisions、回路図を一括更新する。

## 2026-08-05 (Teensy socket pinの階層ラベル／未使用pin整理)

### やったこと

- `hardware/central-board/central-board/modules/200-teensy.kicad_sch`で、使用する44 socket pinの信号名を階層ラベルとしてJ1/J2のpin端へ直接接続した。
- 未使用のTeensy pin 33/37/38/39（socket pad 25/29/30/31）はtest pointへ出さず、回路図上でNo Connect（×）を付けた。
- 再生成用の`tools/kicad/annotate-teensy-hierarchical-pins.ps1`を追加し、pin割当正本とarchitecture decisionsも同じ方針へ更新した。
- KiCad 10 CLIでchild PDF出力、root netlist出力、ERC実行を行い、Teensy sheet内のpin未接続、label dangling、No Connect danglingが各0件であることを確認した。

### 現在の状態

- Teensy socket sheet単体では、使用pinと未使用pinを回路図上で直接判別できる。
- root sheet symbolにはTeensy childの階層pinをまだ配置していないため、root ERCには41種類の`hier_label_mismatch`が残る。他moduleを含む正式な親子sheet接続/ERC収束は未完了。

### 次の作業

1. rootのTeensy sheet symbolへ階層pinを取り込み、CAN・電源・安全・拡張module側の同名netへ接続する。
2. 他moduleも正式symbol／階層labelへ揃え、module単体からroot全体の順でERC 0へ収束させる。

## 2026-08-04 (中央基板 参照回路図＋簡易BOM PDFへ作り直し)

### やったこと

- 前回のKiCad階層sheet PDFは配線表を分割しただけで、人間が回路を追うreview資料として不適切だったため正本扱いをやめた。
- `UNIT_BOARD_SCHEMATIC_WITH_BOM`と`ODOMETRY_BOARD_SCHEMATIC_WITH_BOM`のA3横templateを再確認し、同じ「1機能=1ページ、大きな簡易回路図、重要caption、簡易BOM、page footer」構成で中央基板版を作成した。
- `docs/electrical/CENTRAL_BOARD_SCHEMATIC_WITH_BOM.html`をsource、`output/pdf/CENTRAL_BOARD_SCHEMATIC_WITH_BOM.pdf`をreview PDFとして作成した。全7ページ:
  1. 5 V input/eFuse/star distribution
  2. Teensy socket/pin function/mechanical keepout
  3. CAN interface x3
  4. E-stop hardware loop/contactor driver
  5. isolated E-stop monitor/rearm/24 V sense
  6. INA238/external Kelvin shunt
  7. expansion I/O/test access/review gates
- HTML各pageを1600x1051 PNGへrenderし、全ページを目視確認した。右端clip、CAN bus assignment欠け、Teensy socket label重なり、safety page下端labelを修正後、PDFを再出力した。

### 現在の状態

- オドメトリ／駆動module基板の既存PDFと同じ読み方で、中央基板を機能単位にreviewできる。
- KiCad階層sheetは転記/ERC用の下位資料。人間reviewの正本は新しい`SCHEMATIC_WITH_BOM` PDF。

### 次の作業

1. 新PDFをpage 1から順に人間reviewし、eFuse threshold、24 V protection、coil TVS、shunt source fuse、rearm位置を確定する。
2. 確定内容をKiCad正式symbolへ転記し、module単体からERC 0へ収束させる。

## 2026-08-04 (中央基板回路図を責務別moduleへ再構成)

### やったこと

- A3 1枚へ全回路を詰めた初版は人間reviewに不向きだったため廃止し、`central-board.sch`をroot index、以下6枚をchild sheetとする階層構成へ作り直した。
  - 100 Power input/eFuse/star distribution
  - 200 Teensy socket/pin map/safety GPIO default
  - 300-500 CAN communication x3
  - 600 E-stop/contactor/isolated monitor/motor bus sense
  - 700 INA238/external Kelvin shunt interface
  - 800-900 expansion/test access
- `tools/kicad/generate-central-board-modules.ps1`を追加し、詳細回路generatorから責務別sheetを再現可能にした。
- KiCad CLIでroot＋6 child sheetsの読込み、7ページPDF、netlist、各sheet SVG出力を確認し、全ページを画像renderして目視確認した。

### 現在の状態

- 担当者はroot sheetから自分の機能sheetだけを開いて、部品、pin、保護、TBD gateを独立してreviewできる。
- sheet間はglobal labelで接続している。現段階は引き続きreview draftであり、正式symbol化とERC 0件化は次工程。

### 次の作業

1. 各担当moduleでdatasheet対照reviewを行い、TBDとpin mappingを閉じる。
2. legacy child sheetsを現行KiCad形式へ変換し、正式symbol/pin type/footprintへ置換する。
3. module単体→root全体の順でERC 0件へ収束させる。

## 2026-08-04 (Teensy中央基板 人間レビュー用回路図作成)

### やったこと

- `hardware/central-board/central-board.sch`へA3横1枚のflat schematicを作成した。100=5V/eFuse、200=Teensy socket、300/400/500=CAN1/2/3、600=E-stop/contactor、700=INA238、800/900=expansion/testの機能blockに分け、pin番号・net名・TBD事項を図面上で追えるようにした。
- `output/pdf/central-board-review.pdf`をKiCad CLIから出力し、SVG/PNG renderでA3全体のblock配置、文字欠け、title blockを目視確認した。生成元は`tools/kicad/generate-central-board-schematic.ps1`へ保存した。
- Teensy 4.1はPJRC推奨24x1 socket x2を使い、Teensy直下面を部品/test point/露出copper禁止keepoutとする方針へ修正した。
- review中に判明した設計修正をrequirements、schematic reference、architecture decisions、open itemsへ反映した。
  - Micro-Fitはsingle-row `43650-0600` / `43645-0600`へ修正。旧`43025-0600`はdual-rowで嵌合しない。
  - LTV-847S入力を6.8kΩ x2から2.2kΩ x2、約5mAへ修正。
  - contactor clampを1N4007単独からdiode+TVSの実測選定へ変更。
  - TPS259470 OVLO、24V input reverse/surge保護、shunt sense source fuseを未確定gateとして明示。
- `hardware/central-board/README.md`へ回路図の開き方、review手順、`.kicad_sch`移行後にERC 0件をPCB開始条件とすることを記録した。

### 現在の状態

- 部品、pin番号、net、安全経路を人が照合できるRev.A review draftとPDFがある。KiCad 10で回路図/PDF/netlistを読み出せる。
- 現回路図はpin-explicit generic symbolとlegacy `.sch` labelを含むため、ERC acceptance対象ではない。正式symbolへ置換し現行`.kicad_sch`へ保存した後のERC 0件がPCB着手条件。
- PCBは未作成。Teensy socket方式は確定したが、stacking高さと機体内サービス空間はCAD照合が必要。

### 次の作業

1. KiCad GUIで`central-board.sch`を開いて現行`.kicad_sch`へ変換し、TPS259470/TCAN1051/INA238/LTV-847S/Teensyの正式symbolとpin typeへ置換する。
2. eFuse threshold worst-case計算、24V reverse/surge部品、contactor TVS、shunt source fuse、rearm button配置を確定し、図中TBDを閉じる。
3. No Connect/PWR_FLAGを整理してERC 0件へ収束させ、人間cross-check後にPCB placementへ進む。

## 2026-08-04 (Teensy 4.1中央基板 Rev.A 要件・回路入力固定)

### やったこと

- 中央基板のP0未解決事項を整理し、PJRC公式pinoutに基づくCAN1/2/3、安全I/O、I2C、SPI、UART、ADC、GPIOの全ピン割当を`docs/electrical/TEENSY41_CENTRAL_PIN_ASSIGNMENT.md`へ固定した。
- Teensy 4.1はSamtec `SSQ-124-03-G-S` x2のsocket実装、VUSB-VIN pad切断、CAN3=Drive FD、CAN1=Sensor、CAN2=Expansionとした。
- 5V主入力を`XT30PW-M`+`TPS259470LRPWR`へ確定し、逆接・逆流・突入・過電流・過熱を保護する方針、`RILM=750Ω` typ 4.45A、Teensy枝`1206L075/16YR`を決めた。
- E-stop監視を`LTV-847S`、contactor driverを`IRLML0100TRPBF`+1N4007、操作panelをMicro-Fit 3.0 6pin、物理再アームbutton必須へ固定した。
- バッテリー監視を`INA238AIDGSR`+外付け100A/75mV Kelvin shuntとし、83A級主電流を中央PCBへ流さない構成へ決めた。
- 回路block、接続値、connector pin、PCB配置配線制約、bring-up試験を`docs/electrical/CENTRAL_BOARD_SCHEMATIC_REFERENCE.md`へ記録し、architecture decisions・中央要件・open items・document indexを更新した。
- `git diff --check`で文書差分にwhitespace errorがないことを確認した。

### 現在の状態

- 中央基板Rev.Aの電気要件とKiCad転記入力は固定済み。KiCad回路図・PCBはまだ未作成。
- PCBは4層、暫定100mm x 80mm、四隅M3として開始できる。最終外形・取付穴・connector引出方向は機体CADとの照合が必要。
- 外付けshuntは電気仕様100A/75mV、Kelvin端子まで固定し、正式型番は分電盤の機械寸法確認待ち。

### 次の作業

1. `hardware/central-board/`へKiCad projectとA3 flat schematicを作成し、power、Teensy、CAN x3、安全I/O、battery monitor、expansionの順にERCを収束させる。
2. BOMとfootprintを正式発注型番へ紐付け、Teensy socket列間・XT30極性・Micro-Fit pin 1を現物/図面で二重照合する。
3. 機体CADから基板許容外形、取付穴、USB/CAN/5V/24V harnessの引出方向を確定し、placement/routing、DRC、製造出力へ進む。

## 2026-07-31 (ステア応答高速化・wheel=0操舵 実装計画)

### やったこと

- 最高steer rpmだけを広げず、速度mode単体同定→加速/制動FF同定→time scale縮小→
  速度/加速度包絡拡張→接地3輪回帰の順で理論限界へ近づけるロードマップを
  `docs/control/CENTRAL_COORDINATED_CONTROL.md`へ追加した。
- wheel rpm=0でもsteer角を独立制御することを正式な契約とし、停止角保持、明示pre-steer、
  ETAへの操舵時間算入、ゼロ速度付近の角度ヒステリシス、純操舵非干渉試験を計画へ追加した。
- 主要運用を「指定poseへ到着→タスク→別poseへ移動」とし、`ARRIVE_SETTLED→TASK_HOLD→
  PRESTEER→DEPART`を中央状態遷移へ追加した。低速域は固定40rpmを最終値にせず、
  `Tsettle/Tfeasible`で理論限界への接近を評価する。
- 現行の`min(40rpm, planned包絡)`はcommissioning guardへ格下げし、本番は
  `margin*469rpm`から実効wheel profile rpmを差し引く連続包絡を通常上限にする方針を追加した。
  初期margin=0.90ではwheel=0/265/1200rpm時の上限は307.0/240.7/6.98 steer軸rpmとなる。
- 現コードレビューから、連続unwrap角、時刻付き1kHz局所補間、mode要求の包絡射影、
  back-calculation anti-windup、motor速度+AMT角observer、モデル加速FF、bounded DOB、
  2x2 mode非干渉補償を優先度付き実装項目として追加した。
- 駆動中央バスをTeensy CAN3-G474 FDCAN1のCAN FD nominal 1Mbps/data 2Mbps+BRSへ更新した。
  32byte軌道を200〜250Hzで3輪へ送り、broadcast commit後にG474が1kHz補間する。
  F405センサーCANとC620 CANはClassic 1Mbpsを維持する。

### 現在の状態

- wheel=0の正逆90deg操舵は現ファームと空走試験ですでに成立している。
- 速度mode単体同定ツールは実装済みだが、`firmware/logs/steer-mode-id/`の実測ログはまだない。

### 次の作業

1. 固定治具・ガード・非常停止を準備し、現行Kp=120/Ki=50/LPF=2msのwheel=0速度step/PRBS基準ログを取る。
2. 純操舵中の実wheel rpmと正味回転量を記録し、mode非干渉を確認する。
3. タスク側からpre-steer許可を受ける中央状態遷移と、ゼロ速度時の明示steer目標保持を実装する。
4. Web UIの固定40rpm上限を無効化可能なcommissioning guardへ変更し、planned/hard動的包絡を中央・ユニットで共通化する。
5. 連続unwrap角と時刻付き軌道契約を先に実装し、中央プロファイルとファーム内ランプの二重化を解消する。
6. G474 FDCAN1とTeensy CAN3を64byte/BRS対応にし、32byte軌道+commitと48byte状態を実装する。
7. 内周速度帯域を確定後、time scaleを2.0から段階的に1.0へ縮小する。

## 2026-07-31 (リアルタイムベクトル操作・空走制御セーブポイント)

### やったこと

- 2D速度ベクトルGUIを、Enter確定式からEnable中約30Hzのリアルタイム指令へ変更した。
  矢印キー/Shift微調整/ドラッグ/Escゼロをサポートし、最新入力だけを送信する。
- Enable時はAMT実角度をsteer初期目標に採用し、wheel目標/プロファイルを0へ初期化することで、
  Disable中のdraftや以前の指令による意図しない発進を防ぐ。
- wheel rpmから200Hzでplanned/hard包絡線を再計算し、高wheel rpmほどsteer rpmを連続的に
  減らす本番目標生成をGUIにも適用した。
- 実機でwheel=100rpm、steer=59.854→69.854degを30Hz相当で連続入力し、
  最終70.049deg/104.2rpm、`MOTION_SETTLED=1`を確認した。試験後のSTOPでwheel 0へ復帰した。
- Python構文、Web UIセルフチェック、JavaScript構文、`git diff --check`は合格。

### 現在の状態

- 空走単体制御は、本番形式のwheel rpm+指定角度、time scale=2、rpm包絡線、CAN収束判定、
  リアルタイムGUIまで一続きで動作している。現最良制御はG474へFlash済み。
- Web UIはport 8080で稼働中。保存時点の実wheel/実効wheelは0rpm。Unit Enable状態はtrueのため、
  操作終了時はGUIのSTOPまたはDisableで明示的に停止すること。
- 空走の手応えは強いが、手で回転輪へ負荷を与える試験は再現性と安全性がないため今後行わない。

### 次の作業

1. モータDisable・ステア静止を条件に、治具で機械正面を合わせてAMTゼロオフセットをFlash保存する。
   再起動後に0/90/180/270degと回転方向を検証する。GUIからのゼロ保存操作も追加候補。
2. 固定治具・ガード・非常停止を用意し、代表実車輪荷重でwheel=75/265/1200rpm、正逆90deg、
   急反転、連続8の字を実施する。手で負荷は掛けない。
3. `2*Tmin+0.35s`、角度定常誤差0.5deg、wheel誤差`max(12rpm, 6%)`を暫定受入条件とし、
   電流・母線電圧・温度・包絡線制限率を保存する。失敗時は摩擦補償/トルクFFを先に調整する。

## 2026-07-31 (理論時間x2軌道・CAN収束フラグ・現最良制御の焼込み)

### やったこと

- wheel rpmによる差動モータ包絡、steer最大rpm、非対称加減速を含む台形/三角形の
  `hard Tmin`/10%予備付き`planned Tmin`をWeb UIへ実装した。通常指令はtime scale=2とし、
  steer速度1/2・加速度1/4、wheel rpmランプ1/2で本番相当の目標を生成する。
- G474へSTATUS3を実装し、角度0.5deg、実steer軸1rpm、wheel追従、steer/wheel FF停止を
  100ms連続で満たすと`MOTION_SETTLED`を立てるようにした。STATUS1/3=20ms、STATUS2=50msを
  通常送信し、idx22はベンチ高周期overrideへ変更した。
- 現最良の空走値`steer PI=120/50、mode LPF=2ms、angle Kp=4/moving=1、deadband=0.3deg、
  accel/decel FF=0.5/0.5`を起動時既定へ反映し、G474へFlash/verifyした。
- 本番契約と同じ`SET_TARGET(wheel rpm, 指定角度)`+`SET_TARGET_FF`で、wheel=0/265rpm、
  正負90degを各3回回帰した。time scale=2の12試行はCAN収束12/12、監視期限
  `2*Tmin+0.35s=1.273s`以内12/12、平均1.146s、最悪1.250s、最大overshoot 1.054degだった。
- GUIへwheel/steer実rpm、hard/planned理論時間、2倍軌道、CAN収束状態を表示した。
  2D速度ベクトルの先端を矢印キー/ドラッグで動かすと、Enable中は約30Hzで
  方向=steer角、長さ=wheel rpmをリアルタイム送信するパッドを追加した。Disable中はdraftのみで、
  Enable時は実角度+wheel 0から安全に開始する。最大長は10%予備付きpure-wheel上限1228rpm。
- 実機へ30Hz相当で59.854→69.854degを連続入力しながらwheel=100rpmを指令した。
  最終70.049deg/104.2rpmでCAN収束flagを確認し、STOP後はDisable・wheel 0rpmへ復帰した。
- wheel=1200rpm定常ではplanned steer上限6.98軸rpm、time scale=2後の実指令3.49軸rpmを確認。
  wheel rpmの増減に応じて毎200Hz周期で包絡線を再計算し、steer rpm上限を連続的に増減する。

### 現在の状態

- 最終ファームをG474へ書込み・検証済み。リアルタイム版Web UIはport 8080で起動中、ユニットはDisable。
- 単一ユニット空走では2倍軌道+0.35s監視余裕を12/12で満たす。倍率1の厳しいゲイン試験は
  収束11/12・2*Tmin以内7/12で、終端静止摩擦は残る。

### 次の作業

1. 接地荷重・床材・バッテリー電圧を跨ぐ回帰で追従残差p99を測り、0.35s監視余裕を更新する。
2. Teensy中央100Hzへ10%予備包絡、3輪共通time scaling、STATUS3完了集約を移植する。
3. 終端摩擦は一定floorでなく、摩擦推定/DOBまたは終端専用補償で改善する。

## 2026-07-31 (ステア自動校正・理論速度への接近)

### やったこと

- 実機の粗→細自動探索をKp/Kiだけでなく、angle P/deadband、mode速度LPF、電流上限、
  加速度FF、ステア加速/制動へ拡張した。指令/実測電流peakと運動学的下限比も自動集計する。
- 中央側ベンチ目標生成を200Hzへ上げ、ステア加速3600deg/s^2と制動2250deg/s^2を分離した。
- 局所既定値をsteer mode Kp/Ki=80/25、angle Kp=4、速度LPF=10ms、加速度FF=0.75へ更新し、
  build/flash/verifyした。
- wheel=0/265rpm、正逆90degを各3反復したFlash後回帰は12/12成功。平均0.760s、最悪0.924s、
  理論0.375s比の平均2.03、最大overshoot 2.64deg、温度peak 30degCだった。旧平均1.185sから約36%短縮。
- 電流上限3000〜6000raw比較では指令peakが約2000rawに留まり、電流クランプが律速でないことを確認した。
- 校正を「内周速度PI→外周angle P→FF/プロファイル→負荷・床材ロバスト検証」に分ける手順を
  `docs/testing/UNIT_AUTO_TUNER.md`へ記録し、非対称ステア加速/制動を設計決定へ追加した。
- 巡航中の外周Kp干渉による中間カクつきへ、moving angle Kp=1からhold Kp=4へ連続補間する
  2自由度外周を追加しflashした。加速FF=0.75、制動FF=1.0も分離した。
- 300/360deg/sはovershoot増加で240deg/sより遅く、内周速度帯域が次の律速と判定した。
  最低速度floorと一定steer摩擦FFも悪化したため0へ戻した。
- 定常の多くは0.68〜0.92sだが、冷間1発目が0.527deg残る11/12バッチもあり、初回静止摩擦と
  絶対角依存の再現性は未解決。全ログは`firmware/logs/auto-tune/`へ保存済み。

### 現在の状態

- 最新ファームを書込み済み。200Hz Web UIは起動中、ユニットはDisable。
- 空走採用値はファーム/Web UI/自動調整器で一致している。

### 次の作業

1. **次セッション最優先:** 外周を切ったsteer mode速度step/PRBS同定モードを追加し、
   10ms→5ms以下の速度LPFで内周Kp/Kiを再同定する。
2. 接地時は空走値近傍だけ再探索し、床材・荷重を跨いだ最悪値で共通ゲインを決める。
3. Teensy中央制御へ非対称ステア加速/制動と200Hz相当の目標生成を移植・検証する。

## 2026-07-31 (差動ステア制御の高速収束・rpm包絡線・回生減速方針)

### やったこと

- 機構抵抗低下後の操舵発振を実機ログで切り分け、中央側目標生成を定速スルーから制動付き
  台形/三角形プロファイルへ変更した。90deg収束は最大240deg/s・加減速720deg/s^2を採用。
- `KINEMATICS_AND_RPM.md`の実測済みステア比`8/11`を正本として照合し、
  `DYNAMIC_CONTROL_PLAN.md`と`CENTRAL_COORDINATED_CONTROL.md`に残っていた旧`2/11`の
  包絡線式・数値表を修正した。
- 中央からユニットへの主目標を`omega_w, theta_s`、軌道微分をFFとして併送、中央100Hz・
  ユニット局所1kHzとする指令契約を`CENTRAL_COORDINATED_CONTROL.md`へ明記した。
- 単一モジュール式`|n_drive|/1364 + |n_steer|/341.1 <= 1`をWebUI目標生成へ接続し、
  wheel=1300rpm時のsteer要求240deg/sが96.5deg/sへ自動制限されることを実機確認した。
- 高rpm急減速の回生電圧上昇対策として、中央でwheelを非対称ランプに通し、反転は0rpm経由、
  通常STOPは減速完了見込み後にdisableする方針を`ARCHITECTURE_DECISIONS.md`へ確定事項として追加した。

### 現在の状態

- 改良版WebUIは起動中、ユニットはDisable。ファーム局所ループは1kHzのまま。
- WebUI既定はsteer加減速720deg/s^2、wheel加速1000rpm/s・減速500rpm/s。
- 500rpmからのSTOPは1.51s待機し、disable時実測0.015rpm。ビルド・セルフチェック合格。

### 次の作業

1. WebUIで検証したプロファイル・包絡線・非対称wheelランプを中央Teensy 100Hz制御へ移植する。
2. DCバス電圧を測定し、高rpm減速率500rpm/sの安全余裕を確認する。
3. 低抵抗化後の25/40rpm積分フロアA/Bを完了し、摩擦補償値を再同定する。

## 2026-07-29 (シルク手直し後 Gerber・ステンシルZIP再生成)

### やったこと

- ユーザーによる表面シルク手直し後のPCB(2026-07-29 13:12:32保存)を対象に製造出力を再生成した。
- ゾーン再フィル込みDRCで違反0件・未接続0件・Footprint error 0件を確認した。
- 既存のGerber ZIP、ステンシルZIP、展開ディレクトリを最新内容で置き換えた。
- F.Pasteは234開口、B.Pasteは0開口のため、ステンシルZIPはF.Paste+Edge.Cutsの片面用とした。

### 現在の状態

- `output/fabrication/odometry-board-revA-gerbers.zip`と`odometry-board-revA-stencil.zip`はシルク手直し後の最新版。

### 次の作業

1. 発注サイトのGerber viewerで手直し後シルク、基板外形、穴を最終確認する。

---

## 2026-07-29 (F405オドメトリ基板 Gerber・ステンシル製造ZIP作成)

### やったこと

- 保存後の最新PCBで、IMUコネクタ機能シルク6文字を0.6mmから基板制約の0.8mmへ修正した。
- 埋込みQR/ロゴおよび意図的なローカルFootprint差分について、ライブラリ比較DRCをignoreへ設定した。
- ゾーン再フィル込みDRCで違反0件・未接続0件・Footprint error 0件を確認した。
- 4層銅、表裏マスク/シルク、外形、PTH/NPTHドリルを含む`odometry-board-revA-gerbers.zip`を作成した。
- F.Paste(234開口)+Edge.Cutsを含む片面用`odometry-board-revA-stencil.zip`を作成した。B.Pasteは0開口のためステンシルZIPから除外した。

### 現在の状態

- 製造用Gerber ZIPと表面ステンシルZIPは`output/fabrication/`に作成・検証済み。

### 次の作業

1. 発注サイトのGerber viewerで層構成、外形、表裏シルク、穴を最終目視確認する。
2. ステンシル発注では片面(F.Paste)として指定し、厚さとフレーム有無を選択する。

---

## 2026-07-29 (F405オドメトリ基板 機能シルク仮配置)

### やったこと

- 基板名/Rev、AMT WHEEL 1/2/3とpin配列、PWR/RUN/COMM/ERR、SENSOR CAN、CAN TERM、5V IN、SWD/UART、ID DIP、IMUの機能シルクをF.SilkSへ仮配置した。
- 後から人が個別に移動できるよう、26個の独立したPCB textとして配置した。
- シルク文字高さを基板制約の0.8mm以上、線幅を0.1mmへ統一し、長いSWD/IMU pin列は2行へ分割した。
- KiCad 10トップ面レンダリングで内容を確認し、ゾーン再フィル込みDRCで違反0件・未接続0件・Footprint error 0件を確認した。

### 現在の状態

- 機能シルクは基板内へ仮配置済み。密集部では部品外形・コネクタ・他ラベルとの重なりがあるため、最終位置はPCB Editorで人が調整する。

### 次の作業

1. PCB Editorで各ラベルを見やすい位置へ移動し、コネクタ実装後も読めることを確認する。
2. F.SilkS Gerberを出力し、基板端欠け・パッド上・コネクタ下の文字がないことを最終確認する。

---

## 2026-07-29 (F405オドメトリ基板 部品番号非表示・DRC 0件化)

### やったこと

- PCB上の全68個のFootprint Referenceを非表示にし、部品外形・pin 1/極性マークは残した。
- 同一座標に重複していたGND viaを1個削除し、意図的なローカルFootprint差分チェックはDRCでignoreへ設定した。
- ゾーン再フィル込みのKiCad 10 CLI DRCで、違反0件・未接続0件・Footprint error 0件を確認した。
- 残すべき機能シルクを`ODOMETRY_BOARD_REQUIREMENTS.md`へ列挙した。

### 現在の状態

- 部品番号シルクは非表示。基板上には機能シルクを今後配置する余地がある。
- 電気的DRCは0件。シルククリアランス、Footprintライブラリ差分などの意図的なチェックはignore設定。

### 次の作業

1. 要件書の一覧に従い、基板名/Rev、コネクタ信号、AMT輪番号、LED、ID DIP、CAN終端、デバッグ、IMU軸方向の機能シルクをPCBへ配置する。
2. F.SilkS Gerberを出力し、コネクタ下・パッド上・基板端で文字が欠けないことを確認する。

---

## 2026-07-28 (F405オドメトリ基板 配線DRC収束・共有)

### やったこと

- ユーザーがKiCad PCB Editorでオドメトリ基板の配線を修正し、未接続を0件へ収束させた。
- シルク自体は残し、`silk_edge_clearance`、`silk_over_copper`、`silk_overlap`をDRCの`ignore`へ設定した。
- KiCad 10.0.4 CLIでPCB未接続0件を確認した。
- push前確認で、回路図には`U3/U7/U9 74LVC2G17`の電源ユニットC未配置によるERC error 3件、warning 3件が残っていることを確認した。

### 現在の状態

- PCBの電気的未接続は0件。
- DRCの残りはローカル変更Footprintのライブラリ差分と重複穴の警告で、シルク関連警告は非表示。
- 回路図ERCは未収束で、`74LVC2G17` x3の電源ユニット配置が必要。

### 次の作業

1. AMT102入力3シートへ`U3C/U7C/U9C`を配置し、3.3V/GNDへ接続してERCを再実行する。
2. 重複穴警告の対象を確認し、実重複なら片方を削除する。
3. ローカルFootprint差分を確認し、意図した差分だけ個別除外する。

---

## 2026-07-26 (中央基板 メインコンタクタ確定)

### やったこと

- モジュール評価計画の策定に続けて、中央Teensy基板の要件を固めて回路作成に入る段階へ移った。`docs/electrical/CENTRAL_BOARD_REQUIREMENTS.md`を確認し、CAN構成・mini PC接続・安全I/Oの設計思想は既に確定済みで、回路作成前の唯一のブロッカーがメインコンタクタの正式型番であることを特定した。
- 所有品`KILIGEN E228`(24V DC、100A表記)について、販売情報上の連続使用目安50〜60Aに対し正式なDC負荷遮断定格データシートが無い問題を確認し、採用可否の判断手順(コイル電流確定→想定電流の上限設計→実負荷相当での遮断試験+接点目視検査)を`ARCHITECTURE_DECISIONS.md`・`CENTRAL_BOARD_REQUIREMENTS.md`へ暫定採用として記録した。
- ユーザーがコイル仕様(定格コイル電圧24V DC、コイル電力1.8W、コイル抵抗300Ω、動作電圧14〜16V、解放電圧6〜8V、最大印加電圧28V DC)を確認。計算上のコイル電流は約75〜80mAで、コイル抵抗・電力表記が相互に整合することを確認し、コイルドライバ設計(ロジックレベルNch MOSFET、Vgs(th) 2V以下、Vds 40〜60V級+1N4007フライバック)に反映した。
- 主接点側のDC負荷遮断定格について、ユーザーから前回ロボコン機体でこの個体を使用し、約2000W(24V換算で約83A)の通電中にE-stop等で遮断できた実績があるとの確認を得た。販売情報上の連続使用目安50〜60Aを上回る電流での負荷遮断実績のため、正式データシートの代替根拠として採用し、フル再検証キャンペーンは不要と判断した。残る作業は再利用前の主接点摩耗・ピッティングの目視検査のみとした。
- `docs/electrical/CENTRAL_BOARD_REQUIREMENTS.md`と`docs/ARCHITECTURE_DECISIONS.md`のメインコンタクタ関連記述を上記内容で更新した。

### 現在の状態

- メインコンタクタは`KILIGEN E228`で確定。コイル側の設計値は確定済み、主接点側は前回ロボコンでの実績を根拠として採用し、残作業は目視検査のみに縮小した。
- コイルドライバの具体的なMOSFET品番はまだ選定していない(Vgs(th) 2V以下、Vds 40〜60V級という条件のみ確定)。
- 中央基板の他の未確定事項(5A主入力の逆接/逆流保護、Teensy/拡張枝のヒューズ定格)は今回のセッションでは着手していない。

### 次の作業

1. `KILIGEN E228`の主接点を目視検査し、摩耗・ピッティングがないか確認する。
2. コイルドライバのMOSFET品番を選定する(Vgs(th) 2V以下、Vds 40〜60V級)。
3. 中央基板の残る未確定事項(5A主入力逆接/逆流保護、Teensy/拡張枝ヒューズ定格)を確定し、回路図入力へ進む。

---

## 2026-07-26 (オドメトリ+IMUモジュール評価計画の策定)

### やったこと

- 単一モジュール評価計画の策定に続けて、オドメトリ基板(3輪AMT102+ICM-42688-P、unitId=4)のpose精度をどう評価するかを検討した。
- 2次元経路(XY全体)をトレースする治具は製作難度が高いため不採用とし、代わりに**直線スライダー試験(各輪独立、既知距離で線形換算精度を確認)+回頭ピボット試験(既知角度、平行2輪の差分計算に使うトレッド幅の校正誤差を確認)**の2試験で系統誤差を切り分ける方針とした。直線試験だけでは回頭誤差(トレッド幅誤り)が原理的に検出できない(平行2輪は直線移動中は差分が常時ゼロになるため)ことを確認し、2試験が両方必要と結論した。
- IMUセンサフュージョンの重み付けについて、手動チューニングではなく各センサの誤差特性を先に測定してから重みを導出する方針とした。ジャイロは静止積分によるドリフト特性測定、ホイールオドメトリのθ誤差は回頭ピボット試験(スリップが出やすい条件を振る)で測定する。
- オドメトリ+IMUノードの更新周波数を「①推定値そのものの精度(内部積算レートで決まる)」と「②消費側が使う値の鮮度(配信レートで決まる)」に分けて整理した。中央Teensyの車体逆運動学が100Hzで動く設計(`control/CENTRAL_COORDINATED_CONTROL.md`)であることから、配信は100Hzが妥当と結論し、これが既存の`ODOMETRY_BOARD_REQUIREMENTS.md`のpose 100Hz配信仕様と整合することを確認した。ユニットMCUの1kHzループはSET_TARGET追従用の別経路でオドメトリを消費しないため、そちらに配信レートを合わせる理由はないことも整理した。
- 上記を`docs/testing/ODOMETRY_IMU_EVALUATION_PLAN.md`へ新規文書化し、`docs/PROJECT_DOCUMENT_INDEX.md`へ11.3として登録した。

### 現在の状態

- 評価計画は文書化済み。治具製作・実測はまだ着手していない。

### 次の作業

1. 直線スライダー試験用の治具(定規+スライダー)を用意し、各輪独立で線形換算精度を確認する。
2. 回頭ピボット試験用の治具(固定ピボット+角度ゲージ)を用意し、トレッド幅校正誤差を確認する。
3. ジャイロ静止ドリフト試験を実施し、上記2試験の結果と合わせてセンサフュージョンの重みを導出する。

---

## 2026-07-26 (単一モジュール負荷ロバスト性評価計画の策定)

### やったこと

- ロボコンでの雑談を発端に、差動ステアユニット1基の単体テストの難しさ(steer/wheelが1モータの合成/差分で決まり、機構的に独立評価できない)を整理し、負荷試験の治具方針・評価項目・実施順序を確定した。
- 治具は「実機3モジュール同時稼働」「単輪+台車+重り」を不採用とし、**4隅従動輪+中央に評価対象モジュール1基**を採用した。荷重をシャーシ経由で接地点に伝えつつ、駆動は1モジュールのみで独立評価を維持する。5点接地の静定性は従動輪側のコンプライアンスで確保する方針。
- `docs/control/KINEMATICS_AND_RPM.md`の数値(モータ定格469rpm、DRIVE_RATIO=32/11、STEER_RATIO=8/11)から、wheel/steerが2モータの共有電流予算を通じて1枚の動作包絡線(菱形)を成すことを導出した: `|n_drive|/1364 + |n_steer|/341.1 ≤ 1`。マージン10%を適用した目標境界は`|n_drive|/1228 + |n_steer|/307.0 ≤ 1`で、目標wheel上限1228rpmは既存の2026-07-07実測1200rpm(p-p 3.5〜4rpm)とほぼ一致し、マージンの妥当性を裏付けた。steer軸は理論比で大幅余裕がある(現行ソフト上限40rpm=240°/sは理論比12%)ため、目標値は理論マージンでなく競技要求から決める方針とした。
- 制御ループ周期を確認し、`firmware/src/main.c`の`CONTROL_PERIOD_MS=1`で既に1kHz制御ループが実装済みであることを確定した。これはC620自体のCANプロトコルが1kHz固定であることに整合しており、デジタルループ側はほぼ天井に到達済みで、残る改善余地は機構帯域(バックラッシュ・摩擦)側にあると整理した。
- 計測方針として、wheel rpmはモータエンコーダ由来の計算値(`feedback.rpm/19×DRIVE_RATIO`)をまず信頼性確認する(steer固定・純駆動条件で無負荷/負荷双方を検証)ことを優先し、問題があれば`AMT102`(オドメトリ基板採用品と同型)を出力軸へ仮設する方針とした。オドメトリ基板は駆動輪と別の専用従動輪を使うため、今回の単体評価には流用できないと結論した。
- 負荷試験で追加すべき計測として`torque_current`(C620フィードバック、`c620.c`でデコード済みだが現状ログ未出力)と`temperature_c`を特定した。
- 実施順序を「0. wheel rpm信頼性確認 → 1. 独立軸試験(無負荷、大部分実施済み) → 2. 同時指令試験(無負荷、治具不要) → 3. 4隅従動輪治具の製作 → 4. 負荷試験本体」に確定した。2は差動の合成数式に起因する現象で負荷に依存しないため、治具製作を待たずに着手できる。
- 上記を`docs/testing/SINGLE_MODULE_LOAD_EVALUATION_PLAN.md`へ新規文書化し、`docs/PROJECT_DOCUMENT_INDEX.md`へ11.2として登録した。

### 現在の状態

- 評価計画・治具方針・動作包絡線の数値・実施順序は文書化済み。ファーム・治具の実装はまだ着手していない。
- 動作包絡線を可視化したチャート(Artifact)を作成済み。理論境界・目標境界(菱形)、実測点、現行steer上限帯を表示。

### 次の作業

1. steer固定・純駆動条件でのwheel rpm信頼性確認試験を無負荷/負荷双方で実施する。
2. `main.c`のテレメトリに`torque_current`のログ出力を追加する。
3. 同時指令試験(steer Δθ複数段 × wheel rpm複数点、無負荷)を既存NUCLEOベンチで実施し、クロスカップリングデータを取得する。
4. 4隅従動輪治具を製作する(従動輪側のコンプライアンス機構を含む)。
## 2026-07-26 (F405オドメトリ基板 DRC一次確認)

### やったこと

- `hardware/odometry-board/Oddom board/Oddom board.kicad_pcb`の保存済み状態へKiCad 10.0.4 CLI DRCを実行した。
- 現状はDRC違反152件、未接続13件。ゾーン再フィル後も未接続13件は変わらず、実配線の修正が必要と確認した。
- 自動配線案は密集部で他ネットとの交差・短絡を生じるため基板本体へ適用せず、ユーザーの既存PCB/プロジェクト変更を保持した。
- PCB Editorは同時書き込み防止のため正常終了した。未保存状態のSchematic Editorは閉じずに残した。
- ユーザーがGUI上で配線DRCを0件まで修正した。シルクを基板から削除せず、DRCの`silk_edge_clearance`、`silk_over_copper`、`silk_overlap`だけを`ignore`へ変更した。

### 現在の状態

- 基板本体へ今回の自動修正は入れていない。
- 重要項目は未接続13件、J2取付パッドの基板端クリアランス1件、重複GND via 1組、dangling 3.3V via 1件。
- 残りの大半はシルク重なり/銅箔上シルク、基板端シルク、ローカル変更済みFootprintとライブラリの差分警告。

### 次の作業

1. KiCadインタラクティブルータでDRCレポート記載の未接続13件を接続し、GNDは内層`GND Plane`へのvia追加を基本にする。
2. J2のMPと基板端、重複via、dangling viaを修正する。
3. シルク文字を移動/非表示化し、意図したローカルFootprint差分だけ個別除外してDRCを再実行する。
---

## 2026-07-26 (F405オドメトリ回路図 転記中の部品・接続確認)

### やったこと

- ユーザーがKiCad上でA3横1枚のオドメトリ回路図を転記する過程で、AMT102入力回路とF405最小回路の接続を再確認した。
- `ESDS452DBZR`はAMT102のA/B各信号をGNDへクランプする2ch双方向TVSであり、A-B間を短絡する部品ではないことを確認した。pin 1/2をA/B、pin 3をGNDとし、AMTコネクタ1個につき1個をコネクタ直近へ配置する。
- KiCad 10標準ライブラリには`ESDS452DBZR`の型番固有シンボルがないことを確認した。SOT-23フットプリントは標準にあるため、シンボルは双方向2ch・pin 1/2=IO・pin 3=GNDを満たすものを作成またはピン割当を検証して使用する。
- `SN74LVC2G17DBVR`はKiCad 10標準`74xGxx:74LVC2G17`を使用でき、DBVには`Package_TO_SOT_SMD:SOT-23-6`を割り当てることを確認した。3.3V給電、最大5.5V入力対応の非反転2ch Schmitt bufferとして、AMTの5V A/B信号を整形してF405へ3.3V出力する。
- `C511-C516`は`R511-R516`とRCローパスを構成する入力-GND間の調整用パッドで、初期実装はDNPと再確認した。`C501-C503`の100nFはSchmitt bufferの必須デカップリングであり、役割を区別した。
- STM32F405RGT6のpin 63はVSSであることをST資料とKiCad 10標準`STM32F405RGTx`で再確認した。KiCadシンボルではpin 18のVSSと同一座標に重ねた非表示pinのため、表示上はpin 18だけに見えるが、VSSをGNDへ接続すればpin 63も同一ネットになる。
- BOOT0は専用pin 60から10kΩでGNDへpull-downし、BOOT0テストポイントと隣接3V3テストポイントを設け、ROM bootloader使用時だけ短絡してリセットする接続と再確認した。

### 現在の状態

- 回路図の正本要件、簡易回路図、部品・Footprint・接続表は揃っており、ユーザーがKiCadへ手動転記中。
- 今回はKiCad回路図本体を変更していない。
- AMT入力は`connector -> ESDS452 -> 100Ω -> SN74LVC2G17 -> F405 timer input`、RCコンデンサは初期DNPで確定済み。

### 次の作業

1. `hardware/odometry-board/Oddom board/`の回路図転記を続け、F405電源、BOOT0、AMT102 x3、CAN、IMU、Debug/ID/LEDをA3横1枚へ配置・配線する。
2. `ESDS452DBZR`はpin 1/2=保護IO、pin 3=GNDとなる型番固有シンボルを用意するか、採用する代用シンボルのピン番号と双方向表現をTIデータシートに照合する。
3. 転記完了後、ERC、ネットリスト、PDFを出力し、特にVSS pin 18/63、VDD pin 19/32/48/64、VCAP_1/2、BOOT0 pin 60、AMT A/B全6chを接続表と照合する。

---

## 2026-07-25 (オドメトリ基板 簡易回路図＋BOM作成)

### やったこと

- unit board版`UNIT_BOARD_SCHEMATIC_WITH_BOM`と同じA3横レイアウトで、ブロック別の簡易回路図＋BOMを作成した。
- 6ページ構成: 5V/3.3V電源、F405最小回路、センサーCAN、AMT102 x3、ICM-42688-P、Debug/ID/LED。
- 各ページへRefDes、部品名/値、KiCad Footprint、接続先・注意事項を併記した。
- 電源はunit board共通図を流用し、F405固有回路とCAN/AMT102/IMU/Debug図はオドメトリ用信号名で新規作成した。
- PDF全6ページをレンダリングし、文字切れ・重なり・図欠落がないことを目視確認した。

### 現在の状態

- HTML: `docs/electrical/ODOMETRY_BOARD_SCHEMATIC_WITH_BOM.html`
- PDF: `docs/electrical/ODOMETRY_BOARD_SCHEMATIC_WITH_BOM.pdf`
- 配布用PDF: `output/pdf/odometry-board-schematic-with-bom.pdf`
- KiCad回路図本体は変更していない。

### 次の作業

1. 簡易回路図を見ながらKiCadのA3横1枚へ回路を転記する。
2. IMU現物到着後にJ601 Footprint、pin 1、pitch、外形、固定穴を追記する。
3. 転記後にERC/PDF出力し、簡易回路図の各ネットと1:1照合する。

---

## 2026-07-25 (オドメトリ回路図リファレンス HTML/PDF化)

### やったこと

- Markdown版の接続仕様を、図表・機能ゾーン・信号フロー付きのHTMLへ再構成した。
- ユーザー意図に合わせ、回路図そのものではなく「部品名・値・KiCad Footprint・接続先」を追える回路図転記表へ修正した。
- Chrome印刷用CSSでA4横7ページのPDFを生成した。
- PDF全7ページをPNGへレンダリングし、文字化け、表の切れ、重なりがないことを目視確認した。
- 一時的に作成したKiCad自動生成ドラフトは要求範囲外と判明したため、正規成果物から除外した。ユーザー編集中の`Oddom board.kicad_sch`は変更していない。

### 現在の状態

- HTML: `output/html/odometry_board_schematic_reference.html`
- PDF: `output/pdf/odometry_board_schematic_reference.pdf`
- 回路図本体はKiCad GUIでロック中のため未変更。

### 次の作業

1. HTML/PDFを横に表示しながら、KiCadのA3横1枚へ100番台順で部品を配置する。
2. 回路図保存・終了後、ERC/PDF出力と接続表の1:1照合を行う。

---

## 2026-07-25 (オドメトリ基板 フラット回路図方針確定)

### やったこと

- オドメトリ基板Rev.Aは階層シートを使わず、A3横1枚のフラット回路図へまとめる方針を確定した。
- 電源、F405、CAN、AMT102 x3、ICM-42688-P、Debug/ID/LEDのゾーン配置、100番台RefDes、ローカルネットラベル、接続表を`ODOMETRY_BOARD_SCHEMATIC_REFERENCE.md`へ整理した。
- AMT102入力は`ESDS452DBZR` x3を正式選定し、connector -> TVS -> 100Ω初期値の直列抵抗 -> Schmitt buffer -> MCUの順に確定した。RCはDNP footprintのみ用意する。
- `hardware/odometry-board/Oddom board/`にKiCad 10の新規プロジェクトが作成されていることを確認した。

### 現在の状態

- 新規回路図は空のA4シートで、KiCad GUIにより編集中ロックされている。
- 同時編集による破損を避けるため、今回はこちらから`.kicad_sch`本体を書き換えていない。
- 1枚へ転記する接続仕様とRefDesは準備完了。

### 次の作業

1. KiCad上で用紙をA3横へ変更し、リファレンス資料のゾーン順に部品を配置・配線する。
2. 保存・終了後、`tools/kicad/check.ps1`でERC/PDF出力を行い、接続表とネットリストを照合する。

---

## 2026-07-25 (ICM-42688-P IMUモジュール購入反映)

### やったこと

- ユーザー購入品を`ICM-42688-P`搭載ブレークアウトモジュールとして採用確定した。購入先はAliExpress item `1005012473450791`。
- TDK公式仕様で6軸、VDD/VDDIO=1.71～3.6V、I2C/I3C/SPI対応を確認し、オドメトリ基板では3.3V・4-wire SPIを使用する方針とした。
- F405側をSPI3 PC10=SCK、PC11=MISO、PC12=MOSI、PD2=`IMU_CS_N`、PC4=`IMU_INT1` Data Ready、PC5=`IMU_INT2`予約に確定した。
- キャリア側のIMU電源デカップリングはunit board採用品の100nF+2.2µFを流用する。
- 初回bring-upはSPI Mode 0・1MHz以下で`WHO_AM_I` register `0x75`から`0x47`を確認し、その後に周期取得と速度引上げを行う手順へ確定した。
- 購入モジュールが5V/3.3V給電、I2C/SPI両対応の8pin構成
  (`VCC/GND/AD0(MISO)/SDA(MOSI)/SCL(SCLK)/CS/INT1/INT2`)であることをユーザー情報から確認した。
  本基板ではVCC=3.3V固定、4-wire SPI、INT1/INT2両方を配線する。

### 現在の状態

- IC型式とMCU側信号割当は確定した。
- ヘッダ信号構成は確定。物理pin 1方向、pitch、外形、固定穴、オンボードLDO/レベル変換回路は未確認。

### 次の作業

1. 到着後にモジュールの表裏写真、pin 1方向、pitch、外形寸法、固定穴を確認する。
2. 3.3V/GNDとIC VDD/VDDIO、SPI/INT端子の導通を確認し、オンボード回路を確定する。
3. 確定した外形とpin順をF405オドメトリ回路図・PCB固定方法へ反映する。

---

## 2026-07-25 (F405オドメトリ資料レビュー・unit board部品流用確定)

### やったこと

- Claude作成のF405変更資料を、ST公式DS8626 Rev.12、AN4488、KiCad 10標準`STM32F405RGTx`シンボルと照合した。
- 初稿の「PD2はF405 LQFP64に存在しない」は誤りで、PD2はpin 54に存在することを確認した。SPI IMUのCSはG474案と同じPD2を維持し、PA15はハードウェアNSSが必要な場合だけの代替候補へ戻した。
- 初稿のLQFP64物理pin表にあった複数のずれを修正した。CAN1=PA11/PA12(pin 44/45)、SWD=PA13/PA14(pin 46/49)、VCAP_2=pin 47、SPI3=PC10/11/12(pin 51/52/53)を含む使用pinを確定した。
- F405の電源pinをVDD=19/32/48/64、VSS=18/63と確定し、VDD各100nF+全体4.7µF以上、VCAP_1/2各2.2µF・ESR<2Ωを要件化した。KiCadシンボルではなくSTデータシートを正本とする記述へ修正した。
- F405固有部を除き、unit board採用品を優先流用する方針を確定した。`LM66100DCKR`、`TLV1117LV33DCYR`、`TCAN1051VDRQ1`、8MHz HSE、VDD/VDDAコンデンサ、GHコネクタ、LED、SWD/UART回路を共通化し、VCAP 2.2µFにも在庫共通化できる`GCM21BR71E225KA73L`を割り当てた。
- `AGENTS.md`、`hardware/README.md`、G474最小回路資料、NUCLEOベンチ試験資料に残っていた「オドメトリ=G474」をF405へ更新した。既存`unit_controller`は差動ステア専用のため、オドメトリへそのまま流用しないことも明記した。

### 現在の状態

- F405採用判断は妥当。Classic CAN 1Mbps、TIM2/TIM3/TIM4 Encoder Mode、USART2、SPI3の機能割当競合はない。
- ドキュメント上のF405 pinoutと必須電源回路は確定し、KiCad回路図へ転記できる状態。
- `hardware/odometry-board/`はG474の旧階層シート断片だけで、F405スキーマへの置換は未着手。

### 次の作業

1. `hardware/odometry-board/`へルート回路図とF405最小回路シートを作り、unit boardの電源/CANブロックを流用して接続する。
2. VCAP用`GCM21BR71E225KA73L`のメーカー特性で実装条件におけるESR < 2Ωを確認する。
3. F405回路図完成後にERCを0件へ収束させ、電源pin、CAN TX/RX、3組のEncoder入力をネットリストで自動照合する。

---

## 2026-07-25 (LEDテープ制御を独立CANノード化)

### やったこと

- LEDテープを中央Teensyの直接DATA配線ではなく、独立したCANノード基板で制御する方針を確定した。
- CANではモード、色、明るさ、速度、状態などの高位コマンドだけを送り、全ピクセルRGBの連続転送は行わず、アニメーションをLEDノード側で生成する要件を追加した。
- LED電力は中央PCBを経由させず、24V分電点から専用ヒューズ経由でLED制御基板へ供給する方針を維持した。

### 現在の状態

- 中央基板にはLED専用DATA線を設けず、LEDノードは拡張CANへ接続する。
- LEDテープは12V WS2815系または24Vアドレサブル系を候補とし、2m・高密度を想定している。電圧、密度、最大電力は製品選定後に確定する。
- LEDノードへの`STM32G474RET6`採用はオーバースペックとして不採用。第一候補は64MHz Cortex-M0+、FDCAN x2、128KB Flash、32pin QFNの`STM32G0B1KBU6N`。2026-07-25確認時点でDigiKey在庫2,768個、少量単価US$4.24。手実装・修理性を優先する場合は同系列LQFP32品を在庫と価格から再確認する。
- DC-DC、枝数、ヒューズ定格、電流監視回路は未選定。

### 次の作業

1. 12V個別アドレス品と24Vセグメントアドレス品からテープを正式選定する。
2. `STM32G0B1KBU6N`の電源、FDCAN、SWD、LED出力、ADCピンを割り当て、QFN32実装性を確認して正式採用する。
3. CANメッセージIDとLED高位コマンドを`docs/communication/COMMUNICATION_NAMING_AND_IDS.md`へ割り当てる。
4. テープ実電力からDC-DC、ヒューズ、AWG20電源線、XT30、基板配線幅を確定する。

## 2026-07-25 (オドメトリ基板 MCUをSTM32F405RGT6へ変更)

### やったこと

- 部室在庫から発掘した`STM32F405RGT6`(LQFP64)をオドメトリ基板のMCUとして採用することを確定した。
  オドメトリ基板はセンサーCAN1系統のみ必要で、ユニット基板がG474を選んだ決め手だった
  「FDCANが2系統必要」という制約が掛からないため成立する。センサーCANはClassic CAN 1Mbps固定
  (CAN FD未使用)なので、F405の`bxCAN`(Classic CAN専用)で要件を満たす。
- データシート(`STM32F405xx/STM32F407xx` Doc ID 022152)のピン定義表を確認し、AMT102用TIM2/TIM3/TIM4
  (PA0/PA1、PA6/PA7、PB6/PB7)、CAN1(PA11/PA12)、SWD(PA13/PA14)、LED(PA5/PB10/PB11)、
  ID DIP(PC6/PC7/PC8)、SPI IMU候補(PC10/PC11/PC12)がG474版と同じGPIO名で使えることを確認した。
- F405固有で新規に必要な回路差分を洗い出した: VCAP_1/VCAP_2用2.2µF×2(必須、省略不可)、
  HSEがPF0/PF1→PH0/PH1へ移動、デバッグUARTがLPUART1(無し)→USART2へ変更、BOOT0がG474の
  GPIO共用(PB8)から専用ピンへ変更、VREF+専用ピンが無く内部でVDDAに直結することを確認した。
  SPI IMU CSのPD2に関する初回確認は誤りだったため、直上のレビュー記録で訂正済み。
- ドキュメントを更新: `docs/electrical/ODOMETRY_BOARD_REQUIREMENTS.md`(MCU記載とF405固有要件の節を追加)、
  新規`docs/electrical/STM32F405_ODOMETRY_PIN_ASSIGNMENT.md`(旧`STM32G474_ODOMETRY_PIN_ASSIGNMENT.md`は
  廃止注記を付けて履歴として保持)、`docs/ARCHITECTURE_DECISIONS.md`(オドメトリ関連行とMCU調達数の更新、
  新規決定行を追加)、`docs/PROJECT_DOCUMENT_INDEX.md`の該当説明文。
- KiCadスキーマ(`hardware/odometry-board/*.kicad_sch`)は未着手。MCUシンボルの差し替えはKiCad GUIで
  公式`STM32F405RGTx`シンボルへ置き換える方針とし、本セッションではドキュメントのみ更新した
  (物理ピン番号はデータシートTable 5のテキスト抽出では折り返しの影響で一部確定できず、
  GPIO名を正本として記載し、物理番号はシンボル配置時に照合する方針とした)。

### 現在の状態

- オドメトリ基板は依然スキーマブロックのみの段階(`.kicad_pro`/`.kicad_pcb`未作成)。MCU変更はドキュメント上で完了、
  KiCad上の反映はこれから。
- ファームウェアのオドメトリ実装はまだ存在しない(`firmware/src`はユニット基板用のSTM32G4専用実装のみ)。
  F405用のクロック・GPIO・USART・bxCANドライバは新規実装が必要になる。
- ユニット基板の調達計画(2026-07-25付BOM等)は旧来の「オドメトリ含め必要4個」を前提に計算済みのままなので、
  次回G474調達を見直す際は「ユニットx3のみで必要3個」に更新すること。

### 次の作業

1. `hardware/odometry-board/STM32G474 Minimum System.kicad_sch`をKiCad GUIで開き、公式`STM32F405RGTx`
   シンボルに差し替えて`STM32F405_ODOMETRY_PIN_ASSIGNMENT.md`の割当で再配線する。VCAP_1/VCAP_2の追加、
   HSE/BOOT0/UARTの回路変更を反映する。
2. 確定済み物理pin番号を回路図へ転記し、STデータシートとネットリストで再照合する。
3. F405向けファーム platform層(クロック初期化、GPIO、USART、bxCAN)を新規実装する。

---

## 2026-07-25 (中央基板 `ESTOP_CTRL`ポート要件追加)

### やったこと

- 中央基板へ24V制御系を収容する方針に合わせ、2個のE-stop操作パネルを1本のハーネスで接続する専用`ESTOP_CTRL`ポートを追加した。
- 暫定6pinを、ハード直列NCループ往復、独立保護した24V LED電源/GND、E-stop 1/2補助接点リターンへ割り当てた。
- コネクタ抜去・断線時にNCループが開いてコンタクタが解放されるfail-safe要件と、LED系短絡が安全ループへ波及しない別保護要件を明記した。

### 現在の状態

- `docs/ARCHITECTURE_DECISIONS.md`と`docs/electrical/CENTRAL_BOARD_REQUIREMENTS.md`へ確定事項として反映済み。
- コネクタはキー付き・ロック付き・60V以上を条件とし、正式型番と電流定格はメインコンタクタの24Vコイル電流確定後に選定する。

### 次の作業

1. メインコンタクタの正式型番とコイル電流を確定する。
2. `ESTOP_LOOP_RETURN`と補助接点入力の絶縁・保護回路を選定する。
3. 中央基板回路図へ`ESTOP_CTRL` 6pin、分離保護、コンタクタドライバを実装する。

## 2026-07-25 (ユニット基板 最新シルク反映・製造ZIP再生成)

### やったこと

- ユーザー更新後の`unit-board.kicad_pcb`を再検証し、追加ロゴ、QR、裏面説明シルクを含む最新版を製造出力へ反映した。
- QRフットプリント名に入っていたSSH URLがKiCadからライブラリIDとして誤解釈される問題を修正した。QR図形・格納内容は変更していない。
- 裏面説明文へミラー指定を追加し、基板外へ伸びていた文字揃えを修正した。既知の基板内シルク差異に対する`lib_footprint_mismatch`通知除外も復元した。
- ロゴフットプリントをB.Cu側へ正しく反転し、完成基板の裏面から正向きに読めることを3Dレンダーで確認した。
- KiCad 10.0.4でERC 0件、DRC 0件、未接続0件を確認した。
- 旧`output/fabrication/unit-board-revA`とZIPを削除し、表面ステンシル用`F.Paste`を含むGerber 10層、PTH/NPTHドリル、IPC-D-356、位置CSV、統計、STEPからなる21ファイルの製造ZIPを再生成した。裏面実装パッドは0個のため空の`B.Paste`は含めていない。
- `tools/kicad/fabricate.ps1`へJLCPCB列名のBOM自動出力を追加した。`unit-board-jlcpcb-bom.csv`は32品目・実装対象60個・Designator重複0。LCSC部品番号は回路図に未登録のため全行空欄で、登録済みメーカー型番は4品目に保持した。BOM追加後の製造ZIPは22ファイル。
- 追加製作4枚を基準に、全60リファレンスを31調達品へ割り当てた`tools/kicad/digikey-bom.ps1`を追加した。汎用値の抵抗・コンデンサにもメーカー型番とDigiKey品番を設定し、漏れ・重複・空品番0を自動検査する。
- 4枚の実装必要数240点に対して、受動部品は20%以上かつ2個以上、その他は1個の予備を加え、注文数334点とした。購入済み`STM32G474RET6`は手持ち10個を計上し、必要4個・追加注文0個とした。
- DigiKey投入用30行の`unit-board-digikey-bom-4boards.csv`と、手持ち・必要数・予備を含む31行の`unit-board-procurement-plan-4boards.csv`を製造スクリプトから自動生成し、製造ZIPへ同梱した。
- 今後のG474/CAN系基板でも流用できる`LabStock`調達プロファイルを追加した。4枚の必要数240点は維持しつつ、100nF・0Ω・1kΩは各100個、10k/22k/33kは各50個、その他の受動部品は20～25個、コネクタ・IC・保護部品は用途に応じ10～30個を在庫目標とし、注文合計887点とした。
- 最低限版334点に加えて、在庫込みの`unit-board-digikey-bom-4boards-plus-stock.csv`と数量根拠を含む`unit-board-procurement-plan-4boards-plus-stock.csv`を自動生成する。高価な`STM32G474RET6`は手持ち10個で在庫目標を満たすため、どちらの購入CSVでも追加0個。
- DigiKey調達で使用するコンデンサAVLとLM66100/TLV1117LV周辺の正式型番を、正本の部品選定資料へ2026-07-25付で追記した。HSE/VREF+はC0G、ADCフィルタはX7Rという回路要件を維持している。

### 現在の状態

- 最新製造ZIPは`output/fabrication/unit-board-revA.zip`。
- 最新ZIPは最低限版と共通在庫版のDigiKey BOM計4ファイルを含む26ファイルで、DRC 0件・未接続0件を再確認済み。
- ZIPのSHA-256は`eb22ae9fc2c7c63369b402a837e13c7f1a63ab9febd1684b24c7d99eb1dbc7b0`。

### 次の作業

1. 発注先オンラインビューアへZIPを投入し、表裏シルク、QR、内層、PTH/NPTH、外形の向きを最終目視確認する。
2. 発注先の4層標準stackupと現行1.6mm設定を照合する。
3. 通常はDigiKeyへ`unit-board-digikey-bom-4boards-plus-stock.csv`を投入する。予算を抑える場合だけ最低限版`unit-board-digikey-bom-4boards.csv`を使い、注文時点の在庫、価格、梱包単位、特にJST GH 3極/6極を再確認する。

## 2026-07-24 (ユニット基板 DRC/ERC 0件・配線収束)

### やったこと

- 前セッションの配置・配線済み`unit-board.kicad_pcb`を保持したまま、消失していた`ADC_ANALOG`、`CAN`、`HSE`、`POWER_3V3`、`POWER_5V`、`SPI`ネットクラス、現行階層ネットへの割当、配線幅・ビアプリセット、製造最小制約を`unit-board.kicad_pro`へ復元した。
- 全ネットクラスの最小離隔を製造最小0.20mmへ統一した。5V/3.3Vの既定線幅0.75/0.40mmは維持し、狭ピッチパッド直近だけ0.20mmへネックダウンした。
- `unit-board.kicad_dru`はネットクラスと重複していた片側評価のgeometryルールを削除し、HSEのF.Cu限定・ビア禁止だけを残した。
- HSE直下のIn1.Cu keepoutから`copperpour not_allowed`だけを外し、信号配線・ビア禁止を維持したままGND planeを再注入した。
- NRSTのデバッグコネクタ側とMCU側をIn2.Cuで接続し、TLV1117のpin 2と放熱タブを接続した。電源幹線、3.3V幹線、LED_COMM、U3/D6周辺などを再配線して、未接続、dangling via、短絡、交差、クリアランス違反を0件へ収束させた。
- 密集して読めなかった64個のReferenceシルクを非表示にし、部品番号はF.Fab・回路図・BOMへ残した。SW1と重複していた小型部品4個の外形シルクをF.Fabへ移し、シルク重複・銅箔重なり・基板端警告を0件へ収束させた。
- 意図的にライブラリ原本とシルクだけ異なるため、`lib_footprint_mismatch`は通知対象外とした。その他のパッド、courtyard、銅箔、接続検査は有効のまま。
- SW1の壊れた裸ファイル名モデル参照とPC固有の絶対パス参照を整理し、表示できていたモデルの姿勢（Y=0、Z=0.25mm、X=-90°）を保持した単一の`${KIPRJMOD}/../lib/DifferentialSwerve.3dshapes/JS102011SAQN.stp`参照へ統一した。プロジェクト内フットプリント原本にも同じ3D定義とF.Fab外形を反映し、SW1のライブラリ差異を解消した。
- 消失していた追加6ネットクラスと現行階層ネット16件への割当を再復元した。全クラスclearance 0.20mm、製造最小via 0.60/0.30mm、annular ring 0.15mmを適用し、電源既定幅は3.3V=0.40mm、5V=0.75mmを維持した。
- ECS公式ECX-33Q、Littelfuse/C&K公式JS、JST公式GH図面と照合し、Y1はpad 1/3=信号・2/4=GND、SW1は端子2.5mm pitch・1.2x2.5mm land・φ0.9mm NPTH中心間6.8mm、J7/GH3はpad寸法・pin 1方向が基板と一致することを確認した。
- `tools/kicad/fabricate.ps1`を追加し、Gerber 9ファイル、PTH/NPTH Excellon、ドリルマップ/集計、IPC-D-356、位置CSV、統計、実装済みSTEP、製造ZIPを`output/fabrication/unit-board-revA`へ生成した。gbrjob参照欠落0、Gerber/Excellon終端異常0、STEP内SW1モデル有りを確認した。
- 操作・デバッグ用シルクを追加した。表面はLED `PWR/RUN/COM/ERR`、MCU pin 1、`TERM`、UNIT IDの`1/2/4`を部品近傍へ表示し、裏面は基板名、LED凡例、J1〜J7・SW1・SW3用途一覧を表示した。
- 裏面に`https://github.com/Posaka-Y/Differential-Swerve-Drive`を示す約12.25mm角のQRコード（誤り訂正H）をB.SilkSの矩形として追加した。SW1位置決め穴とのシルク干渉を避け、3Dレンダーで外観を確認した。リンク先は現在privateのため、一般利用前にGitHub側をpublicへ変更する。
- KiCad 10.0.4で`tools/kicad/check.ps1 -FailOnViolations -OutputDirectory output/kicad`を実行し、ERC 0件、DRC 0件、未接続0件を確認した。最終3Dレンダーも目視し、部品Referenceの重なりが解消したことを確認した。

### 現在の状態

- `output/kicad/unit-board-erc.rpt`と`output/kicad/unit-board-drc.rpt`は0 violation。
- HSEはF.Cu・ビアなしを維持し、直下のIn1.CuはGND plane、他信号のtrack/via/pad/footprintは禁止。
- 電気系・シルク系ともKiCad DRCは0件。部品位置、基板外形、銅箔形状は3Dレンダーで読込み可能。
- SW1の3Dモデルはプロジェクト相対パスから1個だけ読み込まれ、別PCへ移しても同じ構成で解決できる。
- 裏面QRコードはGitHubリポジトリのHTTPS URLを直接保持し、Gerberへ画像依存なしで出力される。
- 製造データ一式と機体CAD照合用`unit-board.step`は生成済み。ただしPCBのphysical stackupは1.6mm・4層・各銅35µmの仮設定で、発注先標準stackupとの照合は未完了。
- ReferenceはF.SilkSへ出さない方針のため、実装時はF.Fabプロット、回路図、BOMを併用する。

### 次の作業

1. `output/fabrication/unit-board-revA/unit-board.step`を機体CADへ挿入し、45x45mm外形、39x39mm取付穴、SW1張出し、GH挿抜/曲げ空間、最大高さを承認する。
2. 発注先の4層標準stackupへ合わせて層厚・銅厚・表面処理・最小穴径を確定し、必要ならCAN配線条件を再確認して製造ZIPを再生成する。
3. KiCad Gerber Viewerまたは発注先オンラインビューアで、全9 GerberとPTH/NPTHの層対応・向き・外形を目視確認する。
4. 組立図ではF.FabのReferenceを出力し、初号機の電源投入前に5V/3.3V/GND短絡、NRST、HSE、両CAN終端を確認する。

## 2026-07-23 (ユニット基板 4層・配線ルール初期設定)

### やったこと

- `unit-board.kicad_pcb`を4層構成として整理し、`In1.Cu`をGND plane、`In2.Cu`をPower / Signal層として命名した。板厚は既定の1.6mmを維持した。
- PCBの製造最小制約を試作しやすい値へ設定した: clearance 0.20mm、silk clearance 0.15mm、silk文字線幅0.12mm、via最小径0.60mm、annular ring最小0.15mm。外形銅箔離隔0.50mmは維持した。
- 配線幅プリセット0.20/0.25/0.40/0.50/0.75/1.00mm、ビアプリセット0.60/0.30、0.70/0.35、0.80/0.40mmを追加した。
- `CAN`、`POWER_5V`、`POWER_3V3`、`HSE`、`SPI`、`ADC_ANALOG`ネットクラスを追加し、現行ネット名へ割り当てた。
- `unit-board.kicad_dru`を追加し、CAN、5V、3.3V、HSE、アナログの最小線幅・離隔とHSEのF.Cu限定・ビア禁止ルールを定義した。KiCad 10で非対応の`constraint layer`を使わず、条件式+`disallow track/via`で記述した。
- `JS102011SAQN.stp`を`hardware/lib/DifferentialSwerve.3dshapes/`へ追加し、専用footprintと基板内footprintの3Dモデル参照を`${KIPRJMOD}`基準の相対パスへ修正した。

### 現在の状態

- `.kicad_pro`はNode.jsのJSONパーサで構文正常を確認済み。
- 製造会社固有の4層stackup、CAN差動インピーダンス、基板外形、取付穴、ゾーン形状は未確定のため設定していない。
- Windows版KiCad CLIによる読込み/DRCは、WSL interopの`UtilBindVsockAnyPort`エラーで起動できず未確認。基板にはまだ外形・配線・ゾーンがない。

### 次の作業

1. KiCad GUIで基板を開き、Board SetupのPhysical Stackup、Constraints、Net Classes、Custom Rulesが読み込まれることを確認する。
2. 機体CADから基板外形、取付穴、コネクタ差込方向、高さ制限を確定する。
3. 外形確定後に配置し、`In1.Cu`全面GND、`In2.Cu`の5V/3.3Vゾーン、表裏GNDゾーンとスティッチングビアを作成する。
4. 発注先決定後、その標準4層stackupを入力し、必要ならCAN配線幅/間隔を再計算する。

## 2026-07-23 (ユニット基板 ERC 0件・ネットリスト整合修正)

### やったこと

- KiCad 10.0.4で現行ユニット基板を再解析し、開始時のERC 52エラー/19警告を0エラー/0警告まで収束させた。
- 親子階層名と方向を修正した: `PWR_5V`、`CAN_TX/RX`、`SPI3_MOSI/MISO`、`LED_RUN/COMM/ERR`、`DBG_TX/RX`。誤記`5.5V`、`CANFD]_TX`も除去した。
- MCUのRev.A未使用GPIO 26本へNo Connectを設定し、LM66100のSTにも意図的NCを設定した。入力5V/GNDとVDDAへ`PWR_FLAG`を追加した。
- ERCでは検出できなかったCAN論理方向の逆接続をネットリストで発見し、両バスとも`MCU TX -> TCAN TXD(pin 1)`、`TCAN RXD(pin 4) -> MCU RX`へ修正した。
- GH2電源入力のピン極性を`J1-1=PWR_5V_IN`、`J1-2=GND`へ修正した。
- 中央CANへ2個目のGH3(J3)を追加し、J2/J3を`COMM_A/COMM_B/GND`の並列パススルーにした。C620側J4/J5は`C620_CAN_H/L/GND`で維持した。
- 主要ローカルネットを`PWR_5V_IN`、`COMM_A/B`、`C620_CAN_H/L`、`HSE_IN/OUT`、`VDDA_A`、`VREF_PLUS`へ正規化した。
- デバッグGH6を確定部品`BM06B-GHS-TBT`と垂直footprintへ修正し、COMM/ERR LEDを黄`LTST-C190KSKT`/赤`LTST-C190KRKT`、ADCクランプを`BAT54SLT1G`、22kΩを`RC0603FR-0722KL`表記へ揃えた。
- 45箇所の主要ピン接続、MCU NC 26本、BOM 62部品のValue/Footprint有無、Ref重複なしをネットリストで自動確認した。
- `tools/kicad/check.ps1`へ`-SkipDrc`を追加し、PCB未着手でも`-FailOnViolations -SkipDrc`で回路図だけを厳格確認できるようにした。使用例を`hardware/README.md`へ追記した。
- 最終ERCレポート、ネットリスト、回路図PDFを`output/kicad/`へ、回路図PDFを`output/pdf/unit-board-schematic.pdf`へ出力した。

### 現在の状態

- `tools/kicad/check.ps1 -FailOnViolations -SkipDrc -OutputDirectory output/kicad`は成功し、ERCは0エラー/0警告。
- 電源、中央CAN、C620 CAN、AMT22、SWD/UART、UNIT_ID、LED、5V監視の主要ピン番号はネットリスト上で正本と一致している。
- PDF/SVG書き出しは成功したが、この実行環境にPoppler/Python画像レンダラと利用可能なアプリ内ブラウザがなかったため、ページ画像による目視レビューは未完了。
- PCBは空のままで、DRC/部品配置/配線は未着手。`untitled.kicad_sch`の要否も未確定のため削除していない。

### 次の作業

1. KiCad GUIまたはPDFレンダラのある環境で全6ページを目視し、ラベル重なり、線の交差、可読性を確認する。
2. 正本で要求する主要テストポイント(`PWR_5V_IN`、`PWR_5V`、3.3V、`VDDA_A`、GND、NRST、BOOT0、SWO、両CAN線)を回路図へ追加する。
3. CAN終端抵抗、LED抵抗、残りの受動部品Valueを正式型番表記へ揃え、JS102011SAQN footprintのメーカー推奨ランド照合を完了する。
4. `untitled.kicad_sch`をGUIで確認し、不要な複製なら削除する。
5. 回路図目視レビュー後、PCB外形・配置・配線へ進み、DRCを収束させる。

## 2026-07-22 (ユニット基板 全ブロック回路図入力完了)

### やったこと

- KiCad GUIでユニット基板の全機能ブロックを入力した: 5V入力・逆接保護・3.3V LDO、CAN、STM32G474最小構成、HSE/NRST/BOOT0、AMT22 SPI、デバッグGH6、UNIT_ID 3bit DIP、状態LED、5V監視ADC。
- UNIT_ID DIPをOmron `A6S-3104-H`、KiCad標準footprint `Button_Switch_SMD:SW_DIP_SPSTx03_Slide_Omron_A6S-310x_W8.9mm_P2.54mm`で配置した。
- 5V監視をLM66100後段の`PWR_5V`から33kΩ/22kΩで分圧し、10nFとBAT54Sクランプを介してPA0へ入れるブロックとして入力した。
- KiCad CLIで全階層BOMとERCを試行し、階層ラベル未設定を主因としてエラー57件・警告24件であることを確認した。

### 現在の状態

- 全ブロックの部品配置とブロック内回路入力は完了したが、親子間の階層ピン/階層ラベル設定とルートシート配線は未完了。このため現時点のERC違反は完成判定に使用しない。
- 次回照合事項: 2系統CANのインスタンス/信号名、未使用MCUピンのNo Connect、電源のPWR_FLAG、意図的NC、デバッグGH6の型番・向き、COMM/ERR LEDのValue、R14の正式型番表記、BAT54SLT1GのValue。
- `hardware/unit-board/untitled.kicad_sch`は複製候補のため、確認できるまで未追跡のまま残している。

### 次の作業

1. 各子シートへ階層ラベルを設定し、親シートの階層ピンと1:1で接続する。
2. 中央CAN/C620 CANの2インスタンス化とネット名を正本に合わせる。
3. 未使用ピン、PWR_FLAG、意図的NCを整理し、Value/Footprintを最終照合する。
4. `tools/kicad/check.ps1 -FailOnViolations`でERCを0件まで収束させ、PDF回路図をレビューする。
5. 階層化した全回路図の接続・ERC・PDFレビュー完了後、ユニット（差動ステアモジュール）基板のPCB作成へ移行する（基板外形、部品配置、配線、DRC、製造出力の順）。

## 2026-07-22 (ユニット基板 Block 1・2 回路図入力)

### やったこと

- KiCad GUIでBlock 1「Power Input 3.3V」を`hardware/unit-board/power_3v3.kicad_sch`へ入力し、親`unit-board.kicad_sch`から階層シートとして参照した。
- Block 1へJST GH 2pin入力、`LM66100DCKR`逆接・逆流保護、`TLV1117LV33DCYR` 3.3V LDO、入力/出力コンデンサを配置した。LM66100の`CE_N=VOUT`、TLV1117のtab=VOUT、2.2uF/10uFは0805、100nFは0603の方針で入力した。
- KiCad GUIでBlock 2「CAN Interface」を`hardware/unit-board/can_interface.kicad_sch`へ入力し、親回路図から階層シートとして参照した。
- Block 2へ`TCAN1051VDRQ1`、`ESD2CAN24DBZRQ1`、100nF x2、120Ω終端、`JS102011SAQN`終端スイッチ、JST GH 3pin x2を配置した。TCANのVCC=5V/VIO=3.3V/S=GND、スイッチpin 1=NC/pin 2=COM/pin 3=NOを確認した。

### 現在の状態

- Block 1・2の回路図ファイルは保存済みだが、AIによるS式接続照合とERCは未実施。親子間は階層ラベル/階層ピンで明示接続する必要がある。
- `hardware/unit-board/untitled.kicad_sch`が`power_3v3.kicad_sch`と同じサイズで未追跡のまま残っている。不要ファイルか確認するまで削除しない。
- `JS102011SAQN`専用footprintはメーカー推奨ランドとの最終照合が未完了。C620側コネクタの型番・個数・ピン順も未確定。

### 次の作業

1. Block 1・2のValue、Footprint、ピン接続、階層ラベル方向を正本と1:1照合する。
2. `untitled.kicad_sch`が不要な複製かKiCad GUIで確認し、必要なら正式名へ変更、不要なら削除する。
3. Block 3以降の回路図入力を進め、区切りごとにERCを実行する。

## 2026-07-20 (回路図分業方針の確認・AMT22コネクタGH化・旧XH/4線記述の掃除)

### やったこと

- KiCad作業の分業を再確認: AIは描かず「前(資料・ライブラリ・制約表)と後(S式照合・ERC/DRC・BOM)」、回路図手描き・配置・配線は人がGUIで行う。ピン割当の根拠(ST公式open_pin_data照合+NUCLEO実機動作実績)と、CAN/電源/MCU最小構成の部品選定書が揃っていることを確認。
- AMT22中継コネクタを旧`JST XH 6pin`から横挿しGH 6pin `SM06B-GHS-TB`+`GHR-06V-S`+`SSHL-002T-P0.2`へ確定・修正(`CARRIER_BOARD_REQUIREMENTS.md`)。AMT22と同ピン順でストレート結線、Pico-Lock⇔GH変換ハーネス自作。AMT22はVIH 2.0V/出力High 3.3Vのため全信号直結・レベルシフタ不要(2026-07-02確認済み)。
- DOC-01/DOC-03の旧記述を掃除して解消済みへ: `CARRIER_BOARD_BUILD_PLAN.md`の旧4線一体コネクタ→GH2電源+GH3 CAN x2、`CARRIER_BOARD_REQUIREMENTS.md`の「制御4線」表現を現行ハーネス構成へ、`hardware/README.md`の旧TCAN332記述→`TCAN1051VDRQ1`。
- ユニットID設定を**3bit DIPスイッチに確定**(UNIT-03/ODOM-06解消): PC6-8、内部プルアップ、ON=GND(読み値反転)、起動時に1回読取りRUN LEDをID回数点滅、全OFF(ID=0)は未設定エラー扱い。オドメトリ基板も同一ブロックでunitId=4(0b100)を設定。Flash保存一本化案は不採用。ARCHITECTURE_DECISIONSへ追記済み。DIP型番は部品選定で確定する。
- 回路図の下敷きはNUCLEO回路図ではなく自前の部品選定書3本+candleLightFD/ARK CANnode参考回路とする整理を確認(NUCLEOはST-LINK給電・HSE未実装で回路前提が異なる。実証済みなのはピン割当とファーム)。

- ユニット基板の回路図転記用リファレンス`docs/electrical/UNIT_BOARD_SCHEMATIC_REFERENCE.md`を新規作成: 階層シート6分割案、シート内配置とネットラベル方針、RefDes番号帯割当(シート別100番台)、全接続表(Net/部品/ピン名/ピン番号/電圧)、ブロック別部品一覧、ERCで検出できない誤り8項目(TLV1117タブ=VOUT、LM66100 CE_N=VOUT意図的、BAT54S向き、TCAN Sピン等)、未確定事項12件(C620 CANコネクタ型番が部品リスト未記載と判明、等)。索引9.97へ登録。

### 現在の状態

- docs/electricalの文書間不整合はDOC-01〜04すべて解消。ユニット基板の回路図は「転記リファレンス+ピン表+部品選定書3本」を開けば描ける状態。
- `SM06B-GHS-TB`は既採用のGHシリーズ(SM02B/SM03B)と同系列の6pin横挿し品。発注時に他コネクタと同様の現物確認を行うこと。

### 次の作業

1. KiCad 10 GUIでライブラリロード確認(前回持ち越し)→ G474共通ブロックから回路図手描き開始。
2. 描き終わった回路図をAIがS式でピン表・要件書と突き合わせ、ERC実行。

## 2026-07-20 (KiCad CLI検証環境)

### やったこと

- Windows版KiCad 10.0.4の`kicad-cli`で、`unit-board`のERC、回路図PDF出力、DRCが実行できることを確認。
- `tools/kicad/check.ps1`を追加。既定でユニット基板を検証し、対象プロジェクトと出力先を引数で変更可能にした。
- 厳格確認用に`-FailOnViolations`を用意し、ERC/DRC違反を終了コードへ反映できるようにした。
- `hardware/README.md`へ実行方法を追記した。
- `hardware/blocks/g474_minimum.kicad_sch`を作成し、KiCad 10標準`STM32G474RETx`シンボルへ正式Value `STM32G474RET6`とLQFP64 footprintを設定した。
- ユニット基板ルートへ`G474 Minimum`階層シートを組み込み、確定ピン割当に沿ったCAN、AMT22、SWD/UART、UNIT_ID、LED、予約I2C/SWOの階層I/Oを追加した。
- Rev.Aで使わない26本のGPIOにNo Connectを明示した。I/O名と親子階層ピンはKiCad CLIで解析・PDF出力できることを確認した。
- VDD x4とVBATを`PWR_3V3`へまとめ、VSS x4とVSSAを`GND`へ接続した。中間VDD枝のT字交点には明示ジャンクションを置き、未接続ワイヤ警告0件を確認した。
- `VDDA_A`、`VREF_PLUS`、`HSE_IN`、`HSE_OUT`、`BOOT0`をローカルネットとして分離した。親シートには`PWR_3V3`と`GND`階層ピンを追加した。
- HSE回路を追加: `ECS-80-8-33Q-JES-TR`、10pF x2、OSC_OUT側0Ω調整抵抗を`HSE_IN/HSE_XO/HSE_OUT`へ接続し、水晶ケースGND pin 2/4も接続。HSE部品単体のERC違反0件を確認した。
- VDD/VBAT/VDDA/VREF+用にFB1、R2、C3～C12を配置し、電源ネットへ接続した。FB1は`PWR_3V3`→`VDDA_A`、R2は`VDDA_A`→`VREF_PLUS`。
- NRST用C13、BOOT0用R3、デバッグGH6用J1を配置した（値・footprint・配線は未設定）。

### 現在の状態

- 保存済み`unit-board.kicad_sch`はG474共通階層シートを含み、HSE回路は接続済み。電源デカップリングとReset/BOOT/debugは作成途中。
- 終了時ERCはエラー38件・警告30件。未配線部品を含む作成途中の値で、完成判定ではない。
- C5がオフグリッド。C6～C8はグリッドへ移動済みだが、旧ラベル位置までのワイヤ端が残り、off-grid警告は計6件。KiCadロックファイルなし。
- `unit-board.kicad_pcb`も空のため、DRCはEdge.Cutsなしを1件報告する。
- KiCad GUIで`unit-board`が開かれており、`unit-board.kicad_pro`にはユーザー作業由来の未コミット変更があるため、本セッションでは上書きしていない。

### 次の作業

1. C5をグリッドへ移動し、C6～C8移動前位置へ残ったワイヤ/ラベルを整理する。
2. C3～C12、FB1、R2の未設定Value/footprintを正式型番へ揃える。
3. NRST 100nF、BOOT0 10kΩ pull-down、GH6デバッグ配線を完成させる。
4. 回路完成後に未使用ピンと階層I/Oを再確認し、`check.ps1 -FailOnViolations`でERCを0件にする。

## 2026-07-19 (SamacSysライブラリ取り込みへ方針変更)

### やったこと

- ユーザー要望により、標準ライブラリ流用(前エントリ)からSamacSysダウンロード品の取り込みへ変更。
- Library Loader v2.50が導入済み・アカウント設定済み(ECAD=KiCad、監視=Downloads、自動起動OFF)であることを確認。Chrome自動操作ではCSEのダウンロードがトラッキングリダイレクトで失敗し、ユーザーが別ブラウザで`LIB_TCAN1051VDRQ1/ESD2CAN24DBZRQ1/LM66100DCKR/JS102011SAQN.zip`を手動取得。
- 4部品の`KiCad/*.kicad_sym`を`hardware/lib/DifferentialSwerve.kicad_sym`へ統合。SamacSys原品の誤りを修正:
  - TCAN1051VDRQ1のpin 5が`NC`になっていた(V系列はVIO)→ `VIO`/power_inへ修正
  - 全pinが`passive`だった → データシート通りのelectrical typeへ設定
  - JS102011SAQNのpin 1(切替接点)が`no_connect`型だった → passiveへ修正
  - Footprint欄が裸のIPC名で解決不能 → 照合済みKiCad標準footprintへ変更
- JS102011SAQNのfootprint(SamacSys、2.5mmピッチ3pad+NPTH x2)を`DifferentialSwerve.pretty`へ取り込み(メーカー図面照合は未実施)。
- `LIBRARY_MANIFEST.md`を全面更新(取り込み記録・修正内容・未照合事項)。S式バランス検証済み。

### 現在の状態

- 専用ライブラリはシンボル4個(SamacSys由来+修正)、footprint 2個(Harwin照合済み、JS102011未照合)。
- pin番号・名称はデータシート照合済みの内容と一致。KiCad 10 GUIでのロード確認は未実施。
- 余談: Library Loaderの設定XML(`%APPDATA%\SamacSys\Library Loader\LibraryLoader.xml`)にCSEパスワードが平文保存されている。使い回しなら変更推奨。

### 次の作業

1. KiCad 10 GUIでライブラリをロードし、4シンボル表示とsymbol checkerを確認、保存し直してフォーマット正規化。
2. JS102011SAQNのfootprintをLittelfuse/C&K図面と照合して確定する。
3. G474共通回路図の作成へ着手する。

## 2026-07-19 (自作シンボルを標準ライブラリへ置き換え)

### やったこと

- `hardware/lib/DifferentialSwerve.kicad_sym`の自作シンボル3個を削除し、KiCad 10同梱の標準ライブラリシンボルへ代替。
  - `TCAN1051VDRQ1` → `Interface_CAN_LIN:TJA1051T-3`(8pin全て一致を照合済み。Value書き換えで使用)
  - `ESD2CAN24DBZRQ1` → `Diode:SM712_SOT23`(1/2=ライン、3=GNDでpin番号一致。Value書き換えで使用)
  - `LM66100DCKR` → `Power_Management:LM66100DCK`(同一部品の公式シンボル。定義も自作版と同一)
- 3シンボルとも既定footprintが要件(SOIC-8 3.9x4.9/SOT-23/SC-70-6)と一致することを確認。footprint再割当不要。
- `LIBRARY_MANIFEST.md`を更新(収録表・標準部品表・置き換え照合記録)。`unit-board.kicad_sch`は空でdocs側にも他参照なしのため影響なし。

### 現在の状態

- 専用シンボルライブラリは空(将来の特殊部品用の器として維持)。専用footprintは`Harwin_S1751-46R`のみ。
- LM66100は完全一致だが、TJA1051T-3/SM712_SOT23は別型番名のシンボル流用のため、回路図配置時にValueを正式型番へ書き換える運用。

### 次の作業

1. KiCad 10 GUIで標準3シンボル+`DifferentialSwerve.pretty`のロードを確認する。
2. `JS102011SAQN`推奨land patternのGUI照合とfootprint追加(継続)。
3. G474共通回路図の作成へ着手する。

## 2026-07-19 (KiCad/Codex連携調査)

### やったこと

- KiCad内蔵のCodex公式チャットパネルは現時点でなく、第三者製`KiCad AI Assistant`はOpenAI APIキーと別課金が必要であることを確認。
- Windows版KiCad 10に`C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`が同梱済みであることを確認。
- 現在のWSLセッションからWindows EXEを起動するとWSL interopのvsockエラーになることを確認。

### 現在の状態

- KiCad CLIの追加インストールは不要。Windows側からERC/DRC/製造出力へ利用できる見込み。
- WSL上のCodexからの直接実行は未成立。次回はWindows版Codexから`kicad-cli.exe`を呼び出して確認する。

### 次の作業

1. Windows版Codexでリポジトリを開き、`kicad-cli.exe version`を実行する。
2. KiCadライブラリをGUIでロードして初版部品を確認する。
3. 回路図作成後、ERC/DRCをまとめて実行するPowerShellスクリプトを整備する。

## 2026-07-19 (部品ライブラリ初版レビュー)

### やったこと

- `hardware/lib/`初版を公式データシートと1:1照合レビュー。TI 3部品とHarwin図面のPDFを取得し`hardware/reference/datasheets/`へ保存(ti-tcan1051.pdf、ti-esd2can24-q1.pdf、ti-lm66100.pdf、harwin-s1751r-drg-02202.pdf)。
- ピン照合結果: `TCAN1051VDRQ1`(SLLSET0D)、`ESD2CAN24DBZRQ1`(SLVSFW5D)、`LM66100DCKR`(SLVSEZ8A)の3シンボルともピン番号・名称・electrical typeが完全一致。標準footprint割当(SOIC-8 3.9x4.9/SOT-23/SC70-6)も各パッケージ図と一致。`S1751-46R`のpad 3.45x1.85mmはHarwin DRG-02202の推奨pad layoutと一致。全ファイルのS式構文バランスOK。
- 修正1: `sym-lib-table`/`fp-lib-table`のURIを`${KIPRJMOD}/`直下→`${KIPRJMOD}/../lib/`へ変更。テーブルは各基板プロジェクトディレクトリへコピーして使うテンプレートである旨をマニフェストへ追記。
- 修正2: `Harwin_S1751-46R.kicad_mod`のsilk線をy=±1.0→±1.15へ移動(pad縁との隙間が0.015mmしかなく、solder mask expansionでsilk clip警告/pad上印刷になるため)。
- マニフェストへ照合記録(2026-07-19)を追加。
- レビュー指摘を受け、LM66100の`CE_N`接続をGNDからVOUTへ変更。TIデータシート8.3節のRPP+RCB構成として逆極性保護と逆流遮断を両立する方針を電源選定書、ユニット要件、確定事項へ反映。

### 現在の状態

- シンボル・footprintの寸法/ピンはデータシート照合済み。KiCad 10 GUIでのロード確認とchecker実行は未実施(kicad-cliなし)。ファイルはKiCad 8世代フォーマットのため、GUIで開いて保存し直すと現行フォーマットへ正規化される。
- LM66100の`CE_N`接続はVOUTへ確定し、レビューで見つかった文書不整合は解消済み。
- 軽微(許容範囲として未修正): footprintのcourtyard余白がpad縁から0.1mm(KiCad慣例0.25mm)。

### 次の作業

1. KiCad 10 GUIで`hardware/lib`をロードし、3シンボル表示・footprint link・checkerを確認、保存し直してフォーマット正規化。
2. `JS102011SAQN`推奨land patternのGUI照合とfootprint追加。
3. ライブラリGUI確認後、G474共通回路図へ着手。

## 2026-07-19 (KiCad必要部品ライブラリ初版)

### やったこと

- 回路図作成前に、回路ではなく必要部品ライブラリだけを整備する方針へ変更。
- `hardware/lib/DifferentialSwerve.kicad_sym`へ`TCAN1051VDRQ1`、`ESD2CAN24DBZRQ1`、`LM66100DCKR`の正式pinout付きシンボルを追加。
- Harwin `S1751-46R`のメーカー推奨pad 3.45x1.85mmに基づくリフロー用footprintを追加。
- `hardware/lib/LIBRARY_MANIFEST.md`へ、専用ライブラリとKiCad標準ライブラリの使い分け、STM32/TLV1117/BAT54S/JST GH/水晶の割当を記録。
- 特殊footprintを寸法推測で作らないため、`JS102011SAQN`はメーカー図面とのKiCad上照合まで保留。

### 現在の状態

- 最初のG474/CAN/電源回路に必要な専用シンボル3個とテストポイントfootprintを作成済み。
- この環境には`kicad-cli`がないため、KiCad 10 GUIでのライブラリロード、symbol checker、footprint checkerは未実施。

### 次の作業

1. KiCad 10 GUIで`hardware/lib`を読み込み、3シンボルの表示・pin type・footprint linkを確認する。
2. `JS102011SAQN`の公式推奨land patternをGUI寸法で照合してfootprintを追加する。
3. 必要になった時点でJST GH公式footprintとの差分、TCAN/ESD/LM66100の1:1 pinoutレビューを行う。

## 2026-07-19 (G474 Reset・BOOT・ADC監視・表示部品選定)

### やったこと

- NRSTを内部weak pull-up+100nF、BOOT0を10kΩ pull-down+BOOT/3V3隣接SMTテストポイントに確定。常設Resetボタンと2.54mm BOOTジャンパは不採用。
- 5V監視を33kΩ/22kΩ(0.4倍)、10nF、`BAT54SLT1G`上下クランプでPA0へ入れる構成に確定。
- G474基板表示をPWR/RUN/COMM/ERRの4個とし、Lite-On C190シリーズ緑/緑/黄/赤と1kΩを選定。
- 主要テストポイントをリフロー対応`S1751-46R`、補助信号を1.0～1.5mm露出銅padに確定。
- `STM32G474_MINIMUM_CIRCUIT_PART_SELECTION.md`へ回路、定数、配置条件、実機確認を追記。

### 現在の状態

- G474最小構成の主要部品選定は完了。共通回路図をKiCadへ起こせる状態。
- 中央基板固有のLED、テストポイント数、5A主入力保護は別途選定が必要。

### 次の作業

1. KiCadのG474共通階層シートを作成し、電源/HSE/Reset/BOOT/SWD/ADC監視をERCする。
2. CAN共通階層シートと5V入力/LDO階層シートを作成して共通ブロックを接続する。
3. PDF出力でピン番号、極性、ネット名、部品型番を人とレビューする。

## 2026-07-19 (STM32G474 HSE・アナログ電源部品選定)

### やったこと

- `docs/electrical/STM32G474_MINIMUM_CIRCUIT_PART_SELECTION.md`を追加。
- HSEを`ECS-80-8-33Q-JES-TR` 8MHz、負荷容量をC0G 10pF x2の初期値に確定。CL式とworst-case gmcrit約1.14mA/Vを記録。
- VDDAフェライトを`BLM18AG601SN1D`、各VDD 100nF、全体4.7uF、VDDA 100nF+1uF、VREF+ 10nF+1uFの正式部品まで選定。
- 水晶、デカップリング、VDDA/VREF+の配置配線制約と、温度・HSE起動・ADCノイズの実機確認項目を明文化。

### 現在の状態

- G474共通ブロックはCAN、5V入力保護、3.3V LDO、HSE、VDDA/VREF+、デバッグGH6まで主要部品が確定。
- HSE負荷容量は回路図初期値10pFで、PCB完成後に8.2/10/12pFから最終調整する。

### 次の作業

1. G474のNRST、BOOT0、状態LED、5V監視ADC、テストポイント部品を確定し、最小構成回路を閉じる。
2. 共通階層シートの回路図をKiCadへ作成し、ERC/PDFレビューする。
3. 試作基板でHSE起動余裕、周波数偏差、VDDAノイズを測定する。

## 2026-07-19 (5V共通電源ブロック部品選定)

### やったこと

- `docs/electrical/POWER_5V_COMMON_BLOCK_PART_SELECTION.md`を追加し、G474基板の入力保護、3.3V LDO、中央基板のG474枝PPTC、GH2、枝LEDを正式選定。
- G474基板の逆接・逆流保護を`LM66100DCKR`、LDOを`TLV1117LV33DCYR`、中央のユニットx3+オドメトリ枝を`1206L050/15YR`に確定。
- 5V横挿しコネクタを`SM02B-GHS-TB`、表示LEDを`LTST-C190KGKT`+1.5kΩに確定。
- `TCAN1051V`のVCCが5Vであることを反映し、旧3.3V負荷見積りを修正。LDO損失とPPTC温度derating、配置配線・実機確認条件を明文化。
- 1.5AのLM66100を中央5A主入力へ使わないこと、0.5A PPTCをTeensy枝へ自動流用しないことを明記。

### 現在の状態

- CAN共通ブロックとG474用5V/3.3V共通電源ブロックは正式型番まで確定。
- 中央5V主入力の逆接/逆流保護、Teensy枝の保護定格、XT30基板側正式型番は未確定。

### 次の作業

1. STM32G474の8MHz HSE水晶、負荷容量、VDDAフェライトビーズ、デカップリングを正式選定する。
2. 各G474基板の5V/3.3V電流を試作機で測り、PPTCとLDOの熱余裕を確認する。
3. 中央5V主入力とTeensy枝の保護部品を、実測電流と突入条件から選定する。

## 2026-07-19 (3基板回路設計の未確定事項・作業順整理)

### やったこと

- 中央Teensy基板、差動ステアユニット基板、オドメトリ基板の未確定事項をP0/P1/P2で分類した`docs/electrical/SCHEMATIC_DESIGN_OPEN_ITEMS.md`を追加。
- 旧XH/電源CAN一体4線と現行GH/電源CAN分離、SWDコネクタ、CAN FD方針など、回路図着手前に解消すべき文書不整合を抽出。
- 共通ブロック→ユニット固有→オドメトリ固有→中央固有の回路図作成順を整理。
- AIは公式資料調査、回路ブロック、ERC、配置配線制約表を担当し、人がKiCad GUIで最終配置配線して段階レビューする役割分担を確定。
- G474各基板のデバッグ方式をWeActStudio MiniDebugger直結へ変更。V1.0回路図からJ2が1.0mm 10極SH系、配列が1=5V、2=GND、3=UART_RX、4=UART_TX、5=NRST、6=SWO、7=GND、8=SWCLK、9=SWDIO、10=デバッガ出力3.3Vと確認。ターゲットケーブルは5〜9番だけ実装し、電源逆流を防ぐ方針を確定。
- JST公式資料からSH 10極の正式部品を`SHR-10V-S-B`、`SSH-003T-P0.2-H`と確認。基板側はサービスしやすい横挿し`SM10B-SRSS-TB`を第一候補、上挿し`BM10B-SRSS-TB`を代替とした。
- ロボット側コネクタ系列統一を優先し、G474各基板のデバッグ端子をGH 6pinへ変更。配列を`GND/SWCLK/SWDIO/NRST/DBG_TX/DBG_RX`とし、WeAct側SH 10pinからの専用変換ケーブルを作る。SWOは基板テストパッドへ残し、デバッガ電源出力は接続しない。
- G474デバッグ用GH 6pinの基板ヘッダは、抜き差しと目視性を優先して上挿し`BM06B-GHS-TBT`に確定。コネクタの1番を向ける方向は基板配置時に決める。
- GHヘッダのラッチ側は基板内側へ向ける方針に確定。CANは各区間30cm未満、総延長1m未満を設計条件とし、電源GNDが共通でも非絶縁CANの基準電位を安定させるためGH 3pinのGND線を残す。
- CAN終端120Ωの切替は小型スライドスイッチ方式に確定。正式スイッチ型番は部品選定で決め、シルクに`TERM ON/OFF`を表示する。
- コネクタ嵌合方向は用途別に分離。各モジュールの常設5V電源GH 2pinとCAN GH 3pinは基板端の横挿し、作業時に使用するデバッグGH 6pinは上挿しとする。
- Rev.Aは中央CAN 3系統と各G474-C620専用CANをすべてClassic CAN 1Mbpsで統一し、CAN FDは対象外とした。G474のFDCANはClassicモードで使用し、トランシーバは1Mbps SOIC-8の`TCAN332DR`を正候補とする。
- 部品選定は入手性、少量価格、複数の公開プロジェクト/評価基板での採用実績、信頼性、ステンシルリフロー性、修理性を比較表で評価する方針に確定。Rev.Aは0603以上とリード付きICを優先し、BGA/WLCSP/0201以下は原則避ける。
- CAN共通ブロックの正式部品選定を実施し、`docs/electrical/CAN_COMMON_BLOCK_PART_SELECTION.md`を追加。トランシーバは旧`TCAN332DR`から、5V VCC/3.3V VIO、AEC-Q100、バスフォルト±58V、SOIC-8の`TCAN1051VDRQ1`へ変更し、公開設計で採用実績の多い`TJA1051T/3`を代替候補とした。
- CAN保護を旧PESD1CAN系からActive品`ESD2CAN24DBZRQ1`へ変更。終端は`RC0603FR-07120RL` 120Ωとリフロー対応スライドスイッチ`JS102011SAQN`、CANコネクタは横挿し`SM03B-GHS-TB`+`GHR-03V-S`+`SSHL-002T-P0.2`に正式化した。

### 現在の状態

- KiCad 10の空ディレクトリ構成は用意済みだが、回路図ファイルは未作成。
- 最初にDOC-01〜04の文書不整合、正式コネクタ、G474/Teensyピンマップ、Rev.A範囲を確定する段階。

### 次の作業

1. GH 2pin/3pinの正式型番と、WeAct MiniDebugger 10極ポートのコネクタシリーズ・ピッチ・基板側正式型番を現物確認する。
2. 旧4線一体/XH記述を正本から除去し、共通CANブロック仕様を更新する。
3. Teensy 4.1全ピンマップと初版CAN FD採否を確定する。
4. 水晶、LDO、入力保護、CANトランシーバ、TVSの公式資料調査へ進む。

## 2026-07-19 (E-stop 2個・コンタクタ励磁・状態表示LED要件整理)

### やったこと

- 非常停止ボタンを2個とし、NC安全接点をコンタクタコイルループへ直列接続する方針を確定。
- 各E-stopの24V内蔵LEDをTeensy非依存の`24V_CTRL`ハードワイヤ回路で点灯する要件を追加。
- Teensy中央基板へコンタクタコイル用MOSFETドライバを組み込み、E-stopハード遮断を主、Teensyを励磁許可とする構成を整理。
- Teensyからもコンタクタを解放できる遠隔停止、停止ラッチ、明示的再アーム、主接点開放診断の要件を追加。
- ミッション達成、状態、バッテリー残量用のテープLED/表示LEDを、安全表示灯とは独立して追加する要件を整理。
- mini PCをGMKtec NucBox G2に確定し、常時通電12V系から給電する方針を追加。流通仕様12V/3Aに対して既存候補`SD-50B-12`(12V/4.2A)を採用候補として維持。
- 所有リレーをKILIGEN `E228`(24V DC、100A表記)と特定。販売情報では連続50〜60A目安かつ24V DC負荷遮断定格の正式資料がないため、メインコンタクタには採用しない方針とした。

### 現在の状態

- E-stop個数、安全接点の接続、コンタクタ励磁回路の配置、演出LEDと安全表示の分離は確定。
- E-stop内蔵LEDの点灯条件、代替メインコンタクタの正式型番/コイル/接点仕様、テープLED方式と電源容量は未確定。

### 次の作業

1. 24V DC負荷遮断定格がメーカー資料に明記された代替メインコンタクタを選定する。
2. E-stop LEDを常時点灯、押下時点灯、モータ電源遮断時点灯のどれにするか確定する。
3. E-stopボタンが安全用NCとは別にNO補助接点を持つか確認する。
4. テープLEDの電圧、方式、長さ、LED密度から最大電流を計算し、専用DC-DC要否を決める。
5. コンタクタ仕様に合わせてMOSFET、クランプ、コネクタ、配線太さを確定する。
6. NucBox G2現物のACアダプタ銘板と給電専用USB-C仕様を確認し、高負荷時消費電流を実測する。

## 2026-07-17 (KiCad向け3基板構成・中央配線方針整理)

### やったこと

- PCBをユニット基板、オドメトリ/IMU状態推定基板、Teensy 4.1中央汎用基板の3種類に分け、G474最小構成・CAN・電源・STDC14等をKiCad共通ブロックとして流用する方針を整理。
- 従来の電源+CAN一体4線案を見直し、5V/GNDは中央基板からスター分配、CANはCOMM_A/B/GNDをデイジーチェーン接続する方針へ変更。
- Teensy CAN1=駆動ユニットx3、CAN3=オドメトリ/IMU等センサー、CAN2=汎用拡張/予備としてバスを分離。
- オドメトリ基板をAMT102 x3(Zなし、GH 4pinのVCC/GND/A/B)にSPI IMUを加えた状態推定ノードへ発展させる方針を追加。
- 購入済み24V→5V/5A DC-DCを中央基板へ入力し、各ノードへ個別保護付きで分配する構成を整理。
- バッテリー電圧・電流監視を中央TeensyのI2Cへ接続する方針を追加。
- 基板シルクのQRコードから基板Rev別ドキュメントを開く案を設計要望として整理。

### 現在の状態

- 3基板の役割、MCU、通信バス、電源の大枠が決まり、KiCad回路図へ入る前の主要な構成判断は概ね収束。
- G474は`STM32G474RET6`を10個確保済み。信号・小電流コネクタはJST GH、デバッグはSTDC14を採用する。
- QRコードのリンク先、サイズ、生成方法はPCBレイアウト時に決める。

### 次の作業

1. バッテリー電圧・電流監視IC、シャント定格、I2C絶縁要否を確定する。
2. SPI IMUの候補をデータシート、在庫、価格、リフロー性で比較して型番を確定する。
3. AMT102 A/B 6chのレベル変換/シュミット入力回路を確定する。
4. 所有済みリレーの型番・入力/コイル・接点仕様を確認して中央安全I/Oを確定する。
5. GH各コネクタの正確な型番、許容電流、ケーブル線径と5V電圧降下を確定する。
6. G474共通ブロックと中央基板の電源/CAN分配回路からKiCad設計を開始する。

## 2026-07-17 (G474実装MCUの型番・必要数確定)

### やったこと

- ユニット基板x3とオドメトリ基板x1の実装MCUを`STM32G474RET6`(LQFP64、Flash 512KB)で確定。
- `STM32G474RET6`を10個購入し、実装必要数4個に加えて試作・交換用予備を確保。
- H753への変更検討を終了し、NUCLEO-G474REと同じパッケージ・ピン割当・現行ファーム資産を維持する方針を確定。

### 現在の状態

- G474の型番・Flash容量・調達不足はKiCad設計開始時の未確定事項ではなくなった。
- ユニット基板とオドメトリ基板でG474最小構成、電源、STDC14、中央CANを共通化できる。

### 次の作業

1. JST GHコネクタとSTDC14デバッグヘッダを共通要件へ反映する。
2. G474共通回路ブロックとユニット基板のKiCad回路図作成を開始する。
3. AMT102 A/B 6ch入力回路と既存リレーに合わせた中央基板I/Oを確定する。

## 2026-07-09 (負荷適応制御ロードマップ保存)

### やったこと

- 接地・負荷増加後の制御発展順序を、現行mode PIを土台にした `FF強化 → 摩擦補償 → mode-space DOB → 状態推定 → 必要時MPC` として確定。
- `docs/control/LOAD_ADAPTIVE_CONTROL_ROADMAP.md` を追加し、負荷下での崩れ方、段階導入、`unit_controller_update()` へのFF/DOB挿入点、ログ先行の実装順序を整理。
- `docs/ARCHITECTURE_DECISIONS.md` と `docs/PROJECT_DOCUMENT_INDEX.md` に参照を追加。

### 現在の状態

- 将来の本命構成は `P_theta + PI_d + PI_s + FF + DOB_d + DOB_s`。
- G474は1kHz局所ロバスト制御、Teensy/mini PCは3輪協調・制約処理・必要時の最適化という責務分担で進める。

### 次の作業

1. 接地評価前に `unit_control_output_t` へFF/DOB/外乱推定ログ項目を追加するか検討する。
2. `targetWheelAccelRpmMilliPerS` をdrive accel FFへ接続する実装案を作る。
3. 接地・負荷ありで、摩擦・飽和・drive/steer干渉を分けてログ評価する。

---


## 2026-07-08 (オドメトリセンサをAMT102へ戻し)

### やったこと

- オドメトリセンサ方針をI2Cホール磁気エンコーダ(MT6701/AS5600)からAMT102 x3へ戻した。
- Z相は使わず、各センサ4線(VCC/GND/A/B)のみでTIM2/TIM3/TIM4 Encoder Modeに入力する方針へ更新。
- `docs/electrical/ODOMETRY_BOARD_REQUIREMENTS.md`、`docs/ARCHITECTURE_DECISIONS.md`、AGENTS/INDEX/README/ベンチ計画の記述を更新。

### 現在の状態

- オドメトリ基板はG474 + AMT102 A/B相 x3が正本。
- 磁気エンコーダ案は、シャフトへの磁石・センサ位置合わせの機械接続が難しいため廃止扱い。

### 次の作業

1. AMT102の最新データシートで電源範囲、出力形式、ピン/線色、DIP分解能設定を最終確認して部品表・コネクタ表へ反映する。
2. A/B 6ch分の5V→3.3V入力方式(レベル変換/保護/シュミット化)を決める。
3. NUCLEOでTIM2/TIM3/TIM4 Encoder Modeの最小ファームを作り、1輪手回しでカウント方向と1回転countを確認する。

## 2026-07-08 (Linux mini PC評価環境確立、低速stick-slip対策完了)

### やったこと

- Linux mini PC側の評価環境を確立: can-utils/python3-serial、slcandでcan0(CANableは
  `/dev/ttyACM1`、`/dev/ttyACM0`はST-Link V3 VCP)、`st-flash`でのflashも初成功。
- `tools/linux/unit_bench.py`(socketcan直、run/set-param/disable/profile)を追加。
- ファームへCAN `SET_CONFIG`(0x140+unitId、17パラメータ、安全クランプ付き)を実装し、
  reflash不要のランタイム調整を可能にした。
- 動摩擦電流を実測同定(~200 raw、速度非依存・正逆対称)。低速stick-slipの原因を
  「ブレークアウェイ~850 vs 維持~200の差」と定量確定し、積分フロア(200)+driveKp10+
  動作開始時積分クランプ(400)で40rpm p-p 213→16、25rpm固着46%→0%を達成。
  確定値は`main.c`既定値へ焼き込み済み。コミット`781b516`。

### 現在の状態

- 無負荷単体ユニット(NUCLEO)で、mini PCからCAN経由で25〜1360rpm+ステアの
  安定制御が成立。残るばらつきは機構の角度依存の引っかかり由来。

### 次の作業

1. 連続軌道評価(`unit_bench.py profile`、速度ゼロクロス反転を含む)。
2. 接地・負荷での摩擦再同定とフロア/クランプ見直し。
3. 中央Teensy 4.1のbring-up。

## 2026-07-07 (mini PC Linux評価引き継ぎ)

### やったこと

- Linux mini PC上の別Codexセッションへ渡すため、`docs/testing/MINIPC_LINUX_HANDOFF.md`を追加。
- CANable/socketcan前提の初期セットアップ、CAN ID/payload、smoke手順、Linux側Codexへの依頼文を整理。

### 現在の状態

- `main`と`origin/main`は同一コミットだが、ローカルには未コミット変更が残っている。
- このCodexセッションでは`.git/index.lock`を作れず、commit/pushは不可。

### 次の作業

1. ローカル端末側で未コミット変更をcommit/pushする。
2. Linux mini PC側で`docs/testing/MINIPC_LINUX_HANDOFF.md`をCodexに読ませ、周期送信+CSV再生スクリプトを作る。
3. 実機評価前に`UNIT_CTRL disable`を即送れる端末を用意する。

## 2026-07-07 (未コミット成果のリモート同期)

### やったこと

- CANable bring-up以降の未コミット成果を確認し、ファーム・ドキュメント・チューニングログ・補助スクリプトをGit管理へ同期する準備を実施。
- `firmware/scripts/build.ps1`でDebugビルド成功を確認。
- Codex実行権限では`.git/index.lock`を作れず、さらにGitHubへの443接続もブロックされたため、コミット・pushは未完了。

### 現在の状態

- `main`には未コミット変更が残っている。ローカル端末側で`git add -A`、commit、pushが必要。

### 次の作業

1. ローカル端末側で未コミット変更をコミットし、`origin/main`へpushする。
2. push後、必要なら実機consoleを終了してtimeout修正版をflashする。
3. console再確認でVCPログの`STOP:`行を確認する。

---


## 2026-07-07 (CANable中央CAN指令bring-up)

### やったこと

- NUCLEO-G474REの中央CAN(FDCAN1 PA11/PA12)をCANable(COM16)から制御する経路を実機確認。
- ファームを、起動時disabled、`SET_TARGET(0x101)` + `UNIT_CTRL(0x121)` enableでのみ駆動する構成へ変更。
- CANable送信用スクリプトを追加し、hardware-session経由でflash→短時間smoke→disableを実行できるようにした。
- `θs=179.912°`, `ωw=500rpm`を20Hz送信し、enable後に実駆動、disableで停止することを確認。
- 続けて、CANableから手入力で`θs`/`ωw`を調整するconsole sessionスクリプトを追加。

### 現在の状態

- 最新CAN制御ファームがflash/verify/reset済み。
- 実機は起動時disabledで、最後にCANableから`UNIT_CTRL disable`をBody/SafeIdle両方で送信済み。
- 無負荷ではPC(CANable)から`θs`/`ωw`司令で動作できる段階に到達。
- 手入力確認は `firmware/scripts/run-canable-target-console-session.ps1` から実行可能。
- 手入力consoleで周期的に落ちるような挙動を確認。timeout 200msが主候補のため、
  ワークツリー上では1000ms化+timeout停止ラッチを実装・ビルド済みだが、console sessionが
  mutexを保持していたため未flash。console側は±1200rpm上限を追加済み。

### 次の作業

1. 手元consoleで`q`を押してmutexを解放し、timeout修正版をflash。
2. console sessionで手入力操作を再確認し、VCPログの`STOP:`行で落ち原因を確定する。
3. PC側送信ツールを任意軌道/CSV再生へ拡張し、指令生成とログ保存を分離する。
4. その後、中央Teensy相当の周期送信・timeout・disable手順へ移植する。

---


## 2026-07-06 (7)

### やったこと

- 未コミットだった設計資料、ファームウェア、CAD、開発設定を整理してGit管理へ追加。
- `hardware/reference/ARK_CANNODE` と `hardware/reference/candleLightFD` を、壊れた埋め込み
  リポジトリ参照ではなく正式なGit submoduleとして登録。
- firmware Debugビルド成功を確認し、`main`を`origin/main`へ同期。

### 現在の状態

- 2026-07-06までのプロジェクト成果がリモートリポジトリへ反映済み。

### 次の作業

1. 駆動モードの発散ガード見直しと再チューニング。
2. CAN-G474の実機bring-upと、CAN 2系統の同時1Mbps試験。

---


## 2026-07-06 (6)

### やったこと

- ユーザーがステア軸の手回し点検(引っかかり・ガタ・異音・AMT連れ回りズレ)実施、異常なしを確認。
  Ki=200発振→-114°逆走以降中断していた通電試験を再開。
- gain-tuningスキルでゲイン調整3イテレーション実施(詳細は`firmware/PROGRESS.md`):
  積分クランプ(mode_integral_limit=1200)込みの再現確認に成功 → steer_mode_ki=125で
  収束~3.0秒・終端誤差0.02°まで改善 → 150は125より悪化のため125を確定値に採用。
- gain-tuningスキルのシリアル監視時間を45秒→15秒へ短縮(ユーザー要望、収束が~3秒のため十分)。

### 現在の状態

- ファームは`steer_mode_ki=125`・`CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で書き込み・
  verify・reset済み。操舵(steer)のゲインは実用水準に到達。

### 次の作業

1. angle_kp/steer_accelの追加チューニング、または駆動モード(wheel≠0)の実走テストへ。
2. `drive_mode_ki`は操舵専用試験では未検証のため、駆動実走時に個別調整すること。

---


## 2026-07-06 (5)

### やったこと

- **車体協調制御をゴールとして明文化し、現状とのギャップを仕様レベルで解消**:
  `docs/control/CENTRAL_COORDINATED_CONTROL.md` を新規作成(レイヤー責務=mini PC計画/
  Teensy 100Hzプロファイラ+車体IK+デサチュレーション/ユニット1kHz FF付き追従、
  車体IKとステア角速度FFの式、特異点処理、反転ポリシー、段階導入0〜4)。
- ギャップ4点を確定・文書化:
  1. SET_TARGETにFFがない → `SET_TARGET_FF`(0x110+id、ステア角速度+ホイール加速度、
     FF欠落時=0で後方互換)をCAN仕様へ追加
  2. 飽和処理がユニット単位 → 中央デサチュレーション(3輪最悪値でツイストスケール)を正、
     DYNAMIC_CONTROL_PLANのユニット内配分は保護動作へ位置づけ変更
  3. 反転判断者が未定義 → 中央のみが判断、ユニットへは連続unwrap角(int32 mdeg)と規約化
  4. ユニット内ランプ(steer_accel等)→ 協調制御後は安全ガードへ格下げ(通常は当たらない値に)
- ARCHITECTURE_DECISIONSへ2行追記(協調制御の責務分担、SET_TARGET_FF)。INDEXに5.7追加。

### 現在の状態

- 協調制御の中央⇔ユニット契約が仕様として確定。ファーム実装は未着手(段階0=現行ベンチは
  この変更の影響なし)。ベンチ状況は(3)(4)のエントリから変化なし(手回し点検待ち)。

### 次の作業

1. (変わらず)手回し点検 → 再現確認 → ゲイン詰め → 駆動実走。
2. ベンチのついでに**モード非干渉の実証**(純操舵 n1=n2 でホイールが転がらないこと)を検証項目に追加。
   残留カップリングがあればユニットIKへ補正項が必要(CENTRAL_COORDINATED_CONTROL.md 検証項目1)。
3. モジュール取付位置 r_i・車輪半径 R の正本値をCADから転記(未文書化)。

---


## 2026-07-06 (4)

### やったこと

- **オドメトリセンサを確定変更**: AMT102 x3(約¥9,000)→ I2Cホール磁気エンコーダ x3
  (MT6701第一候補、AS5600代替、約¥1,000〜1,500)。I2Cバス3本分離
  (I2C1=PA15/PB7、I2C2=PA9/PA8、I2C3=PC8/PC9、AF成立確認済み)、プルアップ2.2kΩ、
  バスリカバリ必須、磁石マウントはCAD側。オドメトリ基板ではIDをPB13-15へ移動
  (PC8衝突のため)。`ODOMETRY_BOARD_REQUIREMENTS.md`を全面改訂し、AMT102案は
  差し戻し先として文末に記録。ARCHITECTURE_DECISIONS / AGENTS.md / INDEX / hardware
  READMEも更新。
- **基板の自作vs購入の再検討**: Matek CAN-G474(約¥3,000)×3+オドメトリで約¥11,000と、
  自作(¥18,000〜25,000+設計工数)より安い。CAN-G474ベンチ試験(既定路線)を
  本番採用可否の判定に兼ねる方針。判定材料: CAN2トランシーバ/終端/TVSの実物確認、
  AMT22のSPIパッド直はんだの信頼性(最大の懸念)、オドメトリのホスト選定。
  ユニットIDはMCU Flash保存で代替可(ゼロ点保存と同じ領域)。**決定はベンチ後**。

### 現在の状態

- ユニット基板方式(自作で確定)の決定は、CAN-G474ベンチ結果次第で購入方式へ
  変更の可能性あり。回路図の下準備((2)のエントリ)は自作続行時にそのまま使う。

### 次の作業

1. CAN-G474到着後のベンチで本番採用可否も判定(上記判定材料)。
2. MT6701/AS5600モジュールと磁石の調達、測定輪への磁石ホルダー設計。

---


## 2026-07-06 (3)

### やったこと

- 制御ループをRoboMaster系オープン実装と比較し3点導入(積分独立クランプ
  `mode_integral_limit`=1200、合成電流飽和時のモード比例スケーリング+積分凍結、
  駆動目標ランプ`wheel_accel_rpm_per_s`)。ビルド確認済み・実機未検証。
  詳細: `firmware/PROGRESS.md`、`firmware/docs/CONTROL_LOOP_TUNING.md`。
- 接地移行の議論: 角度ループは流用可、電流系3点(limit/integral_limit/min_rpm)は
  接地実測から引き直し、という整理を確定。
- **将来計画を新規文書化**: `docs/control/CALIBRATION_AND_ADAPTATION_PLAN.md`。
  CALフェーズにブレークアウェイ・時定数の自己同定を追加して電流系パラメータを自動導出
  (重量・床変更へCAL再実行で追従)、走行中変動には将来LESO/LADRC、HARD_MAXは
  自動化しない、駆動同定はCALに含めない、の設計ルール込み。
- gain-tuningスキルのパラメータ表に新パラメータ2つを追記(950未満禁止の注意含む)。

### 現在の状態

- ファームは新制御パラメータ込みでビルド可、`CLOSED_LOOP_TEST_ENABLED=0`の安全待機。
  通電試験は引き続き機構手回し点検待ち。

### 次の作業

1. 手回し点検 → イテレーション3再現確認(積分クランプ込み)→ Ki/angle_kp詰め → 駆動実走。
2. 接地移行時は`CALIBRATION_AND_ADAPTATION_PLAN.md`の段階1(手動再特性化)から。

---


## 2026-07-06 (2)

### やったこと

- ARK CANnodeの公式リポジトリを `hardware/reference/ARK_CANNODE/` へ取得(Rev 1回路図PDF+BOM)。
  回路図を精読し、流用候補ブロック(LM66100逆接保護、CANコネクタ2個並列のデイジーチェーン渡り、
  外部信号ESDダイオード)を `CARRIER_BOARD_REQUIREMENTS.md` の新設「回路図作成メモ」に整理。
- **推奨ピン割当表の全ピンAF成立を机上確認**(ST公式STM32_open_pin_dataのG474Rx XMLと照合)。
  FDCAN1=PA11/12、FDCAN2=PB12/13、SPI3=PC10-12、LPUART1=PA2/3、I2C1=PA15/PB7、SWO=PB3、
  BOOT0=PB8、NRST=PG10(pin7)。要件書の「CubeMXで確認してから」注記を確認済みに更新。
- 主要部品のピン配置をデータシート/KiCad公式シンボルで確認し要件書へ記録:
  TCAN332(SOIC-8)、MCP1826S(SOT-223)、LM66100DCK(SC70-6)、PESD1CAN(SOT-23、標準ライブラリに
  無いので自作シンボルが必要)、OKI-78SR-5。KiCad 10標準ライブラリのシンボル名も表に記載。
- AMT22データシートrev1.10でコネクタピン順を確認(1=+5V/2=SCLK/3=MOSI/4=GND/5=MISO/6=CS)、
  要件書に追記。AMT22/PESD1CANのPDFを `hardware/reference/datasheets/` に保存。
- 回路図のKiCadファイル自動生成も試みたが、**回路図はKiCad GUIで手描きする方針に変更**(ユーザー判断)。
  書きかけの生成スクリプトは削除済み。

### 現在の状態

- 回路図作成(フェーズ2)の前提が全て揃った: ピン割当確定レベルの机上検証済み、参考回路
  (candleLightFD KiCadソース+ARK CANnode PDF+CANable PDF)取得済み、主要部品のシンボル所在と
  ピン配置確認済み。KiCad 10がインストール済み。
- `hardware/blocks/` `unit-board/` 等は骨組みのみ(.gitkeep)。MB1367回路図PDFのみ手動DL待ち。

### 次の作業

1. KiCad GUIで `blocks/`(can_interface / power_input_5v / mcu_min_g474 / status_led)と
   `unit-board/` の回路図を作成する(要件書「回路図作成メモ」と `CARRIER_BOARD_BUILD_PLAN.md`
   フェーズ2のブロック一覧に従う)。PESD1CANの自作シンボルを `hardware/lib/` に作る。
2. CAN-G474到着後のベンチ確認(前エントリの1〜3)は並行して進む。

---


## 2026-07-06

### やったこと

- `docs/S815e87aa382049149032f707af3370877.pdf` を確認。RC FPV Drone Storeが添付した
  汎用製品マニュアルであり、基板の回路・ピン配置・電源・CAN仕様は含まれていないと判明。
- 参考候補のARK CANnodeについて、公式資料と公開ハードウェアリポジトリの所在を確認。
- Matek CAN-L431をベンチ用CANノードとして使う方針を確定。基板製作ではCAN-L431、
  CAN-G474、ARK CANnode、CANable 2.0を参考にすることを設計文書へ反映。
- 購入済みMatek CAN-G474を主試験機へ変更。CAN-L431は対向ノード、NUCLEO-G474REは
  書込み復旧・回帰確認用の予備とする方針を確定。
- CAN-G474のArduPilot hwdef/AP_Periphをファーム設計参考に使い、制御ループは底面SWDから
  ST-LINKで書き込む方針を文書化。GPL実装はライセンス決定前に直接コピーしない。

### 現在の状態

- 対象商品の技術資料は未入手。現PDFのみでは基板設計への直接的な反映はできない。
- ARK CANnodeはSTM32・5V給電・CAN・SWD等の実装参考になるが、G474・2系統FDCAN・
  モーター周辺ノイズ環境との差分評価が必要。
- CAN-G474実機でG474上の2バス同時動作を検証できる。ただし現行NUCLEO用ファームとは
  CAN2・AMT22 SPIのピンが異なるため、ボード別platform設定の追加が必要。
- CAN-L431はCAN物理層・配線・終端・1Mbps通信の対向ノードに使う。

### 次の作業

1. CAN-G474到着後、5V給電、SWD/UART1 DFU、Device ID、LED/GPIO実行を確認する。
2. CAN-G474用ボード定義を追加し、CAN 2系統の同時1Mbps試験を行う。CAN-L431を対向ノードに使う。
3. CAN-G474のhwdefとARK CANnode/CANable公開回路を、現行の`CARRIER_BOARD_REQUIREMENTS.md`とブロック単位で比較する。

---


## 2026-07-05

### やったこと

- ベンチテストを大きく前進: C620フィードバック受信(段階2)→低電流動作確認(段階3)→
  AMT222+C620x2の閉ループ制御まで到達。
- 制御方式を確定: モード座標PI(操舵=モーター和/駆動=差)。摩擦フィードフォワードは
  実測ばらつき(ブレークアウェイ150〜950mA、角度・方向依存)を理由に**廃止**し、
  PI積分のみで摩擦を吸収する構成に。電流上限2000mA(実測最悪値の約2倍マージン)。
- スティックスリップ対策として最低ステア速度フロア(steer_min_rpm=2rpm)を導入。
- ゲイン調整4イテレーション実施。ベスト構成で**+10°ステップを約3.5秒、
  終端誤差0.37°、オーバーシュートなし**を実機達成。Ki=200は激発振でNG確定。
- ゲイン調整の反復作業を下位モデルへ委譲できるようパイプライン化:
  `.claude/skills/gain-tuning/SKILL.md`(手順・判定基準・安全ルール)と
  `.claude/agents/gain-tuner.md`(sonnet固定エージェント)。
- 詳細ログ: `firmware/PROGRESS.md` と `firmware/docs/CONTROL_LOOP_TUNING.md`。

### 現在の状態

- ファームは安全待機(`CLOSED_LOOP_TEST_ENABLED=0`、電流常時0)で書き込み済み。
- **要注意**: Ki=200発振の直後の試験でステア軸が目標から-114°逆走して発散停止した。
  機構(ベルト/ギア/カップリング)に何か起きた可能性があり、通電試験は中断中。
- 操舵制御は「まともに動く」水準に到達。駆動(ホイール回転)側の実走は未実施。

### 次の作業

1. **ステア軸の手回し点検**(引っかかり・ガタ・異音・AMT連れ回りズレの確認)← 最優先
2. 点検OKならベスト構成の再現確認 → `/gain-tuning`(またはgain-tunerエージェント)で
   Ki 100〜150 / angle_kp の詰め。
3. 駆動モードの実走テスト(wheel≠0)、目標角の連続追従評価。

---


## 2026-07-02

### やったこと

- 電装計画の全docsをレビューし、パーツ選定を具体化(AMT22直結化、TCAN332、MCP1826S、SD-25B-5/SD-50B-12、XT90-S、MIDIヒューズ、EVリレー等)。
- AMT22データシートを確認し、MISO分圧不要(全信号3.3V直結可)と判明。要件書を修正。
- 主要アーキテクチャを確定: G474自作基板 / 2バスCAN / Teensy 4.1 / AMT222A-V(5mmボア) / 4線5V給電 / XH+XT / ゼロ点MCU Flash保存。
- 中央CANのID設計案を作成(`docs/communication/COMMUNICATION_NAMING_AND_IDS.md`)。
- STM32G474RET6の推奨ピン割当表を作成(`docs/electrical/CARRIER_BOARD_REQUIREMENTS.md`)。
- 中央ボード要件書を新規作成(`docs/electrical/CENTRAL_BOARD_REQUIREMENTS.md`)。
- KiCad共通ブロック方針を策定(`docs/electrical/CARRIER_BOARD_BUILD_PLAN.md`冒頭)。
- STM32書き込み環境を整備: Arm GCC 14.2導入、toolchain.ps1追加、launch.json修正、日本語パス起因のobjcopy失敗を修正。
- NUCLEO-G474REへFlash書き込み成功、B1→LD2動作を実機確認済み。
- AGENTS.md / CLAUDE.md / PROGRESS.md(本ファイル)を整備。
- オドメトリを確定: 3輪AMT102+専用G474基板(unitId=4)、x/y/θを中央CANへ配信。要件書とCAN payload定義を作成。
- ベンチテスト計画を作成(`docs/testing/NUCLEO_BENCH_TEST_PLAN.md`)。MCP2551の3.3V接続可否をデータシートで確認済み(TXD直結可、RXDはFTピン受け)。
- `hardware/` を整備: lib/blocks/基板3種/referenceの構成。candleLightFD(KiCadソース、CERN-OHL)とMKS CANable V2.0回路図を収集。ST MB1367回路図のみ手動DL待ち(README記載)。

### 現在の状態

- docs体系はG474自作基板+2バスCAN前提で一貫。電装3枚(ユニット/中央/分電盤)の要件が揃った。
- ファームはB1→LD2の最小構成がFlashで動作中。ビルド・書き込みはスクリプトで再現可能。
- KiCad未着手。ピン割当はCubeMX未確認(表はドラフト)。

### 次の作業

1. **ベンチテスト**: `docs/testing/NUCLEO_BENCH_TEST_PLAN.md` に従い、NUCLEO+MCP2551+AMT222A-V+差動モジュール実機で段階テスト1〜7を進める。ファーム実装(FDCAN/C620/AMT22ドライバ、制御ループ)もこの中で行う。
2. CubeMXでピン割当のAF成立確認 → 要件書の表を確定版に更新。
3. `hardware/` ディレクトリ骨組み+KiCad共通ブロック(can_interface等)の作成。
4. 中央ボード用にコンタクタ・E-stopスイッチの型番確定(コイル仕様がドライバ回路に効く)。
5. オドメトリ(AMT102)の受け側MCUを決める(Teensyならレベルシフタ、G474なら直結)。

## 2026-07-07 ゲイン調整セッション保存

- C620の `feedback.rpm` はM3508内蔵19:1減速前のロータRPMで、制御側の差動ステア運動学は減速後出力軸RPMとして扱う方針に整理した。
- ファーム側ではC620フィードバックを `M3508_INTERNAL_REDUCTION` で除算して `unit_controller_update()` に渡す前提へ修正・文書化した。
- 単点RPM試験用に、サブエージェント契約、コンパクトログ収集、実機mutexラッパを追加した。
- 40 wheel-rpm単点試験:
  - Run1: drive Kp/Ki=5/20、steer Kp/Ki=50/20で10秒完走。
  - 後半平均 33.999 RPM、範囲 -0.032〜243.561 RPM、角度誤差peak 1.670°。
  - 周期的stick-slipのためFAIL判定。
  - Run2はログ未生成で評価不能のため採用せず、追加駆動なし。
- 現在状態:
  - `CLOSED_LOOP_TEST_ENABLED=0`
  - clean build後、safe-idle flash/verify/reset成功済み。
  - 40rpmは失敗境界として扱い、次は50rpm以上の安定域から下限探索または試験ハーネス高速化を優先する。

## 2026-07-07 ゲイン調整セッション保存(2)

- `invoke-hardware-session.ps1`経由でstaircase試験を実施し、各回の終了後にsafe-idleを
  flash/verify/resetした。最終状態は`CLOSED_LOOP_TEST_ENABLED=0`のsafe-idle。
- 標準staircase(40/45/50/60/75/100/150rpm)は全stepが`STEP_OK`で完走。
  `STEP_OK`直前1秒では40rpmも平均40.74rpm、角度誤差max 0.97°まで入った。
- 低速staircase(25/30/35/40rpm)も追加実施。25rpm/35rpmは`STEP_OK`、
  30rpm/40rpmはtimeout。最大角度誤差10.37°。結果が非単調で、低速限界は
  始動角・局所摩擦・駆動→操舵カップリングに強く依存している可能性が高い。
- 暫定判断: 現ゲインの正転・無負荷では40rpm以上は動作可能だが、30〜40rpm帯は
  安定採用には未確定。次は角度外乱対策として操舵保持側ゲインを少し戻すか、
  30/35/40rpmを開始角・正逆方向を変えて複数回試験する。

## 2026-07-07 ゲイン調整セッション保存(3)

- 操舵保持を強化して再試験:
  - `steer_max_rpm=1.0`
  - `angle_kp_rpm_per_deg=0.2`
  - `steer_mode_ki=30`
  - step内角度誤差6°/300msでstep FAIL、`scale=`ログ追加。
- 30/35/40rpm再試験では、40rpmのみ`STEP_OK`。30/35rpmは角度ではなく駆動側stick-slipで
  timeout。操舵外乱は最大3.43°まで低下したため、下限は暫定40rpm。
- 中高速staircase(40/75/150/250/350rpm)は全step`STEP_OK`、電流スケーリング0%、
  角度保持良好。350rpm直前1秒は平均345.75rpm、角度誤差max 0.79°。
- 最終状態: 実機はsafe-idle。`firmware/src/main.c`も`CLOSED_LOOP_TEST_ENABLED=0`。
  次は500/750/1000rpm級へ段階拡張して、理論wheel上限(約1360rpm)へ近づける。

## 2026-07-07 ゲイン調整セッション保存(4)

- ユーザー指摘により、各stepの保持時間を長くした拘束領域試験へ移行。
  `STEP_MIN_DWELL_MS=10000`、`STEP_STABLE_MS=3000`、`STEP_TIMEOUT_MS=25000`。
  上限拘束時に要求rpmとの差で失敗しないよう、判定基準を`wheel_rpm_command`へ変更。
- 500/750/1000/1200/1400rpm要求の長時間staircaseを実施し、全step`STEP_OK`。
  500〜1200rpmは直前1秒でp-p 2.5〜5.1rpm程度、角度誤差max 0.62°以下。
  1400rpm要求では制御器が約1363rpmへ制限し、実測平均1363.49rpm、角度誤差max 0.62°。
- 暫定レンジ: 無負荷・正転では下限40rpm、上限は`motor_max_rpm=469`由来の約1360rpm。
  30/35rpmはstick-slipで不採用。次は逆転側と、接地/拘束での温度・電流余裕確認。

## 2026-07-07 ゲイン調整セッション保存(5)

- 逆転代表点 -40/-500/-1400rpm を長時間保持で確認。
  全step`STEP_OK`、終了後safe-idle書き戻し済み。
- 直前1秒:
  - -40rpm: 平均 -42.39rpm、p-p 9.02rpm、角度誤差max 0.53°
  - -500rpm: 平均 -500.31rpm、p-p 1.90rpm、角度誤差max 0.62°
  - -1400rpm要求: cmd約 -1363rpm、実測平均 -1362.55rpm、p-p 2.26rpm、角度誤差max 0.70°
- 結論: 無負荷では正逆とも`|ωw|=40〜約1360rpm`で安定。次は接地/拘束状態での
  温度・電流余裕・低速stick-slip再評価。

## 2026-07-07 ゲイン調整セッション保存(6)

- 接地試験ができないため、`ωw`固定中に`θs`を動かす同時指令試験へ移行。
- `ωw=500rpm`、起動角から`θs=+10°`を実施。
  初回はstep内角度誤差6°ガードが意図せず働いたため、角度step用に12°へ緩和して再試験。
- 再試験結果: `STEP_OK`。角度誤差は約1.0秒で1°以内、final-halfでは
  wheel平均500.11rpm、p-p 9.91rpm、角度誤差max 0.77°、scale 0%、maxTemp 29°C。
- 判断: 無負荷では`ωw=500rpm`を維持しながら`θs=+10°`へ収束できる。
  次は`θs`往復(+10/-10/0)または`ωw=40/1200rpm`代表点で同じ角度step。

## 2026-07-07 ゲイン調整セッション保存(7)

- 目視切り分けしやすくするため、`ωw=500rpm`のまま`θs=+90°`を試験。
- `steer_min_rpm=2`ではログ上は約0.9秒で到達するが、終端で±2〜3°のリミットサイクルが出て
  安定判定timeout。`steer_min_rpm=0`では`STEP_OK`。
- `steer_min_rpm=0`試験のログではAMT角が約49.9°→138.5°へ約90°変化し、wheel平均500.01rpm、
  p-p 6.85rpm、角度誤差max 0.44°、scale 0%、maxTemp 30°C。
- ただしユーザー目視ではステア変化が見えなかった。ログ上のAMT角と物理ステア出力の対応が
  未確認。次は通電せず、ステア出力を手で動かしてAMT角が同じだけ変わるかを確認する。

## 2026-07-07 ゲイン調整セッション保存(8)

- `ωw=500rpm`を先に定常化し、その後`θs=base/+90/+180/+270/+0°`へ90°刻みでstepする試験を実施。
- step0〜3は全て`STEP_OK`。final-half wheel平均はほぼ500rpm、p-pは約5.8〜8.1rpm、
  角度誤差maxは0.62°以内。
- step4(+0°戻し)も`STEP_OK`だが、ユーザーが最終stepでホイールに触れたため外乱あり。
  p-p 93rpmは速度制御評価から除外する。
- 判断: ログ上は500rpm定常中に90°刻みの`θs`変更へ追従でき、ユーザー目視でも良さそう。
  AMT角ログと物理ステア出力は概ね一致している扱いで次へ進める。最終stepはホイール接触外乱あり。

## 2026-07-07 ゲイン調整セッション保存(9)

- 90°刻み同時指令を低速40rpmと高速1200rpmへ展開。
- 40rpmは全step完走し角度は概ね追従するが、wheel p-pが大きく、機構摩擦を超える瞬間の
  オーバーシュート/stick-slip境界。実用下限は40rpmではなく75rpmから扱う方針。
- 1200rpmは全step`STEP_OK`、scale 0%。定常化後のstep1〜4はwheel p-p約3.6rpm、
  角度誤差max 0.70°以内。maxTempは30→36°C。
- 結論: 無負荷単体ユニットでは、実用域`|ωw|>=75rpm`で`ωw, θs`指令制御は成立。

## 2026-07-07 中央CAN受信ログ準備

- 2個目のCANトランシーバをFDCAN1(PA11/PA12)へ接続する前提で、ファームに中央CAN初期化を追加。
- safe-idleのまま、FDCAN1受信フレームをVCPへ`CENTRAL_RX`表示。
- `0x101` DLC8を`SET_TARGET`としてlittle-endian int32 x2で仮decodeし、
  `SET_TARGET_RX steer=... wheel=...`を表示。まだ制御には接続していない。
- `docs/communication/COMMUNICATION_NAMING_AND_IDS.md`へSET_TARGET little-endian規約を追記。
- Debugビルドとflash/verify/reset完了。次はCANableから`0x101`を送ってG474 VCPで受信確認。

## 2026-07-07 中央CAN受信確認

- CANableはWindows上で`COM16`、G474 VCPは`COM15`として認識。
- CANable(SLCAN)から`S8`(1Mbps)、`O`後に`0x101` DLC8を送信。
  payload `90 5F 01 00 20 A1 07 00`。
- G474 VCPで以下を確認:
  - `CENTRAL_RX id=101 dlc=8 data=90 5f 1 0 20 a1 7 0`
  - `SET_TARGET_RX steer=90000 wheel=500000`
- 中央CAN受信経路は成立。次はenable/timeout付きで`SET_TARGET`を制御目標へ接続。

## 2026-07-20 ユニット基板 参照回路図の図面化(CircuitikZ + schemdraw SVG)

- `UNIT_BOARD_SCHEMATIC_REFERENCE.md` 3章の接続表を正として、6ブロックの参照回路図を作成。
  1. 電源チェーン(J101→LM66100(CE_N=VOUT明示)→PWR_5V→TLV1117LV33→3V3)
  2. CANブロック(TCAN1051V ピン1-8、ESD2CAN24、120Ω+SPDT終端、GH3パススルーx2、TXD/RXD方向矢印)
  3. MCU電源・デカップリング(VDD x4各100nF、VBAT、VDDA/VREF+島、C310バルク)
  4. HSE+NRST+BOOT0 / 5. 5V監視ADC(33k/22k+BAT54S) / 6. AMT22・デバッグ・ID DIP・LED
- 成果物:
  - `docs/electrical/figures/unit-board-circuitikz.tex`(article 1本に6図。ローカルにLaTeX環境が
    無いため未コンパイル。pdflatex互換のためtex内注記は英語)
  - `docs/electrical/figures/unit-board-block1.svg`〜`block6.svg`(schemdraw 0.23でレンダリング済み、
    日本語注記付き、テキストはパス化済みでフォント非依存)
- 未確定注記を図中に明記: C620側コネクタ(6章#1)、DIP型番(#2)、R601-604値(#3)、LM66100/TLV1117
  ピン番号(#4,#5)、水晶pad番号(#6)、DBG_TX/RX方向(#7)。
- 生成スクリプトはscratchpad(セッションtemp)の`gen_figs.py`。再生成が必要ならschemdrawで同様に可能。

## 2026-07-23 ユニット基板 回路図ブロック作成・AI監査セーブポイント

- KiCadの`hardware/unit-board/unit-board.kicad_sch`を親シートとして、電源入力/3.3V生成、
  5V監視、STM32G474最小回路、中央CAN、C620 CAN、AMT22/デバッグ/ID DIP/LEDの各ブロックを作成。
- 階層シートからモジュール基板PCBを作成する段階へ進む方針。ユニット基板を正本として整備し、
  オドメトリ基板など派生基板は用途別プロジェクトへ複製して不要ブロックを差し替える。
- AI監査で、5V監視ADCノードの未接続とAMT22 SPI配線の微小ギャップを修正。
- 2026-07-23の保存時点でKiCad CLIから回路図を読み込み可能。ERCは71件
  （Errors 52 / Warnings 19）で、まだPCB更新へ進める品質ではない。
- 未解決の重要項目:
  - 電源入力GH2のpin 1/2極性を要件（pin 1=PWR_5V、pin 2=GND）と一致させる。
  - 4pad水晶Y1を`Device:Crystal_GND24`相当へ変更し、信号pad 1/3、GND pad 2/4を正しく接続する。
  - 親子シート間で`PWR_5V`、`CAN_TX/RX`、`SPI3_MOSI/MISO`などの階層ラベル名を統一する。
  - PWR_FLAG、未使用ピンのNo Connect、電源ピン駆動元を整理してERCを収束させる。
  - J7を縦型`BM06B-GHS-TBT`へ、COMM/ERR LED色とD7/R14のvalueを部品表どおりに直す。
- 次の作業: 上記の重要項目を回路図へ反映し、ERC/BOM/netlistを再検証してからPCBレイアウトへ進む。

## 2026-07-26 (オドメトリ基板 ERC 0件収束)

- `hardware/odometry-board/Oddom board/`のKiCadプロジェクトを対象に、前セッションからの続きでERCを54件→0件（Errors 0 / Warnings 0）まで収束させた。
- 前セッション分（このセッション開始時点で未コミット）: ルートシート未使用MCUピン25本へNo-Connect追加、電源系PWR_FLAG追加（VIN/VDDA/VSSA系統3箇所）、BOOT0の無効な`hierarchical_label`を`label`へ修正、浮いた配線・GNDシンボル整理。`Oddom board/`にsym-lib-table/fp-lib-tableを追加しDifferentialSwerveライブラリ未認識警告を解消。CAN_interfaceシートはVCCへPWR_FLAG追加で0件化。ルートシートとCAN_interfaceシートはこの時点で0件。
- このセッション: 残り18件（AMT102_inputテンプレート、3輪分×6件）を解消。
  - `AMT102_input.kicad_sch`（3シートAMT102_input/1/2で共有するテンプレート）で、チャンネルA/Bを別々の74LVC2G17（2部品、各ゲートB=unit2のみ使用、電源unit3未配置）で受けていた構成を、承認済み方針どおり1部品3ユニット構成へ統合。
    - unit1（ゲートA、pin1/6）= 旧チャンネルA用チップの位置・配線をそのまま流用（座標が同一のため配線変更不要）。
    - unit2（ゲートB、pin3/4）= 既存のチャンネルB用ブロックをそのまま維持。
    - unit3（電源、pin2=GND/pin5=VCC）を新規配置し、GNDシンボルと`global_label "PWR_3.3V"`（ルートシートの3.3Vレールと同名。`ODOMETRY_BOARD_SCHEMATIC_REFERENCE.md`の電源表でバッファは3V3給電と確定済み）へ接続。
    - 各ユニットブロックの`instances`パスを3シート分（U3/U7/U9）に統一し、旧チャンネルA用の重複リファレンス（U5/U6/U8）を削除。GND新規シンボルの参照は`#PWR044`〜`046`。
  - `kicad-cli sch erc`で0 violations確認済み（`fresh_erc*.rpt`はスクラッチ確認用で削除済み、リポジトリには残していない）。
- 次の作業: PCBレイアウト（`Oddom board.kicad_pcb`）側へ配置配線を進める。まだ`hardware/odometry-board/Oddom board/`一式は未コミット（`git status`で確認要）。
