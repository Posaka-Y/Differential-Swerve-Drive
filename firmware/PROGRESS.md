# Firmware progress

最終更新: 2026-07-31(GUI/RAMへ空走ベスト設定適用)

## 実機状態(2026-07-31 GUI/RAM空走ベスト設定)

ユーザー指示で、3機構に合格した空走共通候補をGUI/RAMへ明示適用した。cap/max=300rpm、
profile=1800/12000/3000deg系、jerk=0、unit guard=4000rpm/s、current limit4500raw、
0/60rpm Kp/Ki=120/50、100/150rpm Kp/Ki=140/50、高速decel FF=2.5、brake Kp倍率2。
unitはdisabled、AMT/C620正常。Flash boot既定60rpmは接地未検証のため変更していない。
高グリップタイヤ化後のtraction controlは未実装・未確定。C620 wheel rpmと独立オドメトリの
各輪位置期待速度を比較し、個輪torqueをramp制限する案を接地ログ取得後に評価する。

## 検証(2026-07-31 機構unit3空走回帰)

機構unit3へ切り替え、controller CAN unitId=1、Flash `zero=1503/seq1`のまま段階回帰した。
60rpm/wheel=0/±90degは2/2実用合格(first-entry 0.350/0.358s、overshoot最大3.60deg、
terminal最大0.175deg、実peak61.9rpm)。120rpm候補のwheel=0/265rpm・正逆90degは4/4
実用合格(first-entry 0.302〜0.323s、overshoot最大4.22deg、terminal最大0.264deg、
実peak93.6rpm)。wheel=265正方向だけstrict settle 1.240sだが実用gateは合格。

300rpm cap、profile=1800/12000/3000deg系、current limit4500rawの90deg fullは4/4実用合格。
first-entry 0.210〜0.237s、overshoot最大15.65deg、terminal最大0.176deg、実peak140.4rpm。
170deg fullも4/4実用合格で、first-entry 0.328〜0.371s、overshoot最大15.01deg、
terminal最大0.332deg、実peak160.6rpm。全試験で安全停止、feedback/AMT脱落、温度上昇なし。

unit1/2/3の300rpm設定を補間後の同一指標で集計した。90deg first-entry平均は
0.221/0.230/0.219s、170degは0.348/0.338/0.348s。overshoot worstは90degで
15.21/14.85/15.65deg、170degで14.83/13.43/15.01degで、空走では個体trim不要、共通tableを
継続する。170deg実peakだけunit3が160.6rpmでunit1/2の172.2/173.4rpmより約7%低いため、
接地後も差が残るか監視する。

主要ログは`auto-tune/2026-07-31T12-22-54Z`、`12-23-13Z`、`12-23-32Z`、`12-23-51Z`。
試験後はunit max60rpm、unit accel600rpm/s、current limit4000raw、Web cap60rpm、
profile=360/3600/2250deg系へ復元し、disabledとした。

### 次の作業

1. 外部24V/current計測後に実300rpm制動、続いて接地条件を評価する。
2. 接地でもunit3の実peak差が残る場合だけ個体trimを検討する。

## 実装・検証(2026-07-31 機構unit2回帰・100Hz帯飛び越し対策)

機構unit2への切替ではAMTとステア軸の相対原点は変化しないため再校正せず、Flashの
`zero=1503/seq1`を維持した。controllerは引き続きCAN unitId=1。60rpm/wheel=0/±90degは
2/2実用合格(first-entry約0.354s、overshoot最大3.34deg、実peak60.8rpm)。120rpm候補の
wheel=0/265rpm・正逆90degは4/4実用合格(first-entry 0.324〜0.384s、overshoot最大2.81deg、
terminal最大0.264deg)。

300rpm cap、profile=1800/12000/3000deg系、current limit4500rawの90deg fullは4/4実用合格。
first-entry 0.202〜0.424s、overshoot最大14.85deg、terminal最大0.352deg、実peak142.4rpm。
170deg反復では実peak最大168.6rpmに対して100Hz sample間の角度変化が±2deg帯幅を超え、
目標通過sampleはあるのに初回帯内sampleがovershoot後となるcaseを8本中4本で確認した。

`first_arrival_metrics()`を、帯内sample検索から方向付き誤差境界の最初のcrossingを隣接sample間で
線形補間する方式へ変更した。正負とも-8→+4deg相当を10msで飛び越すself-checkを追加し、
py_compile/self-checkはPASS。既存8移動の補間worst first-entryは0.371sで8/8実用合格。
修正版の正式ログ`auto-tune/2026-07-31T12-19-52Z`は170deg full 4/4実用合格、first-entry
0.336〜0.340s、overshoot最大13.43deg、terminal最大0.195deg、実peak173.4rpm、27degC。

### 現在の状態

- 機構unit2/controller unitId1はdisabled、wheel=0、27/26degC、AMT/C620正常、
  `zero=1503/seq1`とCRCを維持。
- runtimeは安全側のunit max60rpm、unit accel600rpm/s、current limit4000raw、Web cap60rpm、
  profile=360/3600/2250deg系へ復元。boot既定は変更していない。

### 次の作業

1. 機構unit3へ同じ段階回帰を適用する。
2. 外部24V/current計測器導入後に実300rpm制動を再評価する。
3. 接地評価用gateを車体挙動込みで別途定義する。

## 実装・検証(2026-07-31 P4 jerk/profile・300rpm実速度と急制動対策)

Web UIへ`profile_steer_accel_dps2` stateとjerk制限profileを追加した。停止距離は現在速度だけでなく、
現在加速度が`-decel`へjerk rampする間の距離を解析計算する。方向反転でも固定角座標の加速度を
`J*dt`以内で更新し、目標近傍の速度反転時は最大2deg以内だけ位置を着地、加速度はjerk制限で0へ戻す。
非zero jerkは100k〜500k deg/s3、0は旧profile互換。中央host coreにも同じAPI/試験を追加した。

120rpmの0/100k/200k比較(`auto-tune/2026-07-31T11-26-58Z`)は全候補が実用合格。legacy 0が
first-entry平均0.303sで最速、200kは0.326sへ遅くなる一方worst overshoot 7.12→5.10deg、
settle平均0.744→0.721sだった。応答優先方針によりjerk=0を採用した。150rpm比較
(`11-28-16Z`)も0が0.228sで最速だがworst overshoot 16.875deg、100kは0.311s/14.678degだった。

ユーザー指示により空走実用gateをfirst-entry<=0.50s、overshoot<=20deg、terminal<=1degへ緩和し、
旧4deg/settle0.9sをstrict診断に残した。180/220/260/300rpmを段階評価し、300rpm cap、
profile=1800/12000/9000deg系は初回2移動+確認4移動の6/6実用合格。確認4移動のworstは
first-entry 0.253s、overshoot 19.863deg、terminal 0.528deg、28degC。90deg三角profileのため
実速度peakは93〜145rpmであり、300rpm実速度確認とは分ける。

`unit_steer_mode_id.py`は上限300rpm、指令加速度ramp、fresh STATUS1 CAN seed、ACTIVE ack、
STATUS1実角を外周P=0時の安全targetにする方式へ更新した。260rpm±0.3s
(`steer-mode-id/2026-07-31T11-36-45Z`)はrise90 0.158/0.153s、overshoot 0.79/0%、
tail MAE 3.6/11.3 mode rpmで定常到達した。

C620電源復旧後の300rpm±0.3s (`steer-mode-id/2026-07-31T11-41-53Z`)はrise90が
0.174/0.174s、peakが303/333 axis rpm、速度overshootが1.04/11.06%で、300rpm実速度へ
到達した。ただし試験器が加速と同じ4000rpm/sで300→0へ落としており、急制動時に電源が
保護停止したことをユーザーが確認した。永続faultはなく再投入後`fdbkOk=1`へ復帰したが、
この試行は安全な300rpm完了とは扱わない。

速度mode試験器へ`--steer-decel-rpm-s`(既定500)を追加し、加速と回生制動を分離した。
zero phaseは`amplitude/decel`の制動時間を自動追加してから指定dwellを取り、符号反転は必ず
0rpmを経由、終了時も明示zero ramp完遂後にDisableする。`--step-direction`で正または負の
単方向だけを選び、高速制動イベントを1回へ削減できる。self-check/py_compile/diff checkはPASS。

改修版の正方向300rpm 1 pulse (`steer-mode-id/2026-07-31T11-48-06Z`)はrise90 0.174s、
peak 300.9 axis rpm、overshoot 0.85%。指令は0.595sで300→0、実測は3ms後に5rpm未満、
さらに0.25s zero dwellと最終0.1sを置いてDisableした。ACTIVE脱落なし、終了後`fdbkOk=1`、
AMT正常、永続faultなし。旧急制動の電源保護停止は再発しなかった。

24V telemetry経路も監査した。現STATUS3は未実装値`0xffff`、基板ADCは5V専用、C620 feedbackに
入力電圧fieldはない。計測器導入までは260rpm超・無計測時の制動を500rpm/s以下へ制限し、
`--yes-24v-monitored`明示時だけ高速制動を許可する。STATUS3 `FEEDBACK_OK`脱落を即失敗にした。
CSVへbus/status/feedback snapshot、metadataへ
STATUS3数、feedback drop、電圧available/min/max、STATUS2最大gapを保存する。公式C620資料は
rated 24Vのみで最大連続入力を明示しないため、電源型番/OVPと外部実測なしに合否電圧を置かない。

負方向300rpm単発(`steer-mode-id/2026-07-31T11-57-32Z`)もrise90 0.174s、peak300.9rpm、
overshoot0.87%、feedback drop 0で完走し、正負の500rpm/s停止を確認した。

profile制動も500 axis rpm/s相当の3000deg/s2へ揃え、170degをwheel=0/265で評価した。
4000rawはwheel265負方向だけfirst-entry0.605sで実用gateを外れ、加速中9 sample中7 sampleが
current scale、未飽和5375raw/適用3934rawだった。条件付き電流拡張の根拠を満たしたため4500rawへ
1段だけ上げた。4000/4500rawインターリーブ各4移動は双方合格し、4500はfirst-entry平均
0.356→0.344s、settle0.941→0.888s、実peak167→183rpm、overshoot14.66→16.15deg。
応答優先候補を4500rawとした。4500raw・90deg full 4移動も4/4合格、first-entry平均/最悪
0.225/0.243s、実peak141rpm、overshoot最大15.205deg、terminal最大0.175deg、最高27degC。

G474 `SET_CONFIG idx9`は中央profileと同じ通常rampではなく最終guardとして使うため上限を
2000→4000 axis rpm/sへ拡張。boot既定600は維持した。host test、ARM build、flash/readbackを通し、
bin 16064byte、MD5 `42e5be8774fc61f3d4ea87c5901cb290`。zero=1503/seq1保持。

### 現在の状態

- unit disabled、wheel=0、Web UI port8080起動中。`fdbkOk=1`、AMT正常、角度約315.9deg、
  永続faultなし。GUI cap60rpm、RAM current limit4000rawへ安全復元済み。
- unit 1浮上では300rpm位置profile上限、連続実速度、500rpm/s停止を確認済み。4000rpm/s制動は禁止。

### 次の作業

1. unit 1空走の反復は止め、4500raw/ramp制動候補をunit 2/3または接地で評価する。
2. 計測器導入後に24V peak/電源OVPを記録し、500rpm/s暫定制約を再評価する。
3. 接地では空走20deg gateを再利用せず、車体横振れを含む基準を決める。

## 実装・検証(2026-07-31 P3a明示加速度と150rpm段の切り分け)

現ベンチのClassic CAN制約下で`TRAJECTORY_FD.thetaDDot`相当を先行評価するため、
`SET_TARGET_ACCEL_FF(0x160+unitId)`を追加した。payloadはsteer mdeg/s2 + reserved 0。
Web UIが200Hzでprofile rateの実差分を送信し、G474は200ms以内の明示値を旧
`SET_TARGET_FF`受信周期差分より優先する。明示値は現コミッショニング範囲±2000 axis rpm/sへ
clampし、途絶後は旧±1000rpm/s差分へ戻る。`UNIT_STATUS_DIAG diagFlags bit2`、VCP
`ffExplicit`、auto tuner `steer_accel_explicit_active`へ接続した。

最初の120rpm 2移動は初回±2deg平均0.298sだったが1本がovershoot 9.404degとなったため、
profile decel=1800/2000/2250をインターリーブで各4移動比較した(`11-04-58Z`)。全12移動が
実用gate合格。2000deg/s2は初回平均0.313s、最大overshoot 5.625degで総合最良となり、
120rpm明示加速度packageへ採用した。全125 sample、運動中76 sampleでexplicit flag=1。

高速制動だけPを強めて終端反動を避けるため、brake Kp倍率も0/60/100/150rpm knotで連続補間した。
`SET_CONFIG idx48..51`、idx47は全knot uniformへ戻す。host testは80rpm中間倍率、invalid index、
global互換をPASS。150rpm profile=900/7200/4500、unit accel1200の基準(`11-06-00Z`)は
実peak114.2rpm、初回平均0.263sだがovershoot最大14.414deg。高速倍率2.5→3.0で最大11.865degへ
改善したが不合格。150rpm knot=3/3.5/4の各4移動(`11-09-08Z`)も全候補不合格で、最良3.5は
最大10.723deg、4000raw飽和、実peak100.7rpm。倍率を上げるほど飽和で速度帯域を失うため、
この方向の探索とcurrent limit拡張を停止した。

### 現在の状態

- Flash bin 16060byte、MD5 `448c6ffa65d452268efcd94da6eb68cb`。校正zero=1503/seq1保持。
- RAM/Webはmax/cap120rpm、unit accel1000rpm/s、100/150 Kp/Ki=140/50、FF=0.5/2.5、
  brake倍率全knot2、profile=720/5400/2000へ復元。disabled、wheel=0、約306.0deg、28/26degC。
- boot既定はmax60rpm、brake倍率1、FF0.5/0.5を維持。Web UI port8080起動中。

### 次の作業

1. P4 jerk制限profileへ加速度stateを追加し、jerk中の追加停止距離を制動開始へ反映する。
2. G474内部rpm rampをprofileと同じ加速度にせずhard guard化し、二重rampを除去する。
3. 4000raw固定で実peak150rpm/overshoot<=8degを成立させてから200rpmへ進む。

## 実装・検証(2026-07-31 制動Kp倍率と実用到達基準)

ユーザー方針により空走低rpm微小振動を含む厳格settleを性能順位から外した。auto tunerの
trial scoreはsettle/deadlineでなく、初回±2deg進入、overshoot、終端誤差、追従/wheel誤差を使う。
実用gateは全試行で安全停止なし、first-entry<=0.50s、overshoot<=8deg、terminal<=1deg。
旧4deg/0.9s gateは`strict_settle_failures/pass`としてCSVへ残す。

加速応答を落とさず制動帯域だけ上げる`steer_brake_kp_multiplier`をcontroller configへ追加。
target accelerationとrateが逆符号のphaseだけscheduled Kpへ乗算する。`SET_CONFIG idx47=1..4`、
既定1。host testで加速Kp不変/制動Kp x2とP電流x2を固定し、Debug build/Flash verify済み。
bin 15664byte、MD5 `63b59d173a7bdef4bc152761b0bb75`。

倍率比較では1/1.5/2で最大overshoot 6.416/5.888/5.361deg、平均first-entry
0.331/0.331/0.327s。2/2.5/3追試でも2が最も速く、3は7.91degへ悪化した。
強加速profileをscreenし、最終候補を次に決定した。

| 項目 | 値 |
|---|---:|
| steer max / Web cap | 120rpm |
| 100/150rpm Kp/Ki | 140/50 |
| accel/decel FF | 0.5/2.5 |
| brake Kp multiplier | 2.0 |
| unit accel limit | 1000rpm/s |
| Web rate/accel/decel | 720/5400/2250 deg系 |

確認12移動(`auto-tune/2026-07-31T10-53-38Z`)はfirst-entry平均/最悪0.301/0.313s、
実peak119.923rpm、overshoot最大7.647deg、terminal最大0.176degで12/12実用gate合格。
安全停止なし、28degC、最大指令/実測電流3348/2470raw。scale総時間0.151s、最長30ms。

### 現在の状態

- Flash boot既定は120/50、max60rpm、brake倍率1、FF0.5/0.5の安全側を維持。
- RAM/Webは上表の120rpm候補が適用されたまま、unit disabled、wheel=0、校正CRC正常。

### 次の作業

1. scale区間を加速/制動phase別に分け、P5電流拡張条件に合うか確認する。
2. unit 2/3・接地で同じ表を評価し、成立後にだけboot既定化する。

## 実装・検証(2026-07-31 P2 continuous gain schedule)

- 0/60/100/150rpm固定knot間でKp/Ki/加速FF/制動FF/Kawを線形補間し、
  `max(abs(reference),abs(observer))`の10ms LPFから実際のPI/FF/back-calculationへ接続した。
- legacy `SET_CONFIG idx3/4/18/20/25`は全knot同値へ戻す。個別設定はidx27..46を
  4 knot x `Kp/Ki/accelFF/decelFF/Kaw`として追加した。host testはknot、中央値、
  59.9/60/60.1、上端clamp、observer保持、reset、legacy互換、実PI適用をPASS。
- UNIT_STATUS_DIAG page 0/1/3を旧scalar値から補間後outputへ修正。Web UI `--check`、
  auto tuner/mode ID自己テスト、Python compile、ARM Debug build、Flash verify、diff checkをPASS。
  最終binは15532byte、MD5 `2297433648339d3359bc97be64b96a67`。

速度mode IDはWeb UI送信との競合で最初の100rpm試験がangle divergence停止したため、
角度目標を速度指令から積分し、STATUS3 ACTIVE脱落を監視、Web UI起動中は実行拒否するよう修正。
修正後100/150rpmは安全停止なし。150rpm比較:

| Kp/Ki | 正/負 rise90 | 正/負 peak overshoot | 正/負 tail MAE |
|---:|---:|---:|---:|
| 70/20 | 0.105/0.139s | 0/19.12% | 1.93/6.74rpm |
| 90/30 | 0.101/0.139s | 0/23.18% | 1.78/6.15rpm |
| 120/50 | 0.096/0.139s | 0.25/26.04% | 1.27/6.11rpm |
| 140/50 | 0.096/0.115s | 0.89/24.11% | 1.09/2.38rpm |
| 160/50 | 0.094/0.138s | 1.59/32.34% | 1.18/7.51rpm |

140/50を高速候補とした。閉ループ100rpmではKp 120/140/160、制動FF 0.5/1.5/2.5、
moving angle Kp 0..3、低速Ki 50/75/100、friction 200/300/400、hold angle Kp 4/6/8を
インターリーブ評価。gain/FF単独ではwheel=265のovershoot 6〜7degが残ったが、profile decelを
2250→1450deg/s2へ前倒しすると確認12移動で平均/worst settle 0.831/0.998s、最大overshoot
3.252deg、first-entry-2deg平均0.379s、最大指令/実測電流1838/1642raw、温度28degC、
scale/安全停止0。overshoot 12/12合格、settle 9/12合格のため候補止まり。

主要ログ:

- 速度ID: `steer-mode-id/2026-07-31T10-15-30Z`〜`2026-07-31T10-17-06Z`
- profile境界比較: `auto-tune/2026-07-31T10-27-51Z`、`10-29-12Z`
- 最終確認: `auto-tune/2026-07-31T10-35-07Z`

### 現在の状態

- runtimeはlegacy全band120/50、max60rpm、accel600rpm/s、FF0.5/0.5、Kaw0へ復帰。
  Web profile 360/3600/2250、cap60rpm、time scale1。disabled、wheel=0、角度232.119deg、
  28/26degC、AMT/C620 fresh、zero=1503/seq1/CRC正常。Web UI port8080起動中。

### 次の作業

1. 高速候補表をunit 2/3または接地条件へ展開し、個体/負荷差を先に評価する。
2. worst settle<=0.9sが共通に成立しなければP3明示加速度/model FFへ進み、unit 1の特定角へ過適合しない。

## 検証(2026-07-31 初回到達/再収束分離・Kawインターリーブ比較)

`unit_auto_tuner.py`へ`first_entry_2deg_s`、`first_entry_band_s`、`first_crossing_s`、
`resettle_after_entry_2deg_s`を追加し、見た目の速い初動とovershoot後の再収束を分離した。
`--compare-values`は1変数の明示候補を、同じ絶対角対・正逆・wheel条件へ均等配分する。
候補間でPI積分を持ち越さないよう、各 scored move後に通常STOP/Disableして次候補を適用する。
合格gateは全試行で安全停止なし、overshoot<=4deg、settle<=0.9s。

1反復screen(`auto-tune/2026-07-31T09-58-59Z`、各候補4移動):

| Kaw | 初回±2deg平均 | 再収束平均 | settle平均/最悪 | 最大overshoot | gate |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.288s | 0.549s | 0.837/1.069s | 9.053deg | FAIL |
| 1 | 0.326s | 0.358s | 0.684/0.797s | 5.977deg | FAIL |
| 2 | 0.283s | 0.562s | 0.845/1.160s | 4.570deg | FAIL |

