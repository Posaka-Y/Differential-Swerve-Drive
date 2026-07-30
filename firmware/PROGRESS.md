# Firmware progress

最終更新: 2026-07-31(リアルタイムベクトルGUI・空走制御セーブポイント)

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
