# V2 作業用プロジェクト

2026-09-23着手。**設計途中・製造禁止**。

要件正本: [UNIT_ODOMETRY_V2_REQUIREMENTS.md](../../docs/electrical/UNIT_ODOMETRY_V2_REQUIREMENTS.md)

V1の保存済み作業ツリーから分離した。ファイル名を維持しているのはKiCad階層インスタンス参照のため。
V1の製造済み基板との差分は基準マニフェストを参照。

2026-09-23: 駆動回路図の旧GH6デバッグ端子J7をCortex Debug 1.27mm 2×5配列へ置換。pin1=MCUデジタル3.3V(VTref)、2=SWDIO、3/5/9=GND、4=SWCLK、6=SWO、7/8=NC、10=NRST。UARTは独立した2.54mm 1×3スルーホールヘッダJ9（1=GND、2=MCU TX、3=MCU RX）へ変更。3.3Vロジック専用で給電ピンはない。ERC 0、既存接続照合を確認済み。レポートは`../../output/kicad-check/v2/unit/uart-header-check.md`。

J7の正式MPN・キー形状・嵌合ケーブル・フットプリントは未確定で、回路図のFootprintは意図的に空欄。PCBはV1の旧GH6配置・配線が残るため、回路図との同期前に製造してはいけない。UART J9もPCBへ未反映。