Kaw=1は初回進入を速めず、飽和後の積分残りを抜いて再収束だけを約35%短縮していた。
ただし単発の可能性があるため、独立seedで2反復確認した。

確認(`auto-tune/2026-07-31T10-00-21Z`、各候補8移動):

| Kaw | 初回±2deg平均 | settle平均 | 最大overshoot | gate |
|---:|---:|---:|---:|---:|
| 0 | 0.292s | 0.689s | 5.273deg | FAIL |
| 1 | 0.318s | 0.757s | 13.447deg | FAIL |
| 2 | 0.320s | 0.924s | 12.217deg | FAIL |

全36/36移動が収束し、安全停止・温度異常なし。Kaw=1のscreen優位は再現せず、Kaw>0に
一貫した初回到達改善もなかった。P1単独調整はここで止め、Kaw=0のままP2速度scheduleへ進む。

### 現在の状態

- runtime Kp/Ki=120/50、steer max=60rpm、unit accel=600rpm/s、FF=0.5/0.5、Kaw=0/0、
  current limit=4000、status period通常値。Web profile=360/3600/2250、time scale=1。
- unit disabled、wheel=0、角度179.736deg、温度28/27degC、AMT/C620 fresh、校正CRC正常。

### 次の作業

1. P2の0/60/100/150rpm連続tableを全knot同値で実装し、59.9/60.0/60.1rpm等の連続性を試験する。
2. 低速knotのKawは0固定。高速knotはKp/Ki/制動FFと同時に決め、Kawだけを先に採用しない。

## 反復評価(2026-07-31 P1 back-calculation Kaw=0〜4)

予備A/BのKaw=2優位が再現するか、候補順を`3 -> 0 -> 4 -> 1 -> 2`として、
wheel=0/265rpm、正逆90deg、複数絶対角で追試した。Kaw=0/1/2/4は各8移動、Kaw=3は
`--evaluate-only`時にも`--rounds`既定3が適用されたため24移動となった。全56移動が収束し、
安全停止、通信異常、温度異常はなかった。

| Kaw | 移動数 | 平均settle | 最悪settle | 最大overshoot | deadline内 |
|---:|---:|---:|---:|---:|---:|
| 0 | 8 | 0.793s | 0.938s | 10.019deg | 1/8 |
| 1 | 8 | 0.854s | 1.573s | 10.723deg | 3/8 |
| 2 | 8 | 0.847s | 1.925s | 9.844deg | 1/8 |
| 3 | 24 | 0.857s | 1.432s | 12.569deg | 1/24 |
| 4 | 8 | 0.888s | 1.179s | 7.998deg | 1/8 |

Kaw=2の予備2/2、overshoot最大3.340degは再現しなかった。Kaw=4は全候補中の最大overshootを
最も小さくしたが8deg残り、settleもKaw=0より悪化した。Kaw=1はdeadline内3/8と最多だったが、
1.573sの外れ値があり採用できない。Kaw=0が平均・worst settleで最も安定しており、今回の
行列ではKaw>0をFlash既定へ採用する根拠が得られなかった。

`samples.csv`ではKaw=0/1/2/3/4の`scheduled_kaw`が全sampleで各指令値に一致した。
Kaw>0のsteer back-calculation補正も非ゼロで、最大絶対補正はKaw=1/2/3/4で
3.187/6.213/25.102/13.863raw/周期だった。設定未反映ではなく、方向・絶対角・wheel回転の
ばらつきがKaw単独効果を上回っている。

ログ:

- Kaw=3: `auto-tune/2026-07-31T09-45-01Z`
- Kaw=0: `auto-tune/2026-07-31T09-45-54Z`
- Kaw=4: `auto-tune/2026-07-31T09-46-24Z`
- Kaw=1: `auto-tune/2026-07-31T09-46-51Z`
- Kaw=2: `auto-tune/2026-07-31T09-47-20Z`

### 現在の状態

- Kp/Ki=120/50、steer max=60rpm、unit accel=600rpm/s、FF=0.5/0.5、Kaw=0/0、
  current limit=4000、status period通常値へ明示復元済み。
- Web profile=360/3600/2250deg系、time scale=1、wheel=0。unit disabled、角度171.299deg、
  温度30/29degC、AMT/C620 fresh、zero=1503/seq1/CRC正常。
- P1コードとtelemetryは維持するが、Flash既定はKaw=0のままとし、60rpm採用回帰は未実施。

### 次の作業

1. 同一開始角・方向の対ごとにKaw候補をインターリーブする比較手順を用意し、候補単位バッチの
   時間順バイアスを除去する。
2. wheel=0/265rpm、方向、到着角ごとに残差・back-calculation補正・settle外れ値を分解する。
3. Kaw単独で再現しなければ、P2の速度scheduleと制動FFを含む組合せで再評価し、Kaw=0を
   低速knotの安全な既定として維持する。

## 実装・予備評価(2026-07-31 P0 telemetry / P1 back-calculation)

将来の速度帯別gain scheduleを制御へ接続する前に、schedule信号とcurrent scale残差を観測する
P0を実装した。`steer_schedule_rpm=max(abs(steer_rpm_command),abs(observer_rpm))`を10ms LPFし、
現在はgainへ戻さず診断専用。scheduled Kp/Ki/加速・制動FF/Kaw、steer modeのscale前/後電流、
残差、連続飽和ms、制動phaseを`unit_control_output_t`へ追加した。

中央FD driverは未実装で現在のSocketCANもMTU=16のため、`0x1B0+id`を4pageのClassic
`UNIT_STATUS_DIAG`として暫定実装。STATUS3 bit11/12にもcurrent scale/制動phaseを追加した。
Web UI/API/画面とauto tuner samples/trials/summaryへ接続し、実steer peak、reference/actual
減速開始、scale総時間/最長時間も保存する。

P0 Flash後の60rpm回帰(`auto-tune/2026-07-31T09-31-27Z`)はwheel=0/265rpm正逆4/4収束、
平均0.7415s、最悪0.9381s、overshoot最大4.043deg。従来12移動平均0.8020s/最悪1.3915s/
最大4.571degに非劣化。scheduleは0〜77.31rpm、scheduled Kp/Kiは全sample 120/50、
最大電流1978rawでscaleなし、unsat=applied/残差0を確認した。

P1として、共通scale後の`applied-unsaturated`をsteer/drive別Kawで次周期の積分へ戻す
back-calculationを実装した。現周期motor指令、一周期遅れconditional freeze、mode比率は維持。
`SET_CONFIG idx25/26`は0〜20/s、既定0。host testはunsat137.5→applied100、残差-37.5、
Kaw=2/s、dt=1msで積分補正-0.075を固定。ARM build/Flash/verify済み。

150rpm級、wheel=0、正逆各1の予備A/B:

- Kaw=0 (`09-36-29Z`): 平均/最悪0.777/0.938s、overshoot最大11.426deg、deadline 1/2。
- Kaw=2 (`09-36-15Z`): 0.620/0.646s、最大3.340deg、deadline 2/2。
- Kaw=4 (`09-36-40Z`): 0.595/0.656s、最大3.867deg、deadline 1/2(約7ms超過)。

Kaw=2が予備最良だが各2移動だけなので未採用。Flash既定/runtimeともKaw=0へ復元した。
詳細は`docs/control/HIGH_SPEED_STEER_HANDOFF_2026-07-31.md`。

### 現在の状態

- Flash bin MD5 `5b8ec2aedcf418b7887c6f4da76801f3`、AMT zero=1503/seq1/CRC正常。
- runtime Kp/Ki=120/50、steer max=60rpm、unit accel=600rpm/s、FF=0.5/0.5、Kaw=0/0、
  status override=0。Web profile 360/3600/2250、time scale1。
- unit disabled、wheel=0、角度約1.49deg、温度27/26degC、AMT/C620正常。Web UI port8080起動中。
- host test、ARM Debug build、Web UI/auto tuner self-check、Python compile、diff checkは全PASS。

### 次の作業

1. Kaw=0/1/2/3/4をwheel=0/265rpm、正逆・複数絶対角で各最低6移動、順序ランダム化して再評価。
2. Kaw=2前後が再現すれば60rpm 12移動回帰後、Flash既定化してP1完了。
3. P2の0/60/100/150rpm連続gain tableを全knot同値から実装し、境界連続性をhost test。
4. `brake_onset_lag_s`は今回負値だったため、高rpm制動遅れ指標として使う前に定義を再検証。

## 計画確定(2026-07-31 高速ステアの速度帯別連続gain schedule)

AMT原点保存後のunit 1をwheel浮上、正逆90degで段階評価した。60rpm既定12移動は
平均settle 0.8020s、最悪1.3915s、overshoot最大4.571deg、最大電流1717raw。100rpm上限の
12移動は平均約0.789s、最悪0.898s、overshoot最大6.68deg、最大電流1942rawだった。
100rpmで`Kp=160/Ki=50/decel FF=1.5`は短い4移動screenで平均0.696s、最悪0.787s、
overshoot最大3.779degまで改善した。一方、Ki=25の短いscreen結果はfull scenarioで
wheel=0平均1.080sへ悪化し、少数試行だけでは採用できないことを再確認した。

さらにunit accel limitと中央profileを上げた結果、実速度自体は145〜156rpmへ到達した。

- unit accel 900rpm/s、profile 5400/5400deg/s2、decel FF=1.5:
  profile peak 117rpm、overshoot最大13.711deg、最大電流3779raw。
- 同条件decel FF=2.5: overshoot最大8.526deg、最大電流2402raw。
- unit accel 1200rpm/s、profile 7200/7200deg/s2、decel FF=2.5:
  profile peak 134rpm、実速度peak 145rpm、overshoot最大14.766deg、最大電流3289raw。
- unit accel 2000rpm/s、profile 12000/5400deg/s2、decel FF=2.5:
  profile peak 137rpm、実速度peak 156rpm、overshoot 10.195〜13.007deg、
  4000rawへ約70〜80ms飽和。

4000raw未満でも大overshootが発生し、decel FF=3.0/3.5で飽和を増やすと反動が悪化した。
したがって現在の律速は高rpm到達能力や単純な電流不足ではなく、減速時の固定PI/FFの位相、
二重ramp、飽和解除後の積分残りである。

`docs/control/HIGH_SPEED_STEER_GAIN_SCHEDULING_PLAN.md`を正本として追加した。実装順は、
P0 telemetry、P1 back-calculation anti-windup、P2 0/60/100/150rpm連続schedule、
P3 CAN FD明示加速度+モデルFF、P4 jerk制限付き非対称軌道、P5根拠付きcurrent limit拡張。
schedule変数は`max(abs(reference), abs(observer))`を10ms LPFし、Kp/Ki/加速・制動FF/Kawを
knot間で線形補間する。0〜60rpm採用値は維持する。

高速試験用にWeb UIのrate上限を2046deg/s、加減速上限を12000deg/s2へ広げ、auto tunerへ
unit側`steer_accel_limit_rpm_per_s`を追加した。Enable送信は2回行い、STATUS3 ACTIVEを
0.5s以内に確認できない場合はdisableして試験を中断する。Web UI/auto tuner self-checkはPASS。

### 現在の状態

- FlashはAMT原点保存済み採用版のまま。高速値はruntime試験だけで、既定変更や追加flashなし。
- runtimeはKp/Ki=120/50、steer max=60rpm、unit accel=600rpm/s、FF=0.5/0.5、
  Web profile rate=360deg/s、accel/decel=3600/2250deg/s2へ復元済み。
- unit 1はdisabled、wheel=0、最終角約1.49deg、温度28/27degC、AMT/C620正常。
- 主ログは`firmware/logs/auto-tune/2026-07-31T09-01-13Z`〜
  `firmware/logs/auto-tune/2026-07-31T09-12-05Z`。

### 次の作業

1. `unit_control_output_t`、VCP、CAN FDへschedule値、未飽和/適用電流、飽和時間、制動phaseを追加。
2. 共通current scale後の実適用電流を戻すback-calculation anti-windupを実装・host testする。
3. 速度mode step/PRBSで100/150rpm bandを同定し、連続scheduleを閉ループへ接続する。
4. 60rpm回帰後、100→120→150rpmと上げ、unit 2/3・接地条件へ展開する。
5. 加速区間の電流不足が20ms以上計測された場合だけ4500raw以降を段階評価する。

## 完了(2026-07-31 AMT原点のCRC付きFlash保存)

G474REの最終2KiBページ`0x0807F800`をリンカの`CALIB`領域として予約し、ファーム本体を
510KiBへ制限した。保存形式は24byteの追記レコード(magic/version/zero count/sequence/
reserved/CRC32/commit)で、85回分を保持できる。レコードは8byte単位で書き、commitを含む
最後のdoublewordを最後にプログラムする。スキャンはCRC不一致・電断途中レコードを飛ばし、
最新の有効sequenceを採用する。通常保存時は自動ページ消去せず、満杯時は安全に拒否する。

- `steer_calibration_test`: 空ページ、wrap減算、最新レコード、CRC破損、途中書込みからの
  旧値回復をhost試験しPASS。
- `UNIT_CTRL`: `0x02 CALIB_START`、`0x03 CALIB_SAVE_ZERO`、`0x04 CALIB_CLEAR`、
  `0x05 PING`。保存/消去はdisabled、AMT/C620 fresh、両motor output 1rpm以下のみ受理。
- `CALIB_RESULT 0x1C1`: zero/raw count、sequence、calibrated/CRC/page-full/last-op/raw-fresh flags。
- STATUS3 bench flags bit8〜10とerror bit6/8へ校正状態を反映。VCP idleへraw/zero/sequenceを追加。
- Web UIへ保存/読出し/確認付き消去APIと画面を追加。Enable中はGUI側でも拒否する。

Debug build 13,496byte、host tests、Web UI `--check`、`git diff --check`合格。
実機Flash/verify済み(bin MD5 `abcfb22608fec7d52f995fe771940759`)。機械原点姿勢の
AMT raw `1503`をsequence 1として保存し、`132.100deg -> 0.000deg`を確認。`st-flash reset`
後のboot bannerでも`valid=1 zero=1503 seq=1 crcErr=0 full=0`、idle/CAN角0deg、disabledを確認。

### 現在の状態

- unit 1校正済み。Web UIはport 8080で起動中。`enabled=false`、wheel=0、AMT/C620 fresh。
- 保存値はzero=1503、sequence=1、CRC正常、ページ空きあり。実機ではCLEARしていない。
- unit 2/3は未実施。

### 次の作業

1. unit 2/3の機械原点を合わせ、それぞれ保存・reset保持を確認する。
2. wheel=0でsteer capを100/150/200/300 axis rpmへ段階的に上げる。hard包絡341rpmは維持。
3. 接地3輪で中央flip/共通包絡/PRESTEERを統合試験する。

## 完了(2026-07-31 observer速度でbreakaway FFを整形、平均収束20.8%短縮)

相補observerを実制御へ接続する候補を実機A/Bした。

最初に、observer軸速度を外周終端ダンピングとして使う可変lookaheadを試した。wheel=0では
静止摩擦への再突入を増やし、wheel=265rpmでも確認12対12で基準平均0.7523sに対して
10msダンピング0.8536sへ悪化したため**不採用**。関連コードは最終版から除去した。

次に、wheel=0用`steer_friction_ff_current=200`を静止中だけbreakaway assistとして使い、
observer軸速度が上がるにつれて抜く方式を実装した。`steer_friction_ff_fade_axis_rpm=10`なら
0rpmで全量、10rpmで0まで線形減衰する。既存のwheel速度テーパと角度80〜235degブーストは
維持され、wheel>=30rpmでは従来どおりfriction FF自体が0なので走行中条件へ影響しない。

- 5/10/20rpmをscreenし10rpmを選択。
- ユーザーが触れた最初の1試行は集計から除外。その後の90deg・絶対角
  60→150→240→330→60degを順序反転しながら12対12比較。
- 一定FF: 平均0.9555s、中央値0.7800s、最悪2.0402s。
- observer速度減衰FF: 平均0.7570s、中央値0.7190s、最悪0.9747s。
- 平均20.8%短縮、最悪52.2%短縮、両候補とも12/12収束。

`SET_CONFIG idx24`(0〜100 axis rpm、0=減衰無効)とauto tunerパラメータ
`steer_friction_ff_fade_axis_rpm`を追加。host testでは静止時200raw、observer 10rpm時0rawを
固定した。既定10rpmへ変更しbuild/flash/verify後、wheel=0 12移動とwheel=265rpm 8移動を
回帰して20/20収束。wheel=0は平均0.7636s/中央値0.7092s/最悪1.4166s、wheel=265は
平均0.7735s/中央値0.7479s/最悪0.9726s。

### 現在の状態

- Flash済みbin MD5 `5a48f40f44db9f6f19a6faee545043a3`。
- observer補正tau=50ms、friction FF fade=10 axis rpm。角度P、`MOTION_SETTLED`、安全判定は
  observerへ接続せず従来のAMT角/mode速度を維持。
- STOP/disable後idle、最終角59.854deg、wheel=0、AMT/C620正常、試験プロセス終了済み。
- A/Bログ: `firmware/logs/webui-2026-07-31T08-18-51Z.log`。採用版Flash回帰:
  `firmware/logs/webui-2026-07-31T08-21-54Z.log`。

### 次の作業

1. 採用版で残った150deg到着1.4166s外れ値を、角度依存機構抵抗・observer速度・PI積分で解析。
2. wheel=1〜29rpm、接地、3輪条件でfade遷移域を回帰する。
3. observer角を制御/判定へ広げる前にAMT/C620 fault注入とinnovation閾値を確定する。

## 完了(2026-07-31 P1.5 相補observerの診断実装・実機wrap回帰)

`unit_controller_update()`の1kHzループへ相補observerを追加した。既存2ms LPF後の
steer common-mode rpmへ軸比8/11を掛けて角度を予測し、AMT22絶対角との
`shortest_angle_error()`を既定50ms時定数で補正する。初回および
`unit_controller_reset()`後はAMT角を直接seedするため、未初期化角からの過渡を作らない。
推定速度はmotor由来の軸rpmへAMT補正角の微分成分を加え、補正後角度の変化率と整合させた。

- `unit_control_output_t`: `steer_angle_observer_deg`、`steer_axis_observer_rpm`、
  `steer_observer_innovation_deg`を診断出力。
- VCP: `obsA/obsR/obsE`、Web UI: observer角/速度/innovationを表示。
- `SET_CONFIG idx23`: 補正時定数0〜1s、既定0.050s。0はAMT直接追従の診断値。
- `unit_auto_tuner.py`: `steer_observer_tau_s`と3 observer列を追加。
- `firmware/scripts/test-host.sh`: 初回seed、359.9→0.26deg wrap、低周波ドリフト補正、
  tau=0、reset再seedをhost Cコンパイルで検証しPASS。

ARM Debug build、Web UI self-check、auto tuner self-check、Python構文、host test、
`git diff --check`を通し、Flash write/verify完了(bin MD5
`36452ab63553e842c338604a8c802cdb`)。ターゲット側のboot banner、AMT/C620 freshも確認した。

実機はwheel=0と、実wheel=265rpm到達・保持を明示確認した条件で330↔30degを含むwrap試験を
実施し全移動収束。ログ`firmware/logs/webui-2026-07-31T08-05-04Z.log`のVCP run行292点を
同一時刻値として解析し、AMT innovationは最大2.172deg/p95 0.954deg、observer-AMT差は
最大2.130deg/p95 0.936deg、静止時observer-AMT差は最大0.416deg/p95 0.086degだった。
境界通過でも±360degスパイクなし。idx23を20msへ変更するack後、50msへ復元するackも確認。

### 現在の状態

- observerは**診断専用**。角度P、`MOTION_SETTLED`、安全判定の入力は従来のAMT/mode速度の
  ままであり、実機挙動を変更しない。
- Flash/RAMとも補正時定数50ms。通常STOP/disable後idle、最終角30.146deg、wheel=0、
  AMT/C620正常。Web UI/試験プロセスは終了済み。

### 次の作業

1. 接地・3輪、冷間、荷重、問題角度帯でinnovationの正常p95/p99を採り、滑り/バックラッシュ
   診断の振幅閾値と継続時間を決める。
2. observerを制御へ接続する前に、AMT異常時、C620欠落時、ratio誤差、実滑りを注入した
   fault試験を追加する。
3. 閾値確定まではobserverを制御・settled・安全判定へ接続しない。

## 完了(2026-07-31 角度境界・wheelカップリング回帰、60rpm段階採用)

前セッションの角度依存friction補償(80〜235deg、5deg ramp、最大2倍)を引き継ぎ、
計画の残りを実機で継続した。

- wheel=0で補償境界周辺60〜100deg/215〜255degを10deg刻み・両方向から42試行し42/42。
  最大残差0.381deg、最大収束1.652s、温度28/27degC。
- wheel=75/265rpmで問題角域を各24試行し48/48。最大残差0.225deg、最大収束1.117s、
  `LIMITING_ACTIVE`なし。wheel=15rpmはステア誤差0.049degまで到達したが、既知の低速
  drive stick-slipで実wheel=19.2rpmに残り、総合`MOTION_SETTLED`だけ不成立だった。
- 加速/制動FF 0/0.5/1.0を自動チューナで比較。制動1.0は一部バッチで改善したが、
  絶対角0/90/180/270degを含む16対16比較で1.653sの外れ値が出たため、ロバスト性優先で
  現行0.5/0.5を維持した。
- Web側capだけでなくユニット側runtime `steer_max_rpm`も同時に40→60rpmへ上げて再試験。
  角度境界・wheel=0/265を含め26/26合格したため、既定を60rpm/360deg/sへ昇格した。
- 次段階80rpmは14/14で安全に収束したが、60rpm比で90deg移動が平均約0.78→0.92s、
  最悪0.99→1.36sへ悪化したため不採用。100rpmへは進めなかった。
- `SET_CONFIG steer_max_rpm`の試験用clampを60rpm固定からhard包絡のwheel=0相当341.1rpmへ
  拡張。通常はWeb/中央のcommissioning cap=60と469rpm diamond射影が制限する。
- 自動チューナとmode IDツールが試験後に採用済みfriction FF=200を0へ戻す引き継ぎ漏れを
  修正。自動チューナがtime scaleを旧値2.0へ固定復元する処理も、開始時値へ戻す方式へ修正。
- build、Web UI self-check、auto tuner self-check、Python構文、`git diff --check`合格後、
  `st-flash`で書込み・verify。新flashの60rpm既定でも14/14回帰合格。

### 現在の状態

- Flash済み: steer max 60rpm、Kp/Ki=120/50、FF accel/decel=0.5/0.5、friction FF=200
  (wheel 30rpmテーパ、80〜235deg最大2倍)、time scale=1、mode diamond射影、連続deadband。
- Web UI既定: commissioning cap=60rpm、rate max=360deg/s、time scale=1.0。
- 実機は通常STOP後idle。温度28/27degC、異常停止・包絡制限発動なし。

### 次の作業

1. 80rpm再評価前に、加速・制動FFまたは内周追従の外れ値を追加ログで切り分ける。
2. 接地・3輪が用意できたらロードマップ手順5を開始する。
3. P1.2 back-calculation anti-windupは通常試験でcurrent scaling未発動だったため、
   飽和を安全に再現できる専用試験を設計してから実装する。
4. P0.1連続unwrap角、時刻付きCAN FD軌道、Teensy中央状態遷移は未着手。

## 完了(2026-07-31 角度依存friction FFブーストで90-225deg帯のstallを解消)

ユーザーが90-225deg帯を物理点検し、3Dプリント部品の積層継ぎ目の出っ張りが抵抗に
なっている可能性が高いと判断(機構修正はせず、制御側で吸収する方針)。

`unit_controller.c`の既存friction FF(wheel依存テーパ付き)に、AMT角度80-235deg
(実測範囲90-225degへ5deg余裕を追加)で最大2倍(200→400raw相当)まで線形にブースト
する項を追加した。バンド境界は5degで滑らかにランプイン/アウトし、トルク段差を作らない。
位置トリガー(積分ではなく現在角度で判定)のため、残差誤差の大小によらず即座に効く。

build/flash/verify後、**問題を特定した同じ8方向×3往復(48試行)を再実施し48/48で完全解消**
(前回45/48、90-180ペア5/6・135-225ペア4/6が今回は各6/6)。最大残差も0.264-0.879deg→
0.176-0.352degへ改善。

### 現在の状態

- Flash済みfirmwareに角度依存friction補償(80-235deg帯、最大2倍)を追加。
- 8方向×3往復の実機再検証で48/48。ユニットはidle、健全。

### 次の作業

1. より広い振れ幅(45deg以外の到着角度、例えば10deg刻み)でバンド境界(80/235deg)の
   位置精度を追い込む。
2. wheel≠0でもこの角度帯のカップリングに問題がないか確認する
   (wheel_friction_taperにより通常は無効化されるが、ゼロ近傍のPRESTEER相当条件で確認)。
3. 4基とも同じ3Dプリント部品を使う場合、他ユニットでも同様の角度依存点検・補償が
   必要になる可能性がある。

## 完了(2026-07-31 間欠stallが特定角度帯に偏っていることを実測で特定)

## 完了(2026-07-31 commissioning cap引き上げが無効化されていたバグを修正)

前々セクションで実装した`steer_commissioning_cap_rpm`(動的envelope)を実際に60rpmへ
上げてテストしたところ、`hard_min_s`/`planned_min_s`が全く変化せず、40rpm相当のままだった。
原因は`handle_set()`の`steer_rate_dps`クランプが依然固定`STEER_RATE_DPS_MAX=240`
(=40rpm相当)を使っており、capを60へ上げてもリクエスト自体が240dpsで頭打ちにされて
いたため。**動的cap機構を実装した際、入力バリデーション側の固定上限を追従させ忘れていた
抜けだった。**

`handle_set()`のsteer_rate_dpsクランプを、`steer_commissioning_cap_rpm`(None時は
`STEER_COMMISSIONING_CAP_RPM_CEILING`=341.1rpm)に追従する動的上限へ修正。
self-check(既定cap=40のときは240dpsのまま、期待値不変)は合格を維持。

修正後、cap=60・360dps要求で90deg往復8/8成功(wheel=0/265rpm、elapsed 0.69-1.08s、
理論比1.8-2.8x)。ただし今回1バッチのみのため、既定capは40のまま据え置く。

### 現在の状態

- `unit_web_ui.py`の`steer_commissioning_cap_rpm`は本来の意図通り機能するようになった。
- 既定値は`steer_commissioning_cap_rpm=40`のまま(変更なし)。
- ユニットはidle、健全。

### 追加検証(2026-07-31同日)

別絶対角域(36.3/306.3deg)・wheel=0/600/1000rpmでcap=60を追加検証したところ**7/8**
(1件、wheel=0で0.616deg残り6秒未収束)。cap=40既定でも同程度の間欠stallが残っている
ため、cap=60固有の悪化かは断定できないが、**既定への格上げは時期尚早**と判断し
40のまま維持することにした。cap=60自体は動作すること(15/16)は確認済み。

### 追加検証: 間欠stallの角度依存性を定量化(2026-07-31同日)

wheel=0、time_scale=1.0、cap=40(現行既定)で、45deg刻み8方向×各3往復(48試行)を
実施した。

| 角度ペア(deg) | 結果 |
|---|---|
| 0↔90, 45↔135, 180↔270, 225↔315, 270↔0, 315↔45 | 各6/6(stallなし) |
| 90↔180 | 5/6(90degへの到着で1件stall、残差0.879deg) |
| 135↔225 | 4/6(135deg到着1件・225deg到着1件がstall) |

**合計45/48。stallは0-90deg/225-360deg帯では0件、90-225deg帯に集中(4件中3件)。**
ランダムな摩擦変動ではなく特定角度帯へ偏っており、その帯域だけ機構側(ケーブル配線の
突っ張り、特定角度でのプリロード変化、配線材のたわみ等)に何らかの偏りがある可能性が
高い。制御ゲインだけでは解決しない可能性がある。

### 次の作業

1. **要現物確認**: 90-225deg帯(AMTゼロ点基準)でユニットを手動でゆっくり回し、
   ケーブル・ハーネスの突っ張り/擦れ、機構的な引っかかりがないか目視・触診で確認する。
   電気的対策(anti-windup等)より先に、この物理原因の有無を切り分けるべき。
2. 物理原因が見つからない場合は、この角度帯だけの局所的な摩擦補償(角度依存Coulomb FF
   テーブル)やP1.2 anti-windupを検討する。
3. cap=60/80への格上げは、この角度依存stallの原因判明後に再検討する。

## 完了(2026-07-31 mode ID wheel=265/600/1000rpm展開・ロードマップ手順1完了)

## 完了(2026-07-31 mode IDをwheel≠0へ展開、手順1完了)

`unit_steer_mode_id.py`は従来wheel=0固定だったが、`--wheel-rpm`を追加して
wheel=265/600/1000rpmでのsteer mode速度step応答も測定できるようにした。
安全のため、テスト前後に`WHEEL_DECEL_RPM_PER_S=500`でwheelをramp up/downしてから
enable/disableする(disable時にwheelが回転中のままにならないよう、atexitの`restore()`
経路も含めて対応)。

現行flash値(Kp=120/Ki=50/tau=2ms、amplitude=20axis rpm)で測定:

| wheel rpm | 正方向overshoot | 負方向overshoot | tail_mae(正/負) |
|---:|---:|---:|---|
| 0 | 1.4% | 34.1% | 1.43/1.39 |
| 265 | 7.5% | 10.2% | 0.60/0.57 |
| 600 | 7.4% | 7.5% | 0.34/0.33 |
| 1000 | 8.2% | 8.2% | 0.29/0.49 |

**wheel≠0では正負がほぼ対称でtail_maeも小さく、現行ゲインは差動mode干渉下でも良好。
非対称・非収束が集中していたのはwheel=0近傍だけ**であることが裏付けられた
(friction FFテーパの設計方針と整合)。ロードマップ手順1(速度mode単体同定の
wheel=0/265/600/1000/1200rpm展開)を完了した(1200rpmのみ未実施)。

### 現在の状態

- `unit_steer_mode_id.py`は`--wheel-rpm`対応。既定は0(後方互換)。
- 全wheel rpmでハードウェアは健全、idleへ復帰確認済み。

### 次の作業

1. wheel=1200rpmのmode IDも実施する。
2. ロードマップ手順2(加速・制動FF同定)へ進む。
3. 本セッションで得たすべての知見をTeensy中央実装(未着手)へ将来反映する。

## 完了(2026-07-31 time scale既定を理論値1.0へ格上げ、2絶対角×34/34合格)

## 完了(2026-07-31 time scale既定を1.0へ格上げ)

前セクションの1.1採用後、別の絶対角域(45/135deg、従来の174.9/264.9degから90deg以上離れた
未検証領域)でwheel=0/265/600rpmの12試行を追加実施し**12/12合格**。従来の22/22(174.9/264.9deg域)
と合わせて**2つの絶対角域・計34/34でtime scale=1.0が安定**と確認できたため、
`unit_web_ui.py`の`TRAJECTORY_TIME_SCALE_DEFAULT`を1.1→**1.0(理論Tfeasibleそのもの)**へ
格上げした。self-check合格。

### 現在の状態

- `unit_web_ui.py`既定`trajectory_time_scale=1.0`。ロードマップ手順3
  (time scale段階縮小 2.0→1.5→1.25→1.1→1.0)は完了。
- Flash済みfirmwareはKp=120/Ki=50・wheel依存テーパ付きfriction FF=200・P0.3・P1.4のまま。
- ユニットはidle、健全。本セッションの実機トライアル総数は概算150件超。

### 次の作業(ロードマップ残項目)

1. 手順1の残り: steer mode速度同定をwheel=265/600/1000/1200rpm(差動mode干渉)へ展開する
   (今回はwheel=0のみ)。
2. 手順2: 加速・制動FFの再同定(冷間/暖機、絶対角0/90/180/270deg別)。
3. 手順4: 速度・加速度包絡拡張(commissioning cap 40→60→80→100rpm)。P0.3のdiamond射影と
   動的cap機構は実装済みなので、拡張自体はcapの数値変更のみで着手できる。
4. 手順5: 接地・3輪回帰(治具・実機3台待ち)。
5. Teensy中央実装(現時点でコード不存在、ドキュメントのみ)。

## 完了(2026-07-31 time scale 2.0→1.1既定化、1.0まで22/22実機合格)

## 完了(2026-07-31 time scale段階短縮・理論値1.0まで到達確認)

friction FFテーパ採用後、`docs/control/CENTRAL_COORDINATED_CONTROL.md`ロードマップ手順3
(time scale 2.0→1.5→1.25→1.1→1.0)を実機で一気に検証した。各段階でwheel=0/265rpm
(一部600/1000rpmも)×往復10試行前後を`unit_web_ui.py`のMOTION_SETTLED基準で実施。

| time scale | 試行 | 結果 | elapsed_s範囲 |
|---:|---:|---|---|
| 1.5 | 10 | 10/10 | 0.97-1.33 |
| 1.25 | 10 | 10/10 | 0.77-1.23 |
| 1.1 | 10 | 10/10 | 0.74-1.08 |
| 1.0 | 22 (wheel=0/265/600/1000混在) | **22/22** | 0.67-1.18 |

**time scale=1.0(理論Tfeasibleそのもの、予備マージン無し)で22/22全収束。**
旧記録(2026-07-30時点)では「倍率1の厳しいゲイン試験は収束11/12、2*Tmin以内7/12」と
不安定だったが、friction FFテーパ+P0.3/P1.4を経て大幅に改善した。wheel=1000rpmでは
elapsed 1.13-1.18s/planned_min 1.0s=理論比1.13-1.18倍まで到達。

サンプル数(絶対角2点×各条件)はまだ限定的なため、既定値は理論限界の1.0ではなく
一段階手前の**`TRAJECTORY_TIME_SCALE_DEFAULT = 1.1`**(`unit_web_ui.py`)を採用した。
1.0は有望だが、より多様な絶対角・複数セッションでの追加サンプルを取ってから既定へ格上げする。

### 現在の状態

- `unit_web_ui.py`の既定`trajectory_time_scale`は1.1(旧2.0)。self-check合格。
- Flash済みfirmwareは変更なし(前セクションのKp=120/Ki=50・friction FF=200テーパ付き)。
- ユニットはidle、健全。

### 次の作業

1. 複数絶対角・複数セッションでtime scale=1.0のサンプルを増やし、既定への格上げを判断する。
2. wheel=1200rpmでのtime scale段階短縮も確認する。
3. Teensy中央側へ、検証済みのfriction FFテーパ・time scale短縮を移植する
   (ロードマップ: 3輪協調・100Hz中央プロファイルへの反映)。

## 完了(2026-07-31 wheel依存テーパ付きCoulomb FFを採用・flash・全域A/B合格)

## 完了(2026-07-31 wheelテーパ付きfriction FF採用)

前セクションの診断(定数Coulomb FFはwheel=0のstallを消すがwheel≠0を悪化させる)を受け、
`unit_controller.c`へ`WHEEL_FRICTION_TAPER_RPM=30`のテーパを実装した。
`|target_wheel_rpm|`が30rpmを超えると`steer_friction_ff_current`を線形に0まで減衰させ、
wheel=0近傍(pre-steerのユースケース)だけに効かせる。

- wheel=0: friction_ff=200で14/14 stall解消、1.20〜1.38s安定(理論比2.6〜3.0x)。
- wheel=265/600rpm: テーパにより無影響を確認(1.18〜1.49s、テーパ導入前の基準と同等)。
- `main.c`既定値を`steer_friction_ff_current=0→200`へ変更し、build/flash/verify済み。
  Flash後の最終確認(wheel=0/265/600混在8試行)は8/8収束、1.18〜1.59s、
  残差0.002〜0.27deg。

### 現在の状態

- Flash済み既定値: `steer_mode_kp=120`, `steer_mode_ki=50`, `mode_rpm_filter_tau_s=0.002`,
  `steer_friction_ff_current=200`(新規、30rpm以上でテーパアウト)。他は従来通り。
- P0.3(mode包絡射影)・P1.4(連続デッドバンド)も含め、wheel=0/265/600/1000/1200rpmの
  幅広い条件で健全性・収束を確認済み。
- ユニットはidle、健全。

### 次の作業

1. wheel=1000/1200rpmでもテーパ導入後の回帰を確認する(テーパ計算上は30rpmで完全に0になる
   ため理論上無関係だが、実機未確認)。
2. `WHEEL_FRICTION_TAPER_RPM`や`steer_friction_ff_current=200`は今回の限られた試行数での
   結果のため、絶対角を変えた反復でロバスト性を追加確認する。
3. 残る絶対角依存の変動(0.5deg弱で数百ms揺れるケース)がfriction FF導入後にどう変化したか、
   より長時間バッチで統計を取る。
4. time scale 2.0→1.5等の段階的縮小(ロードマップ手順3)へ進む土台が整った。

## 完了(2026-07-31 間欠stallの原因特定・Coulomb FFはwheel依存で不採用継続)

## 完了(2026-07-31 間欠非収束の原因特定・Coulomb FF再検証)

5-6回に1回発生する「0.5deg強で数秒粘る」非収束を`unit_web_ui.py`のtelemetryで直接診断した。
stall中の生ログ: `m1=0/2898 i1=450 ... steerMode=2898/0 iSteer=450034 sInt=102279`。
**commanded current(i1=450raw)が既知のbreakaway電流(850-950raw、2026-07-05/06実測)の半分
程度しかなく、`steer_min_rpm=0`で床が無いため、純積分(Ki=50)だけでbreakawayを超えるまで
待つ構造になっていた。** これが小さな残差(0.3〜0.5deg強)からの最終収束が角度・履歴依存で
不安定になる直接原因。

`steer_friction_ff_current`(index21、Coulomb FF、現在0)を再検証:
- **200/300rawともwheel=0では16/16 stall解消**(300は1.3-1.7s、200は1.20-1.30sで
  より一貫性が高い)。
- **しかしwheel=265rpmでは200raw投入により1.1-1.4s→2.4-4.0sへ悪化**
  (friction_ff=0に戻すと即座に1.1-1.4sへ復帰、再現確認済み)。
- 結論: 定数Coulomb FFはwheel=0のstallを消す一方でwheel≠0の収束を悪化させるトレードオフが
  あり、過去(2026-07-30)に「不採用」と判断された理由(非収束数の増加)と一致する。
  **全wheel rpm一律のCoulomb FFは不採用のまま維持し、index21=0.0へ復元・確認した。**

### 現在の状態

- Flash済み既定値・RAM上のconfigとも変更なし(Kp=120/Ki=50/tau=2ms、friction FF=0)。
- ユニットはidle、健全。

### 次の作業

1. **正しい方向性**: 定数FFではなく、wheel rpm(=drive mode)でスケジュールする、または
   電流・速度残差から低帯域外乱を推定するbounded DOB(P2.1)で、wheel=0近傍でだけ
   breakaway相当の補償を効かせ、wheel≠0では効かない設計にする。
2. あるいはP1.2 back-calculation anti-windupで、小さい要求に対する積分の立ち上がりを
   加速する(現在のconditional freezeは飽和時に凍結するだけで、非飽和の小電流域での
   積分加速はしていない)。
3. 定数FFの再挑戦をする場合は、必ず今回同様にwheel=0とwheel!=0の両方でclosed-loop
   MOTION_SETTLED A/Bを取ってから採否判断する。

## 完了(2026-07-31 Kp=60/Ki=100は閉ループで悪化と判明・120/50へ復元)

## 完了(2026-07-31 Kp=60/Ki=100は closed-loop 収束を悪化させると判明、120/50へ復元)

前セクションでKp=60/Ki=100をflashし、`unit_bench.py`の生step(外周そのまま、firmware内蔵の
加速ランプのみ)で30試行(wheel=0/265/600/1000/1200rpm)全て0.5deg以内という結果を得たが、
これは製品契約(`unit_web_ui.py`のtime_scale=2プロファイル+FF+MOTION_SETTLED判定)での
実際の収束時間を測っていなかった。

`unit_web_ui.py`のHTTP APIを安全な停止手順(`/api/stop`=減速後disable、`unit_bench.py run`の
即時disableは絶対に使わない — 下記「重要な事故回避」参照)で駆動し、wheel=0の90deg往復を
新旧ゲインでA/B比較したところ、**Kp=60/Ki=100は明確に悪化**(6試行: 1.8/2.2/6超未収束/1.7/1.8/3.7s、
理論比3.7〜8倍)、**Kp=120/Ki=50は従来通り良好**(6試行中5/6が1.10〜1.18s=理論比2.4〜2.6倍、
1/6は6秒超で0.615deg残り、既知の絶対角依存stallと一致)と判明。inner loopのKpを下げると
mode速度step応答は綺麗になる(overshoot 0%)が、outer angle-P loopから見た応答性が落ち、
FFが切れた後の追い込みが遅くなる・稀に静止摩擦を割れず停止する、という副作用があった。

**教訓: inner loopゲイン候補は外周を切ったstep/PRBS応答だけで採否を決めず、必ず
`unit_web_ui.py`のMOTION_SETTLED(closed-loop・製品契約)で最終検証してから採用する。**

`main.c`のKp/Ki既定値をKp=120/Ki=50へ戻し、build/flash/verify(st-flash)済み。
戻した状態で同条件を再度回し、5/6が1.10〜1.18s、1/6が絶対角依存stallという
既存の実績(過去セッションの11/12相当)と一致することを確認した。

### 重要な事故回避(2026-07-31)

`unit_bench.py run`はduration経過後に`UNIT_CTRL disable`を無条件即送信する実装で、
wheel=600/1000/1200rpmのフル回転中に何度も即断したところ、ユーザーから
「制動が急すぎて電圧上昇で電源落ちる」と警告を受けた。`ARCHITECTURE_DECISIONS.md`の
既定方針(「通常STOPは減速完了見込み後にdisable」)に反する使い方だった。
**今後、wheelが0でない状態のテストは`unit_web_ui.py`の`/api/stop`(減速→disable)経由でのみ
行い、`unit_bench.py run`の即時disableはwheel=0のときだけに限定する。**
ハードウェア自体に損傷は確認されていない(idle・feedback OK・温度正常に復帰)。

### 現在の状態

- Flash済み既定値はKp=120/Ki=50/tau=2ms(元の値)へ復元済み。P0.3(mode包絡射影)・
  P1.4(連続デッドバンド)は引き続きflash済み(これらはwheel=0/265/600/1000/1200rpmの
  生step回帰30試行で既に健全性確認済みで、今回の悪化はKp/Ki変更のみが原因)。
- ユニットはidle、健全。

### 次の作業

1. 絶対角依存の未収束(5-6試行に1回、0.5deg強で6秒粘る)を、角度を揃えた反復試験で
   再現・定量化する。back-calculation anti-windupや摩擦推定DOBが効く可能性がある。
2. inner loopゲイン改善を再挑戦する場合は、必ずclosed-loop MOTION_SETTLEDでA/B比較してから
   flashする(生step結果だけで判断しない)。
3. `unit_bench.py`の`run`コマンドに減速してからdisableする安全な終了処理を追加することを検討する
   (現状は呼び出し側が`/api/stop`相当を自前で組む必要があり、事故の元)。

## 完了(2026-07-31 新ゲインflash・全wheel rpm域で回帰合格)

Kp=60/Ki=100/tau=2ms(前セクション)を`main.c`既定値へ反映し、P0.3(mode包絡射影)・
P1.4(連続デッドバンド)込みでbuild/flash/verify(st-flash、MD5一致)した。
`unit_bench.py run`で±90deg往復をwheel=0/265/600/1000/1200rpmそれぞれ3往復(計30試行)
実施し、**全試行で最終誤差0.5deg以内(実測0.000〜0.439deg)、STOP異常・温度異常なし**
(t1/t2は27→32degCで単調微増、上限に対して十分余裕)。wheel=1000/1200rpmはplanned steer
包絡が既にかなり狭い(理論7〜57軸rpm)領域でP0.3のdiamond射影が実際に効く条件だが、
問題なく収束した。

### 現在の状態

- Flash済み既定値: `steer_mode_kp=60`, `steer_mode_ki=100`, `mode_rpm_filter_tau_s=0.002`
  (他は従来通り: angle Kp hold=4/moving=1, deadband=0.3deg, accel/decel FF=0.5/0.5)。
- P0.3/P1.4含め実機で健全性確認済み。ユニットはidle、温度は常温域まで放熱待ち。

### 次の作業

1. `unit_web_ui.py`側(プロファイル付きtime scale=2の本番相当試験)でも新ゲインの
   Tsettle/Tfeasibleを測り、旧Kp=120/Ki=50比でどれだけ理論値へ近づいたか定量比較する。
2. 収束が安定していればtime scale 2.0→1.5→...→1.0の段階的縮小に進む(ロードマップ手順3)。
3. 絶対角依存の再現性検証(同一角度での反復)はまだ未実施。

## 完了(2026-07-31 実機steer mode速度同定・Kp/Ki候補発見)

## 完了(2026-07-31 実機wheel=0 steer mode速度同定・新Kp/Ki候補)

`unit_steer_mode_id.py`(外周Kp=0、Ki=0）でwheel=0のstep応答をKp×LPF tau×振幅で
実機グリッド走査した(計70+トライアル、`firmware/logs/steer-mode-id/`)。

- **Kp=60はKi=0で全tau(0/0.5/1/2ms)・振幅5-40rpmで正逆ともovershoot 0%**。
  現flash値Kp=120はKi=0時点で負方向34%overshoot(振幅20rpm)と、そもそもKpが
  安定域を超えていたことが判明。
- 同一条件を繰り返すと結果が変動(例: Kp150/tau2msで正方向overshootが8%→67%)。
  正負非対称ではなく**直前の履歴・絶対角に依存**する挙動で、既知の
  「絶対角依存の再現性未解決」課題と符合。セッション中に角度が正味94deg程度drift。
- Kp=60を土台にKi/tauを追加走査し、**Kp=60, Ki=100, tau=2ms**が振幅20/40rpmで
  overshoot 2-5%、定常偏差(tail_mae) 0.5-1.9rpmまで低減(Ki=0時の2.4-2.7rpmから改善)
  という候補を得た。
- 外周(angle P)を有効にした状態で`unit_bench.py`により実90deg往復(SET_CONFIG idx3=60/
  idx4=100/idx13=0.002を一時適用)を実施。+90deg最終誤差0.088deg、-90deg最終誤差0.264deg、
  いずれも振動なく収束。試験後はKp=120/Ki=50/tau=2ms(現flash値)へSET_CONFIGで復元済み
  (RAM上のみの変更でFlashは書き換えていない)。

### 現在の状態

- Flash済み既定値は変更なし(Kp=120/Ki=50/tau=2ms のまま)。今回のKp=60/Ki=100候補は
  RAM上でのみ検証し、試験後に復元した。ユニットはidle、角度は約174.5deg(セッション開始時
  266.8degから正味drift)。
- 新候補はwheel=0限定の検証。wheel≠0での差動mode干渉は未確認。

### 次の作業

1. Kp=60/Ki=100/tau=2msをmain.cの既定値へ反映し、build/flash/verifyしてから
   wheel=0/265rpm正逆90degの回帰(現行12/12基準)を取り直す。
2. 絶対角依存の再現性(同一ゲインでも試行ごとにovershootが変わる)を、角度を揃えた
   反復試験で定量化する。
3. wheel=265/600/1000/1200rpmでも同じKp/Ki候補が安定か確認する(differential mode干渉)。

## 完了(2026-07-31 P0/P1実装: mode包絡射影・動的commissioning guard・連続デッドバンド)

## 完了(2026-07-31 P0.3 mode包絡射影・P1.4連続デッドバンド・動的commissioning guard)

ユーザーが`unit_steer_mode_id.py`でwheel=0外周切りのsteer mode速度step/PRBS同定を実機で
進めている間、実装計画のうち再フラッシュ待ちで安全に進められるコード変更を実施した。

- **`firmware/src/control/unit_controller.c` P0.3**: 旧`available_drive_motor_rpm`方式
  (steerを先に確定させ、drive/wheelが残り予算を受け取る非対称clamp)を撤去し、
  `requested_steer_mode_rpm`と`requested_drive_mode_rpm`(=`target_wheel_rpm/drive_ratio`)の
  和が`motor_max_rpm`(469rpm)を超えたときだけ両者へ同一`envelope_scale`を掛ける対称射影へ
  置き換えた。モード変換が線形なため、各モードの加速ランプへ入る前(軸rpm単位)でスケールを
  掛けても、モードrpm単位で掛けるのと等価。`output->limiting_active`はこの新しいscale発動
  (旧: wheelがsteer優先で削られたか)を表す値へ意味を更新した(STATUS3 `LIMITING_ACTIVE`ビット
  の文書上の意味「rpm包絡の保護制限が作動」とは整合、ドキュメント変更不要)。
  wheel=0/265rpmのような非飽和域の現行試験には数値上の影響なし(469rpm予算に対して十分小さい)。
- **`unit_controller.c` P1.4**: angle P項のdeadband処理を、`|error|<angle_deadband_deg`で
  P項を完全に0にする旧実装から、`angle_kp*error*(|error|/angle_deadband_deg)`の二次テーパへ
  変更した。境界(`|error|==angle_deadband_deg`)で`angle_kp*error`と連続に一致するため、
  旧実装にあった境界での不連続な0への落ち込み(chatterの一因)を解消する。
  `unit_steer_mode_id.py`は外周(angle P)を切って同定するため、進行中の実機試験には無関係。
- **`tools/linux/unit_web_ui.py` 動的commissioning guard**: `steer_rate_available_dps()`へ
  `commissioning_cap_rpm=STEER_AXIS_MAX_RPM`引数(Noneで無効化)を追加し、`motion_timing()`・
  `can_tx_loop()`・`build_status_json()`・`handle_set()`へ配線した。`AppState`に
  `steer_commissioning_cap_rpm`(既定40rpmのまま)を追加し、`POST /api/set`の
  `steer_commissioning_cap_rpm`(数値または`null`)で実行時に変更できる。GUIに
  数値入力+有効/無効チェックボックスを追加。既定値・`STEER_RATE_DPS_MAX`(240dps)・
  既存self-checkの期待値はすべて変更していない。
- 検証: `firmware/scripts/build.sh debug`成功(FLASH 10776B、旧10716Bから+60B)、
  `python3 tools/linux/unit_web_ui.py --check`合格(新規cap関連アサーション追加込み)、
  JS構文チェック(`node --check`)合格、`git diff --check`合格。
- 見送った項目と理由:
  - **P1.2 back-calculation anti-windup**: 現行の「combined_saturated(前サイクルの合成電流
    飽和)で次サイクル両積分器を丸ごと凍結」という粗いが安全な方式を、正しいback-calculationへ
    置き換えるには、合成電流クリップのうちPI起因分とFF起因分を切り分ける必要があり、
    back-calc gainはチューニング対象になる。実機ログでの検証手段がない状態での投機的な
    書き換えはsettling悪化のリスクがあるため見送った。
  - **P0.1 連続unwrap角**: ファームの`unit_controller_set_target`/`shortest_angle_error`と
    `unit_web_ui.py`の`effective_steer_mdeg`/`profile_steer_step`/`shortest_diff_mdeg`/
    STATUS1 angleテレメトリまで、[0,360)ラップ前提の実装が~15箇所以上に渡って絡んでいる。
    flip判断・pre-steerの土台として重要だが、現在の90deg単発試験の収束時間には直接効かず、
    ブラストレイダスが大きいため見送った。
  - **wheel=0 pre-steer状態遷移**: 連続unwrap角に依存するため連動して見送り。

## 計画追加(2026-07-31 ステア応答高速化・wheel=0操舵)

- `docs/control/CENTRAL_COORDINATED_CONTROL.md`へ、速度mode単体同定、加速/制動FF同定、
  time scale段階縮小、steer速度/加速度包絡拡張、接地3輪回帰の実装・試験順を追加した。
- wheel=0でもsteer角を独立制御する契約を明記した。現ファームではすでにwheel=0の
  正逆90deg操舵が成立しているため、中央側で停止角保持、明示pre-steer、ETA算入、
  ゼロ速度付近の角度ヒステリシスを実装する。
- 主要運用「指定poseへ到着→タスク→別poseへ移動」に対し、中央状態を
  `ARRIVE_SETTLED→TASK_HOLD→PRESTEER→DEPART`とする。タスク側の許可がある場合だけ
  wheel=0で先行操舵し、低速応答は`Tsettle/Tfeasible`で理論限界への接近を評価する。
- 固定40 steer軸rpmは恒久上限にせずcommissioning guardへ格下げする。本番通常上限は
  `margin*469 - abs(wheelProfile)/(32/11)`へsteer比`8/11`を掛けた連続planned包絡とし、
  ユニット側は469rpm hard包絡を最終保護として再計算する。初期marginは0.90。
- 現コードの改善項目として、0～360deg正規化/shortest errorを連続unwrap目標へ変更、
  時刻付き`theta/thetaDot/thetaDDot`の1kHz局所補間、二重ramp解消、mode要求のhard包絡射影、
  combined scaling後のback-calculation anti-windup、motor速度+AMT角observerをP0/P1に追加した。
- 速度loop同定後は実測慣性FFとbounded DOBを追加し、残留mode干渉があれば両mode PRBSから
  2x2 decoupling FFを同定する。単ユニット局所MPCより、この2自由度servoを先に完成させる。
- 駆動中央バスはTeensy CAN3-G474 FDCAN1のCAN FD nominal 1Mbps/data 2Mbps+BRSへ更新する。
  32byte `TRAJECTORY_FD`を200〜250Hzで受信し、3輪共通commit後にG474が1kHz補間する。
  48byte状態を200Hzで返信し、実ハーネスbus load 50%以下を合格目標とする。
- G474 `fdcan.c`は中央バスだけFDOE/BRSE、data 2Mbps、最大64byte message RAM/DLCへ拡張し、
  FDCAN2-C620は既存Classic 1Mbps/8byteを維持する。
- 次は`unit_steer_mode_id.py`で現行Kp=120/Ki=50/LPF=2msのwheel=0基準step/PRBSを取り、
  純操舵中のwheel非干渉も同時に確認する。実測ログはまだない。

## セーブポイント(2026-07-31 リアルタイムベクトルGUI・次工程確定)

- `unit_web_ui.py`のベクトルパッドをEnable中約30Hzのリアルタイム送信へ変更。
  矢印/Shift微調整/ドラッグ/Escゼロを実装し、pointer clickの重複送信経路を除去した。
- Enable時はAMT実角度を目標へseedし、wheel目標/実効値を0へ初期化する。Disable中のdraftは
  モータを動かさず、以前のwheel指令もEnable直後に再開しない。
- 実機30Hz相当でwheel=100rpm、steer=59.854→69.854degを連続指令し、
  最終70.049deg/104.2rpm、`MOTION_SETTLED=1`を確認。STOP後wheel 0rpmを確認した。
- 構文/セルフチェック/JavaScript構文/差分チェックは合格。Web UIはport 8080で稼働中。
  保存時点は実wheel/実効wheel=0rpmだがUnit Enable=true。終了時はSTOP/Disableを行う。
- 次工程はAMT機械ゼロ校正を先に実施し、その後に固定治具・ガード付きの代表荷重試験を行う。
  0/90/180/270deg検証後、75/265/1200rpm、正逆90deg、急反転、連続8の字を評価する。

## 完了(2026-07-31 理論時間x2軌道・STATUS3収束判定)

- `unit_web_ui.py`へhard 469rpm/planned 422.1rpm(10%予備)の2包絡、非対称台形/三角形
  `Tmin`、time scale=2を実装。steer速度1/2・加速度1/4、wheel ramp 1/2で目標生成する。
- G474はSTATUS1/3を20ms、STATUS2を50msで通常送信する。idx22=1〜100msはSTATUS1/2の
  ベンチoverride、0は通常周期復帰。STATUS2からGUIが実steer軸rpmを算出する。
- STATUS3 bit6 `MOTION_SETTLED`を実装。角度誤差<=0.5deg、実steer軸<=1rpm、steer FF<=0.1rpm、
  wheel誤差<=max(12rpm,6%)、wheel加速度FF<=1rpm/sを100ms連続で満たしたときだけ立つ。
  前指令のHigh誤認を避けるため、受信側は新指令後のLow→Highを完了として使う。
- `SET_TARGET_FF`のwheel加速度欄へWebプロファイルの実微分を送信し、純wheelランプ中も
  `MOTION_SETTLED`がLowになることを0→265rpm実機試験で確認した。
- 起動時既定を現最良値へ更新: steer Kp/Ki=120/50、mode LPF=2ms、angle hold/moving Kp=4/1、
  deadband=0.3deg、steer accel/decel FF=0.5/0.5。build成功(FLASH 10716B/RAM 1352B)、
  ST-Link connect-under-resetでFlash/verify済み。
- 最終受入`firmware/logs/auto-tune/2026-07-30T17-50-43Z/`: wheel=0/265rpm x 正逆90deg x3、
  time scale=2で12/12 CAN収束・12/12 deadline 1.273s以内、平均1.146s、中央値1.130s、
  最悪1.250s、最大overshoot 1.054deg。
- GUIへ理論時間/期限/収束flag表示と2D速度ベクトルパッドを追加。矢印キー/ドラッグで先端を動かすと、
  Enable中は約30Hzで方向=steer角、長さ=wheel rpmをリアルタイム送信する。Disable中はdraftのみ、
  Enable時は実角度+wheel 0から開始する。最大長はplanned pure-wheel上限1228rpm。
- 実機30Hz相当の連続指令をwheel=100rpm、steer=59.854→69.854degで確認。
  最終70.049deg/104.2rpmで`MOTION_SETTLED=1`、STOP後はDisable・wheel 0rpmへ復帰した。
- wheel=1200rpm定常でplanned steer上限6.98軸rpm、time scale=2後の指令3.49軸rpmを実測確認。
  wheel profile rpmを使って200Hzでsteer上限を再計算するため、wheel増加時は包絡に沿って減少する。

### 現在の状態

- 最新ファームFlash済み。Web UI起動中、ユニットはDisable。本番同様にwheel rpm+指定角度で指令可能。
- time scale=2は空走受入合格。倍率1のゲイン限界回帰は収束11/12、2*Tmin期限内7/12で、
  wheel回転中の終端摩擦が残る。

### 次の作業

1. 接地/荷重/床材で12試行以上を取り、0.35s残差予算をp99で更新する。
2. Teensyへ3輪共通time scaling、10% planned包絡、全STATUS3収束集約を移植する。
3. 終端静止摩擦へDOB/推定型補償を検討し、gain-only限界を超える。

## 完了(2026-07-31 ステア理論速度への接近・校正フレーム拡張)

- `unit_auto_tuner.py`を粗→細の実機pattern searchとして拡張し、Kp/Ki/angle P/deadband、
  mode速度LPF、電流上限、加速度FF、最大速度、ステア加速/制動を統一的に探索可能にした。
  各trial/summaryへ運動学的下限比、指令/実測電流peakを追加し、CSV/SVG/metadataを逐次保存する。
- Web目標生成を50Hzから200Hzへ上げ、`SET_TARGET_FF`は0を含め毎周期送信するよう修正した。
  最終zeroを省略したときの200ms FF残留を解消した。
- ステア加速と制動を別パラメータに分離した。最大速度へは3600deg/s^2で立ち上げ、
  `sqrt(2*a_decel*distance)`の制動側は2250deg/s^2として早めに減速を開始する。
- 空走自動探索の採用値:
  - steer mode Kp/Ki=`80/25`, angle Kp=`4`, deadband=`0.5deg`
  - mode速度LPF tau=`10ms`, acceleration FF gain=`0.75`
  - 最大`240deg/s`, 加速`3600deg/s^2`, 制動`2250deg/s^2`, current limit=`4000 raw`
- 電流上限3000/4000/5000/6000 rawを比較したが、最大指令電流は約2,000rawで上限に届かず、
  上限増加による高速化はなかった。律速要因は20ms速度LPFの位相遅れと対称制動プロファイルだった。
- 最終値をbuild/flash/verifyし、wheel=0/265rpm x 正逆90deg x 3反復を回帰:
  **12/12成功、平均収束0.760s、最悪0.924s、平均理論比2.03、最大overshoot 2.64deg、
  指令/実測電流peak 2057/1665raw、温度peak 30degC**。旧採用平均1.185sから約36%短縮。
- `docs/testing/UNIT_AUTO_TUNER.md`へ、内周速度PI→外周angle P→FF/プロファイル→
  負荷/床材シナリオの順で行うパッケージ校正手順を追記した。
- その後、巡航中に移動目標を2〜6deg追い越した際、hold用angle Kp=4が速度指令を
  40rpmから約28〜35rpmへ一度落として戻す「中間カクつき」をログで確認した。
  moving angle Kpを別パラメータにした2自由度外周を実装し、FF>=5rpmではKp=1、
  減速終盤にKp=4へ連続補間するよう変更。ユーザー目視でもカクつきと収束が改善した。
- 加速FF=0.75と制動FF=1.0を分離してflash済み。加速/制動を同一係数にせず、慣性加速と
  ブレーキを独立校正できる。
- 最大速度上限を試験時だけ40→60軸rpmへ広げ、240/300/360deg/sを比較したが、平均収束は
  0.838/0.884/0.904s、overshootは3.95/6.59/8.44degで240が最良。360deg/sで制動率を
  1350まで早めても平均0.879sで、rpm/電流包絡線ではなく内周速度帯域が律速と判断した。
  採用上限は40軸rpm=240deg/sへ戻した。
- 終端摩擦対策のsteer_min_rpm=2.5/5とsteer Coulomb FF=200/400rawはいずれも未収束数を
  増やしたため不採用(両方0)。一定floor/FFではなく、次は内周単独同定とDOB/摩擦推定で扱う。
- 2自由度化後は12/12・平均0.833s・最悪0.964sのバッチがある一方、別の冷間開始バッチでは
  最初のwheel=0移動が0.527deg残り11/12、worst 2.37sとなった。定常応答は主に0.68〜0.92s
  だが、積分0からの初回と絶対角依存の再現性は未解決。ログは
  `firmware/logs/auto-tune/2026-07-30T17-01-13Z/`ほかに保存済み。

### 現在の状態

- 最新ファームをFlash済み。Web UIは200Hz版で起動中、ユニットはDisable。
- 空走採用値はコード、Web UI、自動調整器の既定値で一致している。

### 次の作業

1. **次セッション最優先:** 自動調整器/ファームへ外周を切ったステアmode速度step/PRBS同定
   モードを追加する。10ms LPF+PIを基準に、5ms以下のLPFでKp/Kiを再同定し、内周帯域を上げる。
2. 接地後は空走値を中心に狭幅探索し、荷重/床材を跨ぐ最悪応答で共通ゲインを選ぶ。
3. Teensy中央プロファイルへ200Hzベンチで検証した非対称ステア加速/制動を移植する。

## 完了(2026-07-31 低抵抗化後の操舵高速収束・包絡線・安全減速)

- 機構抵抗低下後の発振を進行中WebUIログから切り分けた。wheel=265rpm定常自体は
  p-p約6rpmで安定していたが、操舵を240deg/sで動かした区間は到着時にFFが40rpmから
  0へ瞬時に落ち、実角が目標を約16〜19deg通過して逆向き補正する往復挙動だった。
- `tools/linux/unit_web_ui.py`のステア目標生成を、定速スルーから加速度制限付き台形/三角形
  プロファイルへ変更した。残距離から`sqrt(2*a*distance)`で制動開始速度を求め、
  `SET_TARGET_FF`を到着前に連続的に0へ落とす。短時間に目的角が変わって停止距離が不足する
  場合もFFを不連続に切らず、小さなプロファイルオーバーシュート後に滑らかに戻す。
- ステア加減速を実機A/B:
  - 60deg/s・180deg/s^2・wheel=0の+90deg: 到着オーバーシュート約0.18deg、発振なし。
  - 要求240deg/s・360deg/s^2・wheel=265rpmの+90deg: 短距離のため実ピーク約180deg/s、
    到着後約0.35deg以内。旧方式の16〜19deg往復を解消。
  - 720deg/s^2: 90deg目標プロファイル約0.7s、最大追従誤差約3.2deg、到着直後の振れ
    約+2.5/-1.1deg後に±0.3deg以内へ収束。速度と減衰の両立が最良のため既定値に採用。
  - 1080deg/s^2: 目標約0.60sだが到着後に約±2.2deg往復したため不採用。
- ギア比`DRIVE=32/11`, `STEER=8/11`から単一モジュールのrpm包絡線をWebUI目標生成へ接続した。
  従来は超過警告の表示だけだったが、現在はwheel目標を保つ範囲へsteerプロファイル速度を
  自動制限する。wheel=1300rpm・steer要求240deg/sでは数式どおり96.5deg/sへ制限され、
  実wheel 1302〜1310rpm、+90deg到達後誤差0.44deg以内、温度32degCで完走した。
- 高rpm急停止の回生電圧上昇対策として、WebUI中央側へwheelの非対称ランプを追加した。
  既定は加速1000rpm/s、減速500rpm/s。正逆反転は必ず0rpmを1サンプル経由し、通常STOPは
  `現在のprofile rpm/減速率+0.5s`待ってからdisableする。ファーム内部の4000rpm/sランプは
  最終安全ガードとして残る。500rpm実機試験ではSTOP待ち1.51s、disable時実測0.015rpm。
- 低抵抗化後のdrive積分フロアA/Bを途中まで実施。25rpmはfloor=200でmean 26.3rpm/
  p-p 48.2rpm/固着22.5%、floor=0でmean 25.0rpm/p-p 45.7rpm/固着25.0%となり、旧floorだけ
  では新機構の25rpm固着を解消できない。40rpm floor=200はmean45.7rpm/p-p14.3rpm/固着0%。
  40rpm floor=0は試験中断で未取得。終了後floor=200へ復帰した。
- `python3 tools/linux/unit_web_ui.py --check`、`py_compile`、`git diff --check`はPASS。
  `bash firmware/scripts/build.sh debug`成功(FLASH 8896B / RAM 1280B)。制御ファームの実動作変更は
  今回なく、実機Flashは行っていない。WebUIは改良版で起動中、ユニットはDisable状態。

### 現在の状態

- ユニット局所ループは既存どおり1kHz。中央の主指令は`omega_w, theta_s`で、軌道から得た
  steer rate/wheel accelをFFとして併送する構成。
- ステア90degの現採用プロファイルは最大240deg/s、加減速720deg/s^2。
- wheel中央プロファイルは加速1000rpm/s、減速500rpm/s。高rpm停止の急変は禁止。
- runtimeのdrive積分フロアは安全のため既定200rawへ戻している。

### 次の作業

1. wheelランプ有効状態で40rpm floor=0を再取得し、25/40rpmのfloor採否を確定する。
2. 今回WebUIで検証したステア制動プロファイル、rpm包絡線、非対称wheelランプをTeensyの
   100Hz協調制御へ移植する。3輪では1輪だけを削らず、最悪モジュールに合わせて全体をデサチュレートする。
3. `LOAD_ADAPTIVE_CONTROL_ROADMAP.md` Level 0に従い、mode積分値とC620 torque currentを
   テレメトリへ追加し、低速固着と機構抵抗変化をログで分離する。
4. `targetWheelAccelRpmMilliPerS`をdrive加速度FFへ接続する前に、加速/減速方向別の係数を同定する。
5. DCバス電圧を計測可能にし、高rpm減速時の電圧ピークから安全な減速率500rpm/sを再評価する。

## 完了(2026-07-08 WebUI ωsセマンティクス変更: 収束速度+到達キープ)

- ユーザー要望「ωsを指定すると指定角度までの収束速度が変わり、到達したらその角度でキープ」
  に合わせてWebUIの送信ロジックを変更(軌道整形は送信側の責務、というアーキテクチャどおり
  ファームは無変更):
  - θs=目的角、ωs=接近速度(0〜240°/s、0=即ステップ=従来挙動)。
  - 実効目標を目的角へ最短経路でωs °/sずつスルーし、移動中のみSET_TARGET_FFを送信。
    到達で実効目標を目的角に固定しFF=0(角度Pループがそのままキープ)。
  - ターゲットリーシュ(実測+45°制限)は移動中も併用。
- 実機検証: +90°をωs=30°/sで指定、約3秒の等速接近(FF=5rpm)→到達→FF=0で
  324.7°キープ(誤差0.5°以内)、wheel200rpm維持。
- バグ修正2件: /api/setでθsとωsを同時送信するとωs適用前に即スナップする処理順の問題、
  旧サーバプロセスがポート8080を握り旧コードが応答し続ける問題(fuserでkillして解消)。

## 完了(2026-07-08 rpm包絡線逸脱でのSTOP対策+C620途絶診断)

- ユーザー報告「ホイール・ステアrpmが関数(トレードオフ)になっていて逸脱すると落ちる」を確認。
  原因: 2モーターが速度予算`motor_max_rpm=469`を共有し
  `|ωs/6/(8/11)| + |ωw/(32/11)| <= 469`(+ステア軸クランプ240°/s)の包絡線がある。
  超過ωs指定時、UIが目標角を開ループで前進し続け、実角が追従できず
  `STOP: angle diverged err=121〜142°`(120°ガード)でラッチ停止していた。
- 対策(unit_web_ui.py):
  1. **ターゲットリーシュ**: 目標角の先行を実測角+45°までに制限(テレメトリ0.5s以内の
     ときのみ適用)。物理が追いつけない間は目標も待つため120°ガードに到達しない。
  2. **包絡線ライブ表示**: 現在ωwで出せるωs上限/現在ωsで出せるωw上限をstatusへ追加、
     UIで超過時赤字。
- 実機検証: wheel=1300rpm+ωs=120°/s(従来は数秒でdiverged死)で連続回頭、
  誤差max1.2°、wheel1282〜1316rpm維持、発散STOPなし。
- **副次対応: C620フィードバック途絶の診断**。試験中にモーター24V電源が落ち、
  enableが無反応(START条件`feedback_is_fresh`不成立)になる事象が発生。
  ファームの`idle`行へ`fdbkOk/en/tgtOk`を追加し(flash済み)、UIに
  「C620 feedback: NG(24V電源off?)」表示を新設。電源再投入で復帰確認。

## 完了(2026-07-08 試験用ブラウザUI `tools/linux/unit_web_ui.py`)

- θs/ωw/ωsスライダー+Enable/STOP/Disable+ライブ数値表示の単一ファイルWebUI
  (Python標準ライブラリ+pyserial、既定 http://localhost:8080)。ファームプロトコルは
  既存のSET_TARGET/SET_TARGET_FF/UNIT_CTRLのみ使用。
- 安全設計(すべて実機検証済み):
  - Enable時にステア目標を現在角へ自動シードし、**enable送信前にシード済みSET_TARGETを
    1発送信**(ファームはSTART時に最後に受信した目標をラッチするため、これを怠ると
    古い目標で発散ガードが即発火する。実際に初回試験でtarget=0のままSTART→即STOPを踏んだ)。
  - STOPはωw=0/ωs=0で1秒減速後にdisable(空走カップリング対策)。
  - デッドマン: ブラウザ操作/ポーリングが3秒途絶で自動STOP(実測5秒放置→自動停止確認)。
    enable/set等のPOSTもハートビートとして扱う(enable直後の誤発火を修正済み)。
  - Ctrl-C/例外/atexitで必ずdisable。
- **ファーム変更**: disabled中も500ms周期で`idle angle=<mdeg> amtOk=<0|1>`を出力
  (`IDLE_REPORT_PERIOD_MS`)。UIがenable前に現在角を知るために必須(`run=`行はactive中のみ)。
  flash済み。
- UI側バグ修正: `SET_TARGET_RX`等のangleを含まないVCP行がテレメトリを置き換えて
  現在角が消える問題を、angleを含む行のみ採用する形で修正。
- 実機検証: enable(シード121.99°)→ωs=30°/s+ωw=100rpmで追従誤差0.4°以内・
  wheel実測97〜103rpm→STOP正常。デッドマン自動停止も確認。

## 完了(2026-07-08 STEER_RATIO訂正とSET_TARGET_FF実機検証)

- **運動学定数の重大バグを発見・修正**: FF初回試験で「FFあり」が-7.5°先行する矛盾から追跡。
  wheel=0でも再現し、AMT実測軸速度がモーター実測からの運動学逆算値のちょうど4.00倍だった。
  ユーザー確認によりギア列は各モーター40:55:60:15で、**60:15段は差動後のドライブ経路のみ**。
  ステア経路は40/55のみなのに、docs/firmwareは15/60を含めた`0.0909(n1+n2)`(=1/4)に
  なっていた。`STEER_RATIO`を2/11→**8/11**へ修正(`docs/control/KINEMATICS_AND_RPM.md`も
  訂正注記付きで修正済み。実測0.3623 vs 理論0.3636、0.4%一致)。
- これまでのステア調整は外側角度Pループが4倍誤りを吸収していたため成立していた
  (実効angle_kp・実効上限が公称の4倍)。挙動維持のため外側パラメータを4倍リスケール:
  angle_kp 0.5→2.0、steer_max_rpm 10→40(真の軸rpm、=240°/s)、steer_accel 150→600。
  SET_CONFIGクランプもsteer_max_rpm≤60、steer_accel≤2000へ拡大。
  修正後のFFなし30°/s回頭で定常遅れ+2.76°(修正前+2.77°)と挙動維持を確認。
- **SET_TARGET_FF実機検証(比修正後)**:
  - 30°/s回頭+wheel300: FFなし定常遅れ+2.76° → **FFあり mean -0.03°、max 0.93°**
  - 90°/s回頭+wheel300: **mean +0.24°、max 0.93°**、wheel維持p-p 6.6rpm、安全停止なし
  - `unit_bench.py run --steer-rate-dps R`でθs・ωs・ωwの3指令駆動が成立。
- 注意: ドライブ比2.909はモーター間整合のみで**ホイール物理回転数は未検証**
  (外部計測が必要)。ギア列上は40/55×60/15=32/11で整合するため正しい見込みだが、
  実測機会があれば確認すること。

## 完了(2026-07-08 SET_TARGET_FF実装: ステア角速度FF)

- `docs/communication/COMMUNICATION_NAMING_AND_IDS.md`(SET_TARGET_FF payload)
  と`docs/control/CENTRAL_COORDINATED_CONTROL.md`(通信への追加)の仕様どおり、
  CAN ID `0x110+unitId`(unitId=1につき`0x111`)、8バイトint32 LE
  `targetSteerRateMdegPerS` + `targetWheelAccelRpmMilliPerS`を受信する処理を追加。
- `firmware/include/control/unit_controller.h` / `firmware/src/control/unit_controller.c`:
  `unit_target_t`に`steer_rate_ff_rpm`を追加し、専用setter
  `unit_controller_set_steer_rate_ff_rpm()`を新設(`unit_controller_set_target()`とは
  独立。CAN側のタイムアウトでFFだけ0へ戻せるようにするため)。
  `unit_controller_update()`内でFF注入位置は「角度P項(deadband適用後)へFFを加算し、
  その和へsteer_min_rpm floor→steer_max_rpm clampを適用」(既存のsteer_accelランプは
  そのまま和の後段に残置)。FF=0なら旧コードパスとビット単位で同一の計算式になる。
- `firmware/src/main.c`: `CAN_ID_SET_TARGET_FF_BASE=0x110`受信を追加。
  mdeg/s→rpmは`/6000`(mdeg→deg`/1000`、deg/s→rpm`/6`)。`last_ff_ms`を記録し、
  `TARGET_FF_TIMEOUT_MS=200`(仕様どおり)を過ぎたら制御ループで毎サイクルFF=0を
  setterへ渡すフォールバックを実装(`ff_is_fresh()`)。受信ログ`SET_TARGET_FF_RX`は
  既存の`SET_TARGET_RX`と同じ500ms間引きを踏襲。wheel加速度FFは現時点では
  パース・ログのみで制御へは未接続(将来用、`can_wheel_accel_ff_rpm_milli_per_s`)。
  周期テレメトリ(`run=`行)へ適用中のsteer FF rpmを`ffS=`として追加。
- `tools/linux/unit_bench.py`: `send_set_target_ff()`(ID`0x111`)を追加。
  `run`サブコマンドへ`--steer-rate-dps`(既定0)を追加。非0のとき、毎周期
  SET_TARGET_FFをSET_TARGETの直前に送り、同時にツール側のsteer目標もrate*dtで
  進める(360000mdegでラップ。中央協調制御の連続unwrap契約とは別物とコメントで明記)。
  `profile`サブコマンドのCSVへ省略可能な4列目`steer_rate_mdeg_s`を追加(値がある行のみ
  FF送信)。`python3 -m py_compile`と各`--help`はPASS、can0への実送信は未実施。
- ビルド確認: `bash firmware/scripts/build.sh debug`成功。FLASH 8664B(1.65%)、
  RAM 1280B(1.30%)。警告なし。**実機flash/書き込み・駆動は今回未実施**(指示により
  ビルド・構文チェックまでに限定)。

次:
1. 実機での単体FF追従評価(段階1、`CENTRAL_COORDINATED_CONTROL.md`の段階導入表参照):
   `unit_bench.py run --steer-rate-dps <R>`でランプ・ステア速度追従を確認。
2. `steer_min_rpm`floorがFF単独(角度誤差小・FF一定)のケースでどう効くか実機評価
   (deadband導入後の設計候補として`CENTRAL_COORDINATED_CONTROL.md`に記載あり)。
3. wheel加速度FFを実際の駆動側制御へ接続するかどうかの検討(現状は受信のみ)。

## 完了(2026-07-08 current_limit引き上げ: 応答性第3弾)

- ユーザー承認のもとSET_CONFIGのcurrent_limitクランプを2000→6000へ、
  wheel_accelクランプを2000→5000へ拡大(要ファーム変更のため)。
- 切り分け: cl=3000/4000にしてもaccel=2000のままでは立上り不変(電流需要~2300止まり、
  律速はランプ)。accel=4000で電流余裕が活き、立上り0.50→0.41s。
- drive Kp=30: オーバーシュート4.2%、定常p-p 5.7。**25rpm低速はさらに改善**
  (mean 27.2、p-p 7.1、固着0)。電流ピーク3737、温度29°C。
- 総合(±500反転プロファイル): **反転0.51〜0.52s**(当初5.2sの10倍)、操舵1.14°以内、
  飽和スケーリングなし、温度29°C、安全停止なし。
- **焼き込みflash/verify済み**: current_limit=4000、wheel_accel=4000、drive Kp=30
  (+steer 10rpm/150、floor200、クランプ400、threshold5)。
- 注意: 4000 raw≈4.9A(M3508定格10A連続に対し余裕)。接地・負荷時は電流・温度を
  再評価すること。無負荷での応答性詰めはここで完了とする。

## 完了(2026-07-08 応答性第2弾: PI帯域とステア速度の引き上げ)

- accel=2000時の電流ピークは1442/2000で飽和しておらず、律速はdrive Kp=10のPI帯域と特定。
- drive Kp 15/20をA/B: Kp=20で0→500rpm立上り0.50s、オーバーシュート5.7%
  (Kpを上げるほどランプ遅れ→積分蓄積が減りオーバーシュートも減少)。電流は瞬間2000タッチ
  (比例スケーリング1サンプルのみ)。
- 25rpm退行チェック: Kp=20でmean 26.9(バイアス+7.6%に改善)、p-p 12.6、固着0。
- ステア: steer_max_rpm 5→10、steer_accel 50→150で90°ステップが0.5°以内まで0.72〜0.91s
  (従来1.2〜1.6s)。wheel300rpm維持は±4rpm。
- 総合確認: ±500rpm完全反転0.71s(当初5.2s、7倍改善)、操舵保持0.70°、安全停止なし。
- **採用値を`main.c`へ焼き込みflash/verify済み**: wheel_accel=2000、driveKp=20、
  steer_max_rpm=10、steer_accel=150(+前回のfloor200/クランプ400/threshold5)。
- 注意: これ以上の立上り短縮はcurrent_limit=2000(ユーザー承認事項)の引き上げが必要。
  無負荷ではここまでで十分と判断。

## 完了(2026-07-08 応答性改善: wheel_accel_rpm_per_s調整)

- ユーザー指摘「応答性が悪い」の主因は制御ゲインではなく`wheel_accel_rpm_per_s=200`
  (未実測の仮値)のランプ律速だった。SET_CONFIG idx10で500/1000/2000をA/B:
  - 500: 0→500rpm立上り1.11s、試験中角度誤差max 0.97°
  - 1000: 0.71s、0.44°
  - 2000: 0.61s、0.79°(伸び僅少)
- **1000を採用し`main.c`既定値へ焼き込み・flash済み。** ±500rpm完全反転は5.2s→1.2〜1.3s、
  操舵保持1.32°以内、安全停止なし(`firmware/logs/profile-reversal-fast.log`)。
- **新発見: disable時の空走カップリング。** 高速回転中にdisableすると、ホイール慣性の
  コーストダウンが差動機構経由でステア軸を最大43°回す(accel試験のrun間で実測)。
  実運用の停止シーケンスは「wheel目標→0で減速完了後にdisable」とすること
  (プロファイルCSVの最後にwheel=0行を入れる)。将来はファーム側の減速停止
  (disable受信時にランプで0へ)も検討。
- 残課題: ステップ時のオーバーシュート~15%(ランプ後のPI追いつき)。必要なら
  drive Ki/Kpの位相を詰めるが、接地後に再評価が先。

## 完了(2026-07-08 連続軌道プロファイル評価)

- `unit_bench.py profile`で53秒のCSV軌道を実行(`firmware/logs/profile-reversal-v1.{csv,log}`)。
  内容: ±500rpm反転x2、75→-75低速反転、25rpm保持、ステア±90°ステップ+wheel300rpm同時、停止。
- 結果: 安全停止なしで完走。
  - ±500rpm反転: ゼロクロスのストール最大0.3秒、定常±512rpm(+2.4%バイアス)、p-p 22〜24。
  - 75→-75反転: ストール0秒(スティック域を無停止で通過)。25rpm保持も固着なし(mean 33.7、+35%バイアス)。
  - ステア±90°ステップ(wheel 300rpm維持中): |err|<2°まで約1秒、<0.5°まで1.2〜1.6秒。wheel速度は維持。
- 残る軽微な課題: 積分フロア由来の過速バイアス(低速ほど相対比大: 25rpmで+35%、500rpmで+2.4%)。
  CAN経由の目標値側で補正するか、接地後に再評価。

注意: CAN版ファームの角度発散ガードは120°(`ANGLE_DIVERGENCE_STOP_DEG_MILLI=120000`)。
90°ステップは通るが、それ以上の目標ジャンプはCSV側でスルーレート制限すること。

## 完了(2026-07-07 低速stick-slip対策: SET_CONFIG+積分フロア)

- CAN `SET_CONFIG`(0x141)でランタイムパラメータ変更を実装・実機確認(reflash不要で調整可能に)。
  併せて動摩擦FF(idx14)・積分フロア(idx15)・動作判定しきい値(idx16)を追加(既定0=無効)。
- Linux評価ツール`tools/linux/unit_bench.py`を新規作成(socketcan直、必ずdisable送信)。
  `st-info --probe`→`flash.sh debug`でこのLinux機からの書き込みも初成功。
- 動摩擦電流を定常iDrive法で同定: **約200 raw(185〜215)、速度依存なし、正逆対称**。
  ブレークアウェイ~850との差がstick-slipキックの定量的原因と確定。
- A/B試験の結論: **積分フロア=200+driveKp=10**で、40rpmはp-p 213→19.6・固着66%→0%、
  25rpmも固着0%で連続回転化。150rpmは無退行(mean 150.0)。FF併用は過速NG。
  詳細は`firmware/docs/CONTROL_LOOP_TUNING.md`の同日セクション。

現在の状態(2026-07-08更新):
- **採用値をすべて`main.c`既定値へ焼き込みflash済み**: driveKp=10、積分フロア=200、
  動作しきい値=5、動作開始時積分クランプ=400(idx17、2026-07-08追加実装)。
- クランプ400で25rpm 3回連続固着ゼロ(p-p 17〜47、ばらつきは機構の角度依存の
  引っかかり由来)。40rpmはp-p 16。ユーザー所感とも一致:「機構上改善はできない
  引っかかりがあり、それがオーバーシュートの原因」— 制御側はfloor+クランプで
  通過トルク確保と過剰キック抑制まで対応済み。

次の作業:
1. 接地・負荷ありでの摩擦再同定とフロア/クランプ値の見直し(負荷下では引っかかりの
   相対影響は縮む見込み)。
2. 恒久対策が必要なら角度インデックス摩擦マップ(CALフェーズ、
   `docs/control/CALIBRATION_AND_ADAPTATION_PLAN.md`)。
3. 中央Teensy/mini PCからの連続軌道(`unit_bench.py profile`)での評価。

## 完了(2026-07-07 mini PC LinuxからのCANable smoke test)

## 完了(2026-07-07 mini PC LinuxからのCANable smoke test)

- `docs/testing/MINIPC_LINUX_HANDOFF.md`に従い、mini PC(Ubuntu 22.04)側の評価環境を構築。
  - `python3-serial`追加導入(can-utils/dialoutは既存Linux環境整備で導入済み)。
  - USBデバイス判別に注意: `/dev/ttyACM0`は**ST-Link V3のVCPパススルー**(ユニットのdebug UARTログが
    ここに出る)、`/dev/ttyACM1`が実際の**CANable2**(slcan)。ハンドオフメモの`ttyACM0`前提は
    このPC構成では逆だったため、`slcand -o -c -s8 /dev/ttyACM1 can0`で接続した。
  - `sudo ip link set can0 up`後、`ip -details link show can0`で`UP`/`ERROR-ACTIVE`確認
    (`bitrate 0`表示はslcanインターフェース仕様上の既知表示で異常ではない)。
- ホイールを浮かせた状態でメモ記載の単発smoke(`SET_TARGET`1回→`enable=1`→3秒→`enable=0`)を実施し、
  `candump`と`/dev/ttyACM0`(VCP)を同時キャプチャして正常動作を確認:
  - `SET_TARGET_RX steer=90000 wheel=500000`受信、`START_CAN`後angleが90000mdeg付近(err±2000)へ収束、
    wheelがランプ増加。
  - 単発送信のため周期`SET_TARGET`が止まり、想定どおり`STOP: target timeout`→`UNIT_CTRL enable=0`で安全停止。
- ログ保存: `firmware/logs/linux-minipc-smoke-vcp-2026-07-07T23-29-46.log`、
  `firmware/logs/linux-minipc-smoke-candump-2026-07-07T23-29-46.log`。

次: mini PC側で周期送信スクリプト(メモのCodex prompt例、20〜50Hzで`SET_TARGET`を送り続けるPython実装)を
作成し、単発smokeではなく実際の連続駆動評価に進む。

## 進行中(2026-07-07 CANable手入力consoleの落ち挙動切り分け)

- CANable手入力consoleで、周期的に「落ちる」ように見える挙動が発生。
- 現ファームには電流増加率しきい値で停止する処理はないため、主候補は`STOP: target timeout`。
  PowerShellのキー入力/表示処理で`SET_TARGET`周期が一瞬200msを超え、停止→再STARTしている可能性が高い。
- 対策コードは実装・ビルド済み:
  - `TARGET_TIMEOUT_MS`を200ms→1000msへ変更。
  - `STOP: target timeout`時に`unit_enabled=false`へラッチし、通信断でSTOP/STARTを繰り返さないように変更。
- ただしflashは`invoke-hardware-session.ps1`が`busy`を返したため未反映。
  おそらく手元のconsole sessionがmutexを保持中。ユーザーがconsoleで`q`を押して終了後、再flashが必要。
- wheel rpmが1300rpm以上に見える件:
  - ファーム内の理論上限は`motor_max_rpm=469 * 32/11 = 約1364 wheel-rpm`なので、1300台自体は異常ではない。
  - ただし運用上1200rpmまでにしたいため、console側に`MaxAbsWheelRpmMilli`を追加し、既定を±1200rpmへ制限。
  - `run-canable-target-console-session.ps1`からも同パラメータを渡せるようにした。
- PowerShell構文チェック:
  - `run-canable-target-console.ps1`: OK
  - `run-canable-target-console-session.ps1`: OK

現在の状態:

- 実機flash上は、まだtimeout 200ms版の可能性が高い。
- ワークツリー上のfirmwareはtimeout 1000ms + timeout停止ラッチ版。
- consoleスクリプトは±1200rpm上限版。

次:

1. 手元consoleで`q`を押して終了し、mutexを解放。
2. `.\firmware\scripts\flash.ps1`でtimeout修正版をflash。
3. consoleを再起動し、VCPログの`STOP:`行で落ち原因を確認。

## 完了(2026-07-07 CANable手入力コンソール追加)

- CANableから手入力で`θs`/`ωw`を変えられる操作スクリプトを追加。
  - `firmware/scripts/run-canable-target-console.ps1`
  - `firmware/scripts/run-canable-target-console-session.ps1`
- 操作は`invoke-hardware-session.ps1`経由のsession版を使う前提。操作中はmutexを保持し、
  終了時はconsole側finallyとSafeIdle側の両方で`UNIT_CTRL disable`を送る。
- キー操作:
  - `e`: enable
  - `d`: disable
  - `q`: quit
  - 上下矢印: wheel rpmをstep増減(既定25rpm)
  - 左右矢印: steer角をstep増減(既定5°)
  - `z`/`x`: steer角を-90°/+90°
  - `0`: wheel=0
  - `h`: status表示
- `SET_TARGET`は既定50ms周期(20Hz)で常時送信。起動直後はdisableを送ってから待機。
- PowerShell構文チェック成功。対話操作はユーザーのコンソール入力が必要なため、ここでは未実行。

次: 実機で以下を使って手入力確認。

```powershell
.\firmware\scripts\run-canable-target-console-session.ps1 -CanPort COM16 -InitialSteerMdeg 179912 -InitialWheelRpmMilli 0
```

## 完了(2026-07-07 CANable経由SET_TARGET実動作確認)

- `firmware/src/main.c`を中央CAN(FDCAN1)の実指令で動くベンチアプリへ変更。
  - `SET_TARGET` ID `0x101`: int32 little-endian `steer_mdeg` + int32 little-endian `wheel_rpm_milli`
  - `UNIT_CTRL` ID `0x121`: `01 01`でenable、`01 00`でdisable
  - 起動時は必ずdisabled。`SET_TARGET`は200ms timeout、B1/温度/センサ/C620 timeout/角度発散は停止。
  - 安全停止時は`unit_enabled=false`へラッチし、角度発散時の再START連打を防止。
- CANable用スクリプトを追加:
  - `firmware/scripts/run-canable-target-smoke.ps1`: SET_TARGETを周期送信し、enable後に短時間動かしてdisable。
  - `firmware/scripts/run-canable-target-session.ps1`: `invoke-hardware-session.ps1`経由でflash→smoke→SafeIdle(disable)。
  - `firmware/scripts/send-canable-unit-disable.ps1`: CANableからUNIT_CTRL disableだけを送る。
- 実機確認:
  - CANable COM16、G474 VCP COM15、NUCLEO-G474RE。
  - `θs=179912mdeg`, `ωw=500000milli-rpm`を20Hzで送信し、`UNIT_CTRL enable=1`後に`START_CAN`。
  - wheel commandはランプで500rpmまで到達し、角度誤差は最終的に0〜0.6°程度。
  - `UNIT_CTRL enable=0`で`STOP: disabled`、SafeIdleのdisable送信も成功。
- 最終状態:
  - 最新CAN制御ファームをflash/verify/reset済み。
  - 実機は起動時disabled、最後に`t12120100`をBody/SafeIdle両方で送信済み。

次: mini PC側または中央Teensy相当の送信器から、`θs`/`ωw`の連続プロファイルを生成して評価する。
まずはPC上のCANable送信ツールを、単発smokeではなく任意軌道/CSV/キーボード入力で使える形にする。

## 完了(2026-07-07 wheel RPM staircase試験ハーネス高速化)

- `firmware/src/main.c`の閉ループベンチ試験を、単一RPMではなく複数RPMを1回のflashで順次実行する
  staircase形式へ変更した。現在のステップは40/45/50/60/75/100/150 wheel-rpm。
- 1ステップが`STEP_TIMEOUT_MS`内に安定しない場合は`STEP_FAIL`を出して次RPMへ進む。
  角度発散、温度上限、センサ/C620 timeout、B1 abortは従来どおり即停止。
- `firmware/scripts/compact-test-log.ps1`をstep別集計に対応させ、1本のログから各RPMの後半mean/min/max/p-pと
  角度誤差を出せるようにした。
- `firmware/scripts/build.ps1`でDebugビルド成功。`compact-test-log.ps1`のPowerShell構文チェック成功。
- まだ実機flash/駆動はしていない。安全ゲートは`CLOSED_LOOP_TEST_ENABLED=0`のまま。

次: 実機セッションではmutex wrapper経由でこのstaircase HEXを1回だけflashし、ログ取得後にsafe-idleをflashする。

## 完了(2026-07-07 wheel 40rpm単点試験)

- C620 raw rpmを`/19`した既定ゲイン(steer Kp/Ki=50/20、drive Kp/Ki=5/20)で
  wheel 40rpmを10秒評価。後半平均33.999rpm、範囲-0.032〜243.561rpm、角度誤差peak
  1.670°、m1/m2非ゼロ率32%/34%で、停止・再始動を伴うスティックスリップのためFAIL。
- 2回目はdrive Kiだけ20→30へ変更したが、実行ツールがtimeoutしログ未生成のため評価不能。
  追加駆動は行わず、Ki=20へ戻した。最終状態は`CLOSED_LOOP_TEST_ENABLED=0`をclean buildし、
  mutex内でflash/verify/reset成功済み。ログ: `docs/tuning_logs/2026-07-07_wheel_40rpm_run1.log`。

最終更新: 2026-07-07(wheel 40rpm単点試験、FAIL)

## 完了(2026-07-06 C620 rpm単位修正・RPM点分割試験)

- C620 `feedback.rpm` はM3508内蔵19:1減速機より前のロータrpmと判明。制御器の
  `motor_max_rpm=469`、運動学、目標値は減速後出力軸rpmなので、`main.c`のmeasurement境界で
  raw feedbackを19で除算した。イテレーション12〜17は目標と測定の単位が19倍ずれており、
  そこから導いた「250rpmでも悪化」「低速域原因説を否定」は無効として扱う。
- 修正後、単一モーター50 output-rpmはKp=5/Ki=20で概ね47〜54rpmへ追従。
  差動wheel試験は暫定構成(steer Kp=50/Ki=20、drive Kp=5/Ki=20、current limit=2000、
  integral limit=1200)で50/60/75/100/150/250rpmを各10秒完走。25rpmは周期的な停止・再始動でNG。
  40rpmは正式な再試験が必要。正逆転および各点3回の再現性確認は未実施。
- RPM点ごとに短命エージェントを起動する`.claude/agents/wheel-rpm-point-tuner.md`、最新の
  `START:`〜`STOP:`だけ保存・集計する`scripts/compact-test-log.ps1`、実機処理を直列化して
  必ず安全待機を実行する`scripts/invoke-hardware-session.ps1`を追加。
- 別セッションが`main.c`を試験有効へ再編集していたため、競合中の実機試験は中止。
  `CLOSED_LOOP_TEST_ENABLED=0`へ戻し、clean build、flash、verify、reset済み。競合側が繰り返し
  `=1`へ戻したため、停止確認まで`main.c`を読み取り専用属性にして安全値を固定している。

次: 他セッションの編集停止を確認後、40rpmを正逆転・3回で判定。その結果を境界として
最低安定rpmを二分探索し、上限側は既知安定点から段階的に探索する。全実機操作はmutex wrapper経由。

## 完了(2026-07-06 単一モーター速度制御の追試、5アーキテクチャとも発振)

- 二モーター差動を切り離し、motor1単体・motor2=0固定で5種類のアーキテクチャを試験
  (詳細は`firmware/docs/CONTROL_LOOP_TUNING.md`「単一モーター速度制御の追試」参照):
  1. 単純rpm PI(KP=5,KI=100) → 激しいスティックスリップ限界サイクル
  2. +測定rpmへの一次LPF → 改善なし(キックは実際の動きでノイズではないと確認)
  3. +初期キック電流(1200raw) → キック自体は成功もPI移行後は同じ振動が継続
  4. 仮想シャフト位置追従(C620のrotor_angleで位置制御) → 改善なし
  5. 目標rpmを50→250へ引き上げ(低速域回避仮説) → **悪化**。低速域原因説は否定
- **結論**: 5種類ともKP=5/KI=100の内側電流PIゲインは共通で、外側アーキテクチャ変更では
  解決しないことを確認。ユーザーが目視した「モーターのガクガクした動き」は指令送信の
  不連続バグではなく、1kHzで正しく更新され続けている指令値自体が数百ms周期で
  大きく振動していることの物理的な現れと確認。
- セッション終了時、`CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で書き込み・verify・reset済み。
- 無負荷ベンチでのこれ以上の深追いは費用対効果が低いと判断し保留。

次: KIを大幅に下げる(100→20〜30程度)実験は未実施のまま保留。実走行(接地・負荷あり)で
摩擦特性を取り直すのが優先度高いかもしれない。

## 完了(2026-07-07 Linux機のビルド・書き込み環境整備)

- 開発機(Ubuntu 22.04、これまでのWindows/PowerShell環境とは別の作業PC)に
  ファーム開発ツールチェーンが未導入だったため、ユーザーと相談の上apt版で整備する方針を確定:
  - ARM GCC: 公式Arm GNU Toolchain 14.2(Windows側)ではなく、apt版
    `gcc-arm-none-eabi`(10.3-2021.07-4)を採用(手動導入の手間を避けるため)。
  - 書き込みツール: 公式`STM32CubeProgrammer`(ST公式サイトでのアカウント登録必須)ではなく、
    apt版`stlink-tools`(st-flash 1.7.0)を採用。
  - `ninja-build`(1.10.1)もaptで導入。
- `sudo apt-get install gcc-arm-none-eabi ninja-build stlink-tools`でインストール
  (初回は`unattended-upgrades`がdpkgロックを保持しており一時失敗、時間を置いて再実行で成功)。
- udevルールはパッケージ既定の`/lib/udev/rules.d/49-stlinkv*.rules`で足りており追加設定不要と確認。
- `firmware/scripts/build.sh debug`でビルド成功を確認(FLASH使用0.92%、RAM 1.19%)。
- `firmware/scripts/build.sh`・`flash.sh`に実行権限(`chmod +x`)が付いていなかったため付与。
- `flash.sh`を`STM32_Programmer_CLI`(Windows側専用、未導入)から`st-flash --reset write
  <bin> 0x08000000`(stlink-tools)呼び出しへ書き換え。`.hex`ではなく`.bin`成果物を使う点に注意。

### 現在の状態

- このLinux機でのビルドは動作確認済み。書き込みは未検証(作業時点でST-Link/ボード未接続、
  `st-info --probe`は0件)。ボード接続後に`./scripts/flash.sh debug`での実機書き込み確認が必要。
- Windows側の`build.ps1`/`flash.ps1`/`toolchain.ps1`(Arm GCC 14.2 + STM32CubeProgrammer前提)は
  無変更。今回の変更は`build.sh`/`flash.sh`(Linux用)のみ。

### 次の作業

1. ST-Link(NUCLEO-G474RE搭載のものでも可)をこのPCへ接続し、`st-info --probe`で認識確認。
2. `./scripts/flash.sh debug`で実機書き込みが成功するか確認する
   (ARM GCCバージョン差異(10.3 vs 14.2)によるバイナリ挙動差にも注意して見る)。

## 完了(2026-07-06 rpm発散ガード撤去・駆動ステップ10秒完走)

- ユーザー指摘: 「current_limitで既にハードクランプされているのだから、rpm誤差ベースの
  発散ガードは無駄」。閉ループのwheelステップテストからガードを撤去し、停止条件を
  角度発散(12°)・センサ/C620タイムアウト・B1・最大試験時間(10秒)のみに縮小。
- 再試験の結果、**誤停止なく10秒間完走**。イテレーション10のブレークアウェイ(~850raw)は
  再現し、m1/m2の実測rpmは試験中ずっと非ゼロで振れ続けた(スティックスリップ的な断続動作、
  滑らかな50rpm定常回転ではない)。
- **新知見**: 保持していたはずの操舵角が、開始から終了まで継続的に±0.5〜1.1°振動し続けた
  (単発ドリフトではなく持続的振動)。角度P制御が常にこの外乱を追いかけて
  `steer_rpm_command`が±2rpmを往復。差動機構の駆動→操舵への機械的カップリングが
  想定より強く持続的であることを示す実測データ(`CENTRAL_COORDINATED_CONTROL.md`の
  非干渉性検証項目1の裏付け)。
- セッション終了時、`CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で書き込み・verify・reset済み。
- 詳細は`firmware/docs/CONTROL_LOOP_TUNING.md`「イテレーション11」参照。

次: (1) 持続的な操舵振動への対策(カップリング補正項の要否、angle_deadband見直し等)。
(2) スティックスリップを抑えて滑らかな定常回転に近づける`drive_mode_ki`/
`wheel_accel_rpm_per_s`のチューニング。

## 完了(2026-07-06 駆動(差動)電流ブレークアウェイの開ループ確認)

- 前段(下記「駆動モードwheel≠0ステップ応答テスト」)のイテレーション9で見た
  `measured_wheel_rpm`の巨大スパイクについて、ユーザーから「実機は全然回っていない」との
  指摘を受け、PIを完全に排除した開ループ試験で切り分け。`main.c`を
  「motor1=+I, motor2=-Iの純粋差動電流を500raw/sでランプし、生のC620 rpm/torque_currentを
  20ms周期でそのままログする」テストへ書き換え。ホイールは接地させず浮かせて実施。
- 結果: **電流852(raw、current_limit=2000のうち)でm2rpm=-32を検出し正常にブレークアウェイ**。
  それまでm1/m2の生rpmはほぼ0(±3程度のノイズのみ)で、イテレーション9のような異常値は
  一度も出なかった。**C620フィードバック自体は健全と確認**。イテレーション9のスパイクは
  フィードバックのバグではなく、ブレークアウェイ瞬間の実際の機械的キック(スティックスリップ
  解放)だった可能性が高いと訂正。
- 結論: ホイールは実際に動く(固着・破損していない)。静止摩擦を破るのに約850raw
  (current_limit=2000の半分弱)必要なだけ。閉ループ試験(イテレーション8/9)が失敗していたのは、
  PIの積分がその電流に安定して到達する前に発散ガードへ引っかかっていたため。
- セッション終了時、`CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で書き込み・verify・reset済み。
- 作業中、Bashツール経由(cmd.exe)で`serial-monitor.ps1`を呼ぶと日本語コメント入りスクリプトで
  文字化け・パースエラーが発生する事象を確認。PowerShellツールから直接呼べば問題なし
  (関連: AGENTS.mdの日本語パス起因cmd.exe文字化け注意)。

次: このブレークアウェイ電流(~850raw、方向依存で変動しうる)を踏まえ、閉ループの発散ガードを
「瞬間的なブレークアウェイキックを誤検出しない設計」に見直し、`drive_mode_ki`/
`wheel_accel_rpm_per_s`を再チューニング。モード非干渉(操舵ドリフト-0.615°)の定量評価も残作業。
詳細は`firmware/docs/CONTROL_LOOP_TUNING.md`「駆動(差動)電流のブレークアウェイ確認」参照。

## 進行中(2026-07-06 駆動モード(wheel≠0)ステップ応答テスト)

- `main.c`を「操舵を起動角に保持しつつwheel目標を0→50rpmへステップ」するテストへ書き換え
  (`unit_controller_set_target`のwheel_rpm引数を初めて非ゼロで使用)。モード非干渉の確認と
  `wheel_accel_rpm_per_s`/`drive_mode_ki`の実機評価が目的。ホイールは接地させず浮かせて実施。
- 発散ガード(rpm誤差20rpm、ユーザー指定)を追加したが、初版はランプ完了直後に判定したため
  ブレークアウェイ電流に届く前に誤ってSTOP(モーターほぼ無回転のまま)。
  1.5秒の猶予期間(`WHEEL_ERROR_CHECK_GRACE_MS`)を追加して再試験。
- 猶予期間ありの再試験で`measured_wheel_rpm`計算値が単発で300〜500rpm相当まで跳ね上がり、
  発散ガードが誤発動して停止。**当初「フィードバックのノイズ/バグ」と誤診断したが、
  上記の開ループ確認で否定。ブレークアウェイの実キックだった可能性が高い。**

次: 上記「駆動(差動)電流ブレークアウェイの開ループ確認」参照。

## 完了(2026-07-06 serial-monitor.ps1 早期終了オプション)

- `scripts/serial-monitor.ps1` に `-EarlyExit` スイッチを追加。閉ループ試験ログを
  行単位で解析し、収束(|err|<500かつsteer=0が`-StableSamples`(既定4)連続)または
  `STOP:` 行を検出したら `-TailSeconds`(既定2秒)後に自動終了する。
  イテレーションあたり~8秒の短縮見込み。
- VCPバッファ再生対策: 接続後 `-StartIgnoreSeconds`(既定5秒)以内のSTART行は
  前回ファームの古いデータとして無視。flashが5秒未満で完了した場合は早期終了せず
  従来通りDurationSecondsまで走る(誤検出側に倒れない設計)。
- `-EarlyExit` 未指定時の挙動は完全に従来通り(実行中セッションへの影響なし)。
- 検証はハードウェア非接触で実施(構文チェック+判定ロジックのオフライン
  ユニットテスト7ケース、全PASS)。**実機での動作確認は次回チューニング
  イテレーションで行うこと。**
- gain-tuning SKILL.md の監視コマンドを `-EarlyExit` 付きに更新。

## 完了(2026-07-06 ゲイン調整再開・Ki確定)

- ユーザーがステア軸の手回し点検(引っかかり・ガタ・異音・AMT連れ回りズレ)を実施、異常なしを確認。
  通電試験を再開。
- イテレーション5: `mode_integral_limit=1200`込みで前回ベスト構成の実機再現に成功
  (~3.25秒、終端誤差0.07〜0.16°、発振なし)。積分クランプ導入の影響なしと確認。
- イテレーション6: `steer_mode_ki` 100→125で改善(~3.0秒、終端誤差0.02°、
  軽微な1サンプルのみのオーバーシュート、発振なし)。
- イテレーション7: `steer_mode_ki` 125→150(安全上限)は125より悪化(~3.25秒、
  誤差0.332°、Ki=100相当まで後退)。150は採用せず、**125を確定値**とした。
- `drive_mode_ki`は100のまま据え置き(wheel=0の操舵専用試験のため未検証。駆動実走時に個別調整)。
- セッション終了時、`CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で書き込み・verify・reset済み。
- gain-tuningスキルのシリアル監視時間をユーザー要望で45秒→15秒に短縮
  (収束が~3秒程度のため十分)。パラメータ表・ベスト実績も更新。
- 詳細は `firmware/docs/CONTROL_LOOP_TUNING.md` 実験ログ(イテレーション5〜7)参照。

次: Ki(操舵)は125で確定。次はangle_kp/steer_accelの詰め、または駆動モード
(wheel≠0)実走テストへ。drive_mode_kiは駆動実走時に別途検証が必要。

## 完了(2026-07-06 制御ループ改善: RoboMaster系実装との比較)

- RoboMaster系オープン実装(DJI公式C板例/standard_robot系)のM3508カスケード制御と
  現行モード座標PIを比較。構造は同等と確認し、欠けていた3点を導入:
  1. `mode_integral_limit`=1200(RM系max_iout相当の積分独立クランプ。固着中に積分が
     ±2000まで溜まって解放時に跳ぶ経路を遮断。Ki=200発振の一因への対策)
  2. 合成電流飽和時のモード比例スケーリング(m1/m2個別クランプによる操舵/駆動トルク比の
     歪みを解消)+飽和次周期の積分凍結。`torque_scaling_active`をログ出力に追加
  3. `wheel_accel_rpm_per_s`=200(駆動目標のランプ。値は未実測、実走テストで調整)
- 詳細と採用しなかった項目は `docs/CONTROL_LOOP_TUNING.md`「RoboMaster系オープン実装との
  比較と取り込み」参照。「mA」表記が実はC620生値(±16384=±20A)という単位注意も記録。
- Debugビルド成功(FLASH 4736B / RAM 1168B)。**実機未検証**(機構の手回し点検待ちのため
  通電試験は中断中のまま)。`CLOSED_LOOP_TEST_ENABLED=0`維持。

次: 手回し点検 → イテレーション3構成の再現確認(本変更込み。挙動差はiLimit=2000で切り分け)
→ Ki/angle_kpの詰め → 駆動実走。

## 方針更新(2026-07-06 CAN-G474主試験機)

- 購入済みMatek CAN-G474(STM32G474CE、CAN 2系統)を今後の主試験機とする。
- 購入済みCAN-L431は中央CANの対向ノード、NUCLEO-G474REは書込み復旧と回帰確認の予備とする。
- 現行ファームはNUCLEO固定ピンであり、そのままではCAN-G474へ移せない。CAN1 PA11/PA12は共通だが、
  CAN2をPB12/PB13からPB5/PB6へ、AMT22をSPI3 PC10/PC11/PC12+PD2から
  SPI2 PB13/PB14/PB15+PB12へ切り替えるボード定義が必要。
- G474CE(512KB Flash)のメモリ容量は現行G474REと同じだが、パッケージと露出ピン、LED、
  デバッグUARTが異なる。SWDまたはUART1 DFUで最小bring-upを完了してからモーターへ接続する。
- `docs/MATEK_CAN_G474_PORT.md`を作成。ArduPilot hwdef/AP_Periphの参照範囲、GPLコードを
  直接コピーしない方針、底面SWD+ST-LINKの配線、工場ブートローダとFlash配置の競合、
  復旧準備、段階bring-up、ボード別platform実装タスクを記録した。

次: CAN-G474実機の電源・SWD・Device ID/Option Bytes確認と工場ファーム復旧手段の確保 → ボード別ピン定義 → LED/GPIO実行確認 → CAN 2系統試験。

## 完了(2026-07-05 モード座標制御・ゲイン調整)

- unit_controllerをモード座標PI(操舵=和/駆動=差)へ書き換え。摩擦FFは
  実測ばらつき(150〜950mA、角度依存)を理由に廃止し、積分のみで吸収する方針に確定。
- 電流ランプ式の摩擦特性化テストを実装・実測(4方向×4試行)。
- テストアプリをB1保持式から起動時自動開始+B1中断ラッチ式へ変更。
- ゲイン調整4イテレーション実施。ベスト構成(Kp=5/Ki=100、steer_min_rpm=2、
  accel=50、limit=2000)で+10°を約3.5秒・終端誤差0.37°・オーバーシュートなし。
- **Ki=200は±2°の激発振(NG確定)。** 発振直後の試験で角度が-114°逆走して発散停止。
  機構損傷の可能性があり、通電試験を中断。**次回はユーザーの手回し点検から。**
- ST-LINK VCPの滞留バッファが古いログを再生する罠を確認(START行より前は捨てる)。
- 調整ループを他モデルへ委譲できるよう整備:
  `.claude/skills/gain-tuning/SKILL.md`(ランブック)と
  `.claude/agents/gain-tuner.md`(sonnet固定エージェント)。
- 詳細は `docs/CONTROL_LOOP_TUNING.md` の実験ログ参照。
- `CLOSED_LOOP_TEST_ENABLED=0`(安全待機)で引き渡し。

次: 手回し点検 → イテレーション3構成の再現確認 → gain-tunerエージェントで
Ki 100〜150 / angle_kp の詰め → 駆動モード実走テスト。

## 完了(2026-07-05 C620 CAN受信テスト実装)

- C620公式フィードバック形式(標準ID 0x201〜0x208、8byte、角度/rpm/トルク電流/温度)のデコーダを追加。
- FDCAN2を通常モード/クラシックCAN 1Mbpsで起動し、電流指令を送らず受信だけ行うテストアプリへ変更。
- 受信全件を処理し、ID 1/2の最新値・フレーム数・受信経過時間・PSRをVCPへ250ms周期で表示。
- Debugビルド成功(FLASH 3372B / RAM 1080B)、NUCLEO-G474REへの書き込み・verify・reset成功。
- COM15実測: ID 1/2ともfeedbackなし、unknown=0、PSR=0x70f。CANフレーム未検出。
- MCP2551の5V給電を修正後、ID1/ID2ともC620フィードバック受信に成功。
  age=1ms、温度28/27℃、静止rpm=0を確認し、手回しで角度・rpmが変化した。
  PSR=0x708/0x710、unknown=0。電流指令は未送信。ベンチ段階2合格。
- ベンチ段階3開始。B1押下中のみID1へ指令値+200(約0.24A)、最大500msでゼロへ戻す
  ガード付きテストを実施。C620 #1は微小動作し、モーター上部から見て時計回りを確認。
- 同じガード条件でC620 #2も微小動作し、モーター上部から見て時計回りを確認。
  両モーターのフィードバックと低電流指令動作を実機確認し、ベンチ段階3合格。
- テスト後は誤操作防止のため、ID1〜4へ10ms周期で0電流だけを送る安全待機アプリへ変更。

次: ベンチ段階3。ホイールを浮かせ、安全な電流上限を実装してから0x200へ微小電流指令を送る。

## 進行中(2026-07-05 差動閉ループ・自動同定)

- 目標ホイールrpm/目標ステア角を入力とする制御層を追加。角度P、ステア速度/加速度制限、
  操舵優先rpm配分、差動逆運動学、2モーターrpm PI、静止摩擦補償を実装。
- B1長押し中のみ現在角+10°を指令し、解放/2秒/AMT異常/C620受信途絶/角度発散で0電流へ戻す安全ゲートを実装。
- 高ゲインPIでは低速域で電流が正負飽和して振動したため、ゲイン推測を止め、共通モードの
  ブレークアウェイ電流を300〜800で自動測定する同定アプリへ変更。
- 正負両方向とも指令800までrpm=0、AMT角度変化=0。C620実トルク電流は指令へ追従
  (例: cmd=-800, fbI1=-794, fbI2=-789)しており、CAN/指令生成は正常。
- それ以前の固定-800試験ではステア軸が2〜3周動作しているため、現在は電源CC制限・24V降下・
  機械拘束など実機条件が変化した可能性が高い。追加増流は禁止し、実機切り分け待ち。
- 原因は安定化電源の電流制限(CC)だったことをユーザー確認。C620実トルク電流が指令へ追従しても
  電源側で出力が制限され、rpm/AMTが動かなかった。電源設定修正後の再同定待ち。
- 電源CC設定修正後、個別ブレークアウェイを自動測定。Motor 1は約814〜1009、Motor 2は
  約814〜1022で始動し、初期キック1125を設定した。
- 個別rpm PI+瞬時rpm閾値によるキック切替は、静止付近のrpmノイズで左右非同期になり振動した。
  目標+10°に対して有意な角度移動は得られず、2秒タイムアウトで安全停止した。
- 次回方針を`docs/CONTROL_LOOP_TUNING.md`へ記録。モーター個別PIをやめ、操舵(和)/駆動(差)の
  モードPI、rpmフィルタ、同期キック(固定時間+ヒステリシス)へ変更する。
- セッション終了時、`CLOSED_LOOP_TEST_ENABLED=0`としてB1動作を無効化。安全待機で引き渡す。

次: `docs/CONTROL_LOOP_TUNING.md`に従いモード座標制御を実装し、監督付き試験時のみ
`CLOSED_LOOP_TEST_ENABLED=1`へ変更して+10°応答を再確認する。

## 完了(2026-07-04 AMT22ベンチテスト実装)

- SPI3(PC10=SCK、PC11=MISO、PC12=MOSI、PD2=CS_N)のAMT222A-Vドライバを追加。
- SPI Mode 0 / 1MHz、CS前後・バイト間3us、2バイト個別転送、チェックビット検証を実装。
- 12bit位置と角度を100ms周期でST-LINK VCP(115200bps)へ出力するテストアプリへ変更。
- NUCLEO CN7配線を起動ログへ表示し、起動後250msの静止待ちを追加。
- Debugビルド成功(FLASH 2976B / RAM 1032B)。実機書き込みとVCPログ確認は未実施。
- 書き込み試行時、接続されていたのは想定のNUCLEO-G474REではなくNUCLEO-G431RB
  (ST-LINK SN `0031004E3532510831333430`, VCP COM14)だった。G474向けHEXの書き込みと
  verify/resetまでは成功したが、対象不一致のためAMT22実機評価は中止。正しいG474REへ
  接続し直して再書き込みが必要。
- NUCLEO-G474REへ交換後、SN `0033003E3532510731333430` / 3.32V / 512KBとして検出し、
  AMT22テストファームの書き込み・verify・resetに成功。VCPはCOM15。
- `scripts/serial-monitor.ps1`を追加。ST-LINK VCP自動検出または`-Port COM15`指定で常時表示可能。
- COM15実測は`raw=0x0 pos=0 angle=0.0 deg check=ERROR spi=OK`。MCU側SPI転送は完了するが
  AMT222から有効応答を受信できていない。5V/GND、Pico-Lockのピン番号、MISO配線を実測確認する。
- 配線再確認後、AMT222のセンサー値取得を実機確認済み(2026-07-04、ユーザー確認)。
  次は手回しで`check=OK`の継続、0〜4095の範囲、回転方向、一周時のラップを記録する。

次: AMT222A-VをCN7へ配線し、`scripts/flash.ps1`で書き込み、VCPログの`check=OK`と手回し時の角度変化を確認する。

## 完了(2026-07-02 ベンチ段階1)

- `platform/uart.c` を追加: LPUART1(PA2/PA3、ST-LINK VCP直結)115200bps、最小printf(%s %c %d %u %x)。
- `platform/fdcan.c` を追加: G4固定メッセージRAMレイアウト対応のベアメタルFDCANドライバ。
  - クラシックCAN 1Mbps(HSI16 PCLK直、BRP=1、16tq、サンプルポイント87.5%)
  - FDCAN1(中央CAN、PA11/PA12 AF9)、FDCAN2(C620、PB12/PB13 AF9)
  - 内部ループバックモード、全受信→FIFO0、送信3スロットFIFO、ポーリング送受信
- `stm32g4xx_min.h` を拡張: RCC(APB1ENR1/2、CCIPR)、GPIOB、LPUART1、FDCANレジスタ定義。
- main.cを段階1テストアプリに変更(両バスのループバック検証、LED表示、5秒ハートビート)。
- **実機確認済み**: NUCLEO-G474REで両FDCANともPASS。
  VCP実ログ: `[FDCAN1/central] PASS (id=123 dlc=8 PSR=708)` / `[FDCAN2/C620] PASS` / `result: ALL PASS`。
  PSRのLEC=0(プロトコルエラーなし)。COM13でハートビート継続動作確認。

次: ベンチ計画の段階2(MCP2551配線→C620フィードバック受信)。C620プロトコルのエンコード/デコード実装が必要。

## 完了(2026-07-02)

- Arm GNU Toolchain 14.2.Rel1をwingetで導入した(`C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\14.2 rel1`)。
- `scripts/toolchain.ps1`を追加した。STM32Cube拡張バンドル(`%LOCALAPPDATA%\stm32cube\bundles`)のCMake/Ninja/Programmer/GDBとArm GCCを自動発見してPATHへ載せる。build.ps1/flash.ps1から自動で読み込まれるため、手動PATH設定は不要になった。
- `.vscode/launch.json`にgdb/GDBサーバ/Programmerの実体パスを明示した(従来はPATH頼みでデバッグ起動不可だった)。
- CMakeのPOST_BUILDを相対パス化した。日本語を含む作業パス(`趣味`)がcmd.exe経由で文字化けし、objcopyが失敗する問題の回避。
- Debugビルドが通ることを確認した(FLASH 848B / RAM 1032B、ELF/HEX/BIN/MAP生成)。
- `flash.ps1`でNUCLEO-G474RE(SN 004F002C3532510731333430)のFlashへ書き込み、ベリファイ成功、リセット実行した。Flash上のSTデモは本ファームで上書きされた。

## 完了(2026-07-01以前)

- firmwareプロジェクトのGCC/CMake/Ninja構成を作成した。
- テスト対象をNUCLEO-G474RE / STM32G474RET6へ変更した。
- B1 USER (PC13、押下High) とLD2 (PA5、High点灯) の実機ピンを確認した。
- B1を押している間だけLD2を点灯する処理と20 msデバウンスを実装した。
- PowerShell/POSIXのビルド・書き込みスクリプトを追加した。
- VS Code、CMake Preset、ST-LINKデバッグ設定を追加した。
- SRAM診断コードを正規ベクタ付きで高位SRAMから実行し、B1→LD2動作を実機確認した。
- ST-LINK firmwareをV3J9M3からV3J17M10へ更新した。
- STM32CubeProgrammer 2.22.0で再認識を確認した。
- ST-LINK GDB Server 7.13.0が接続待機まで進むことを確認した。
- Bring-up、書き込み時の注意、エンコーダ段階テストを`docs/BOARD_BRINGUP.md`へ記録した。

## 現在の実機状態

- Flashには本プロジェクトのB1→LD2ファーム(Debugビルド)が書き込み済み。ベリファイ・リセットまで確認。
- 人手での実機動作確認(B1を押している間だけLD2点灯、RESET後も維持)が未実施。

## 未完了・次の作業

1. RESET後もB1を押している間だけLD2が点灯することを実機で確認する(人手)。
2. エンコーダはAMT22で確定(絶対値SPI、5V、Mode 0、≤2MHz、バイト間2.5µs/リード間40µs/CS解放前3µs、上位2bitチェックビット)。詳細は `docs/electrical/CARRIER_BOARD_REQUIREMENTS.md` 参照。全信号3.3V直結でよい。
3. AMT22のSPI読み取りを実装する(`docs/BOARD_BRINGUP.md`の段階テスト準拠)。
4. ~~搭載ボードを確定する~~ → **2026-07-02時点ではNUCLEO-G474RE、2026-07-06に主試験機をMatek CAN-G474へ変更。** 中央通信の2バスCAN構成は維持し、NUCLEOは予備とする。startupファイルは `startup_stm32g4xx.s` にリネームし、CMakeLists更新済み。
5. FDCAN1/FDCAN2のピン割当をCubeMXで確定し、morphoに出ていることを確認する(`docs/electrical/CARRIER_BOARD_REQUIREMENTS.md`参照)。

## 環境上の注意

- 現セッションでは`.git/index`が読み取り専用で、Gitコミットを作成できなかった。
- firmware、`.vscode`、`.gitignore`の変更はワークツリーへ保存済み。
- CADや既存docsの別作業変更は今回のfirmware作業へ含めないこと。

## wheel staircase試験(2026-07-07)

- `invoke-hardware-session.ps1`経由で実機試験を2回実行し、各回とも終了後に
  `CLOSED_LOOP_TEST_ENABLED=0`のsafe-idleをflash/verify/resetした。最終状態もsafe-idle。
- 標準staircase(40/45/50/60/75/100/150rpm、drive Kp/Ki=5/20、steer Kp/Ki=50/20):
  全stepが`STEP_OK`で完走。`firmware/logs/staircase-2026-07-07T04-31-33-622Z.log`。
  `STEP_OK`直前1秒の代表値:
  - 40rpm: 31.06〜46.13rpm、平均40.74rpm、角度誤差max 0.97°
  - 45rpm: 43.94〜51.99rpm、平均47.78rpm、角度誤差max 1.76°
  - 50rpm: 45.00〜59.00rpm、平均49.57rpm、角度誤差max 1.58°
  - 60rpm: 51.51〜68.58rpm、平均60.91rpm、角度誤差max 1.58°
  - 75rpm: 69.67〜84.93rpm、平均80.27rpm、角度誤差max 0.53°
  - 100rpm: 85.54〜104.89rpm、平均92.52rpm、角度誤差max 0.62°
  - 150rpm: 131.29〜159.61rpm、平均151.50rpm、角度誤差max 0.88°
- 低速staircase(一時的に25/30/35/40rpmへ変更):
  `firmware/logs/staircase-lowrpm-2026-07-07T04-34-11-016Z.log`。
  25rpmと35rpmは`STEP_OK`、30rpmと40rpmはtimeout。角度誤差は最大10.37°まで出たが、
  12°の停止ガードには届かなかった。結果が非単調なため、低速限界は単純なrpmしきい値ではなく
  始動角・局所摩擦・駆動→操舵カップリングに依存している可能性が高い。
- 暫定判断: 現ゲインでは正転・無負荷・この姿勢の「一発通過」なら40rpm以上は動くが、
  30〜40rpm帯は再現性未確定。最低安定rpmとして採用するには、角度誤差ガードを厳しめ
  (例: step内6°程度)にして、正逆・開始角を変えた複数回試験が必要。

次:
1. 低速境界を詰めるなら、同一rpm単点を開始角を変えて3回ずつ実施し、30/35/40rpmの再現性を判定。
2. 角度外乱が大きいので、次のゲイン調整はdrive Kiを上げる前に操舵保持側
   (`angle_kp_rpm_per_deg`、`steer_max_rpm`、`steer_mode_ki`)を少し戻す試験を優先。
3. ログへ`torque_scaling_active`を出して、STEP_OK判定と集計で飽和有無を直接確認できるようにする。

## wheel staircase試験(2026-07-07 追加: 操舵保持強化と中高速)

- 試験ハーネスを更新:
  - `torque_scaling_active`を`scale=`としてログ出力。
  - `compact-test-log.ps1`でstep別の電流スケーリング率を集計。
  - step内角度誤差が6°を300ms超えたら、そのstepを`STEP_FAIL: angle`として次へ進める
    ガードを追加(12°超の即停止ガードは維持)。
- 操舵保持を少し強化:
  - `steer_max_rpm`: 0.5 -> 1.0
  - `angle_kp_rpm_per_deg`: 0.1 -> 0.2
  - `steer_mode_ki`: 20 -> 30
- 低速再試験(30/35/40rpm): `firmware/logs/staircase-lowrpm-steerhold-2026-07-07T04-42-02-928Z.log`
  - 30rpm: timeout、終了時 measured 0rpm、angleErr -1.406°
  - 35rpm: timeout、終了時 measured 0.001rpm相当、angleErr 0.176°
  - 40rpm: `STEP_OK`、直前1秒平均39.37rpm、p-p 11.94rpm、角度誤差max 0.44°
  - 全体の最大角度誤差は3.43°、`scale=1`は0%。操舵外乱は大きく改善したが、
    30/35rpmは角度ではなく駆動側stick-slipで不合格。
- 中高速試験(40/75/150/250/350rpm): `firmware/logs/staircase-highrpm-steerhold-2026-07-07T04-44-49-432Z.log`
  - 全stepが`STEP_OK`で完走、`scale=1`は全step 0%。
  - 直前1秒:
    - 40rpm: 平均39.36rpm、p-p 9.34rpm、角度誤差max 0.70°
    - 75rpm: 平均69.23rpm、p-p 11.18rpm、角度誤差max 0.79°
    - 150rpm: 平均148.84rpm、p-p 20.77rpm、角度誤差max 0.53°
    - 250rpm: 平均239.55rpm、p-p 50.40rpm、角度誤差max 1.14°
    - 350rpm: 平均345.75rpm、p-p 81.13rpm、角度誤差max 0.79°
- 暫定判断:
  - 下限は40rpm。30/35rpmは現状の無負荷正転では採用しない。
  - 350rpmまでは電流飽和なし・操舵保持良好で通過。速度p-pは高速ほど増えるため、
    次は500/750/1000rpm級へ段階拡張し、`motor_max_rpm`由来のwheel上限(約1360rpm)に近づける。
- 最終状態:
  - 実機は`CLOSED_LOOP_TEST_ENABLED=0`のsafe-idleをflash/verify/reset済み。
  - `firmware/src/main.c`は次回用に40/75/150/250/350rpm staircase、操舵保持強化、
    step角度FAIL、`scale=`ログを残し、`CLOSED_LOOP_TEST_ENABLED=0`。

## wheel 長時間・拘束領域試験(2026-07-07)

- ユーザー指摘により、従来の1秒安定判定では定常評価が短すぎるため試験ハーネスを変更:
  - `STEP_TIMEOUT_MS=25000`
  - `STEP_MIN_DWELL_MS=10000`
  - `STEP_STABLE_MS=3000`
  - 拘束時に要求rpmとの差でtimeoutしないよう、安定判定を要求targetではなく
    `output.wheel_rpm_command`基準へ変更。
  - `STEP_OK/STEP_FAIL`へ`cmd=`を追加。
- 長時間staircase(500/750/1000/1200/1400rpm要求):
  `firmware/logs/staircase-long-highrpm-constraint-2026-07-07T04-49-46-624Z.log`
  - 全step `STEP_OK`、実機は終了後safe-idleをflash/verify/reset済み。
  - 直前1秒:
    - 500rpm: 平均500.03rpm、p-p 5.06rpm、角度誤差max 0.53°、scale 0%
    - 750rpm: 平均749.72rpm、p-p 3.99rpm、角度誤差max 0.62°、scale 0%
    - 1000rpm: 平均1000.10rpm、p-p 2.96rpm、角度誤差max 0.62°、scale 0%
    - 1200rpm: 平均1200.27rpm、p-p 2.50rpm、角度誤差max 0.62°、scale 0%
    - 1400rpm要求: `cmd`平均約1363rpm、実測平均1363.49rpm、p-p 1.86rpm、
      角度誤差max 0.62°、scale直前1秒0%
  - step全体のfinal-half集計では1400rpm要求stepで`scale=1`が0.8%。ただし安定窓では0%。
- 判断:
  - 500〜1200rpmは10秒保持後に非常に安定。無負荷・正転ではdrive PIは十分。
  - 1400rpm要求は`motor_max_rpm=469`とdrive比32/11によるwheel上限約1364rpmに拘束され、
    制御器の`wheel_rpm_command`も約1363rpmへ制限される。拘束領域でも角度保持は良好。
  - 現時点の無負荷正転レンジ: 下限40rpm、上限は約1360rpm(機構/設定上限)。30/35rpmは不採用。
- 次:
  1. 正転だけでなく逆転(-40/-500/-1000/-1400)を同じ長時間保持で確認。
  2. `STOP: `が空で出るログ行を修正し、完走時は`STOP: staircase complete`を確実に出す。
  3. 接地・拘束状態へ移る前に温度ログを集計へ追加し、長時間高負荷で温度上昇を見る。

## wheel 逆転代表点試験(2026-07-07)

- 逆転側の代表点として -40/-500/-1400rpm 要求を長時間保持で試験。
  `firmware/logs/staircase-reverse-representative-2026-07-07T04-55-26-552Z.log`
- 負方向の安定判定で許容幅が常に10rpmになる問題を修正:
  `wheel_tolerance`を`abs(effective_target)`基準へ変更。
- 結果:
  - 全step `STEP_OK`、実機は終了後safe-idleをflash/verify/reset済み。
  - 直前1秒:
    - -40rpm: 平均 -42.39rpm、p-p 9.02rpm、角度誤差max 0.53°、scale 0%
    - -500rpm: 平均 -500.31rpm、p-p 1.90rpm、角度誤差max 0.62°、scale 0%
    - -1400rpm要求: `cmd`約 -1363rpm、実測平均 -1362.55rpm、p-p 2.26rpm、
      角度誤差max 0.70°、scale 0%
- 判断:
  - 逆転代表点でも問題なし。無負荷では正逆とも `|wheel rpm|=40〜約1360rpm` を
    `ωw, θs` 指令で制御できる状態。
  - 次は接地/拘束状態での温度・電流余裕・低速stick-slipの再評価。

## wheel 500rpm + steer +10deg 同時指令試験(2026-07-07)

- 接地試験ができないため、次段階として「`ωw`を出しながら`θs`を動かす」確認へ移行。
- 試験内容: 起動角から`θs=+10°`、同時に`ωw=500rpm`。長時間保持ハーネスを流用し、
  1stepのみ実行。
- 初回ログ: `firmware/logs/theta-step-wheel500-2026-07-07T05-01-36-470Z.log`
  - `θs=+10°` stepを入れた直後に、既存のstep内角度誤差6°/300ms FAILが働き、
    評価前に終了。角度step試験ではこのガードは不適切。
- 再試験:
  - `STEP_ANGLE_FAIL_DEG_MILLI`を一時的に12000へ緩和。
  - ログ: `firmware/logs/theta-step-wheel500-retry-2026-07-07T05-02-45-975Z.log`
  - `START: angle=185.186° target=195.186° wheelTarget=500`
  - `STEP_OK: target=500 cmd=500.000rpm measured=499.349rpm angleErr=0.156°`
  - 100msログ基準で、角度誤差は約0.9sで2°以内、約1.0sで1°以内/0.5°以内へ到達。
  - final-half wheel: 平均500.111rpm、p-p 9.914rpm、角度誤差max 0.771°、
    scale 0%、maxTemp 29°C。
- 判断:
  - 無負荷では`ωw=500rpm`を維持しながら`θs=+10°`へ収束できる。
  - 次は`ωw=500rpm`で`θs`を+10/-10/0へ往復させる、または低速/高速代表点
    (`ωw=40/1200rpm`)で同じ角度stepを確認する。

## wheel 500rpm + steer +90deg 切り分け試験(2026-07-07)

- ユーザー指摘: +10°/20°では角度変位が小さく、目視切り分けしにくい。
  `ωw=500rpm`のまま`θs=+90°`へ変更して試験。
- 試験1: `steer_min_rpm=2`のまま。
  `firmware/logs/theta90-wheel500-2026-07-07T05-10-13-158Z.log`
  - ログ上は約0.9sで角度誤差1°以内まで到達。
  - ただし終端で`steer_min_rpm=2`由来のリミットサイクルが出て、±2〜3°程度で揺れ、
    3秒安定判定に入れずtimeout。
- 試験2: `steer_min_rpm=0`へ変更。
  `firmware/logs/theta90-wheel500-nomin-2026-07-07T05-11-51-426Z.log`
  - `STEP_OK`。ログ上のAMT角は49.922° -> 138.516°付近へ約90°変化。
  - 約0.9sで1°以内、保持時は角度誤差0.1〜0.4°程度。
  - final-half wheel平均500.013rpm、p-p 6.845rpm、角度誤差max 0.439°、
    scale 0%、maxTemp 30°C。
- 重要な未解決点:
  - ユーザー目視ではステア変化が見えなかった。ログ上のAMT角は約90°変わっているため、
    「AMTが見ている軸」と「実際にステアとして見ている出力」の間にズレ/滑り/観察点違いが
    ある可能性がある。
  - 次は通電試験ではなく、無通電でステア出力を手で90°動かし、AMT角が同じだけ変わるかを
    確認する。AMTだけ変わって出力が変わらない場合は、機械結合/エンコーダ取付を点検する。

## wheel 500rpm定常 + steer 90deg刻み試験(2026-07-07)

- ユーザー提案により、wheel立ち上がり過渡を切り離すため、先に`ωw=500rpm, θs=base`
  で定常化してから、`θs=base+90/+180/+270/+0°`へ90°刻みでstepする試験に変更。
  step間で`unit_controller_reset()`は呼ばず、wheel状態と積分を維持。
- ログ: `firmware/logs/steer-90deg-steps-wheel500-2026-07-07T05-16-32-974Z.log`
- 結果:
  - step0 base: `STEP_OK`、final-half wheel平均500.08rpm、p-p 6.88rpm、角度誤差max 0.53°
  - step1 +90°: `STEP_OK`、final-half wheel平均500.01rpm、p-p 5.81rpm、角度誤差max 0.53°
  - step2 +180°: `STEP_OK`、final-half wheel平均499.85rpm、p-p 8.13rpm、角度誤差max 0.62°
  - step3 +270°: `STEP_OK`、final-half wheel平均500.03rpm、p-p 5.91rpm、角度誤差max 0.62°
  - step4 +0°: `STEP_OK`、ただしユーザーが最終stepでホイールに触れたため外乱あり。
    final-half wheel p-p 93rpmは速度制御評価から除外する。角度誤差は0.53°以内。
- 判断:
  - 少なくともstep0〜3では、`ωw=500rpm`定常中に90°刻みで`θs`を変更しても、
    AMT角ログ上は各目標へ収束し、wheel速度も維持できている。
  - ユーザー目視でもステア出力は良さそうとのこと。AMT角ログと物理ステア出力は概ね一致している
    扱いで次へ進める。ただし最終stepはホイール接触外乱ありのため速度評価から除外。

## wheel 40/1200rpm定常 + steer 90deg刻み試験(2026-07-07)

- 500rpmで成立した90°刻み試験を、低速代表40rpmと高速代表1200rpmへ展開。
- 40rpm: `firmware/logs/steer-90deg-steps-wheel40-2026-07-07T05-22-52-902Z.log`
  - 全step完走。角度は概ね追従し、step0〜3の角度誤差maxは0.7°以内。
  - ただしwheel p-pが大きい(step0 41rpm、step3 85rpm、step4 129rpm)。
    40rpmは機構摩擦を超える瞬間のオーバーシュート/stick-slip境界と判断。
  - 実用下限は40rpmではなく75rpmから扱う方針へ変更。
- 1200rpm: `firmware/logs/steer-90deg-steps-wheel1200-2026-07-07T05-27-36-868Z.log`
  - 全step `STEP_OK`、scale 0%。
  - step0 base: final-half wheel平均1202.65rpm、p-p 37.98rpm、角度誤差max 0.53°
    (立ち上がり/定常化込み)
  - step1 +90°: 平均1199.86rpm、p-p 3.60rpm、角度誤差max 0.70°
  - step2 +180°: 平均1200.25rpm、p-p 3.57rpm、角度誤差max 0.70°
  - step3 +270°: 平均1199.96rpm、p-p 3.54rpm、角度誤差max 0.70°
  - step4 +0°: 平均1200.15rpm、p-p 3.58rpm、角度誤差max 0.70°
  - maxTempは30°Cから36°Cまで上昇。
- 判断:
  - 実用域は暫定`|ωw| >= 75rpm`。
  - 1200rpm定常中の90°刻み`θs`変更は非常に安定。無負荷単体ユニットでは
    `ωw, θs`指令制御は成立。

## 中央CAN(FDCAN1)受信ログ準備(2026-07-07)

- NUCLEO-G474REの中央CAN用FDCAN1(PA11=RX/CN10-14、PA12=TX/CN10-12)に
  2個目のCANトランシーバを接続した前提で、ファームにFDCAN1初期化を追加。
- `CLOSED_LOOP_TEST_ENABLED=0`のsafe-idleのまま、FDCAN1で受信した全フレームをVCPへ
  `CENTRAL_RX id=... dlc=... data=...`として表示する。
- `0x100 + unitId(=1)`、DLC 8を`SET_TARGET`としてlittle-endian int32 x2で仮decodeし、
  `SET_TARGET_RX steer=... wheel=...`を表示する。まだ制御には接続しない。
  - byte0-3: `targetSteerMdeg`
  - byte4-7: `targetWheelRpmMilli`
- `docs/communication/COMMUNICATION_NAMING_AND_IDS.md`へSET_TARGETのlittle-endian規約を追記。
- Debugビルド成功後、実機へflash/verify/reset済み。最終状態はsafe-idle。
- CAN受信確認時に邪魔になるため、`run=0`の100ms周期ログは止め、従来テレメトリは
  `active`時のみ出すように変更。再ビルド・flash/verify/reset済み。

次:
1. PCのCANableから中央CANへ`0x101` DLC8を送信し、G474 VCPで`CENTRAL_RX`と
   `SET_TARGET_RX`が出ることを確認。
2. 受信確認後、enable/timeout付きで`SET_TARGET`を`unit_controller_set_target()`へ接続する。

## 中央CAN(CANable -> FDCAN1)受信確認(2026-07-07)

- PCにCANableをUSB-C接続。Windows上では追加シリアル`COM16`として認識、G474 VCPは`COM15`。
- CANable(SLCAN)へ以下を送信:
  - `C`
  - `S8` (1Mbps)
  - `O`
  - `t1018905F010020A10700`
- payloadは`SET_TARGET`:
  - steer=90000mdeg (`90 5F 01 00`)
  - wheel=500000rpm*1000 (`20 A1 07 00`)
- G474 VCP実測:
  - `CENTRAL_RX id=101 dlc=8 data=90 5f 1 0 20 a1 7 0`
  - `SET_TARGET_RX steer=90000 wheel=500000`
- 判断:
  - CANable -> 中央CANトランシーバ -> G474 FDCAN1(PA11/PA12)の受信経路は成立。
  - 次は`SET_TARGET`をenable/timeout付きで制御目標へ接続する。

## ESP32 Bluetooth→NUCLEO UART ベンチ送信機(2026-08-02)

- MCP2551中央CANベンチ経路を撤去し、ESP32↔NUCLEOを3.3V UART 115200bpsへ変更。
  固定長14byte、sync/type/sequence、steer mdeg、wheel rpm×1000、enable、CRC8を送受信する。
- ESP GPIO17/TX→NUCLEO PC5/USART1_RX（D0/CN10-6）、NUCLEO
  PA9/USART1_TX（CN10-21）→ESP GPIO22/RX、GND共通。
- NUCLEO側はUSART1 FIFOとoverrun自動復帰を実装。指令timeoutを1000ms→200msへ短縮。
- 初期実動では左スティックを操舵角/車輪速度へ変換し、R1をデッドマン、OPTIONSを
  arm切替とした。後に操作性改善のため、左スティックX=操舵（0°基準±90°、実機確認で
  左右符号を反転）、右スティックY=正逆スロットルへ分離した。速度上限は起動時500rpm、
  十字キー上下で250rpm刻み（250〜1300rpm）に変更でき、変更時は短く振動する。
- Bluepad32 Arduino framework 4.1.0（package表示4.0.2）でPlatformIOビルド成功。
- Ubuntuの`brltty-udev`を停止してCH341を再ロードし、ESP32-D0WD-V3へ安全ロック版を
  書き込み・verify・再起動まで成功。
- UART双方向通信成立。NUCLEOで`tgt=1`、`fdbk=1`、ESPでSTATUS 50frame/s受信を確認。
- DualSenseをBluepad32で認識（VID 054c/PID 0ce6）。AMT現在位置raw約3258を0°として
  Flash保存し、電源再投入後の永続化を確認。
- 車輪浮上状態でOPTIONS arm + R1デッドマンを実動確認。約15rpm指令に対し実測
  約14.6rpm、操舵角も目標付近へ追従し、制御挙動は良好。
- 角度乖離停止後にR1保持で再enableを繰り返す問題を修正。センサ/C620 timeout、過温、
  角度乖離、B1停止後はenable=0指令を受けるまで再armしないラッチを追加した。
- ESP側も操舵目標を現在角±90°へ制限。ESP/NUCLEOとも再ビルド・実機書き込み成功。
  現在は浮上試験用として`DSD_MOTOR_ENABLE_ALLOWED=1`。
- 次: 分離した左右操舵・右前後スロットルの符号と操作感を確認し、必要なら軸反転・
  上限値を調整する。

## AMT原点再校正(2026-08-04)

- ユーザー指定位置で`BENCH_SAVE_CURRENT_ZERO_ON_BOOT=1`のワンショット版を実行し、
  AMT raw=331をFlashへ保存。`save=1`、sequence=3、CRC errorなしを確認。
- マクロを0へ戻した通常版を再ビルド・書き込み。再起動後も`zero=331`を保持し、
  現在角は359.824°（0°に対して-0.176°）付近で安定。
- NUCLEOのST-Link仮想ドライブ容量（32KB）に対してHEXが32755byteで収まらなかったため、
  約11KBの`differential_swerve_firmware.bin`をドラッグ&ドロップ相当で書き込んだ。

## ESPラジコン同期ログ・LittleFS記録(2026-08-07)

- ESP32へ20Hz同期TELを追加し、steer/wheelのtarget/actual/error、enable/unit_active、
  UART bad/gap/txFailを1行へ格納。PythonでCSV取得・定常/過渡分離・停止時間・通信品質・
  グラフを自動解析できるようにした。
- 浮上90秒ログ（1801sample）: UART error/gap/txFail=0、定常steer誤差p95=0.439°、
  max=1.170°、定常wheel誤差p95=13.059rpm（相対1.086%）。定常制御は良好。
- 急な左右切返しではESPの直接角度指令により最大90°errorへ到達。次はESPベンチ送信側の
  steer rate/profile整形を検討する（最終構成では中央Teensyの責務）。
- R1解除から30rpm以下はmedian 75ms、max 750ms。maxは解除直前約235rpmのimmediate
  disable後の惰性。通常停止の閉ループ減速と緊急disableは分離して評価する。
- USB拘束をなくすためESP内蔵LittleFSへ20Hz CSVを保存。十字左で開始/停止し、USB再接続後は
  PCから`D`を送って自動dumpする。録画中はUSB TELを止める。
- `capture_radio_telemetry.py`、`analyze_radio_telemetry.py`、`download_offline_log.py`、
  `TELEMETRY.md`を追加。
- PC USBなし録画→USB再接続→自動dump→解析の実機end-to-end試験を完了。
  96.09秒/1920sample、UART bad/gap/txFail=0、定常steer誤差p95=0.264°・max=0.527°、
  定常wheel相対誤差p95=2.928%、R1停止median=25ms・max=350ms。この記録も浮上・無負荷。
- 続けて最新の内蔵ログ79.08秒/1581sampleを回収。UART bad/gap/txFail=0、定常steer誤差
  p95=0.364°・max=0.777°、定常wheel絶対誤差p95=24.129rpm（相対p95=5.539%）、
  R1停止median=75ms・max=1.300s。単輪の定常操舵と通信は3輪試験へ進める水準と判断した。
- 次は3輪を浮上状態で組み、各輪の回転方向・ステア原点・車体指令への対応を確認する。
  成立後、250〜500rpm上限から接地試験へ進み、3輪同時動作時の電源・通信・停止ログを採る。
