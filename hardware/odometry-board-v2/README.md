# V2 作業用プロジェクト

2026-09-23着手。**設計途中・製造禁止**。

要件正本: [UNIT_ODOMETRY_V2_REQUIREMENTS.md](../../docs/electrical/UNIT_ODOMETRY_V2_REQUIREMENTS.md)

V1の保存済み作業ツリーから分離した。ファイル名を維持しているのはKiCad階層インスタンス参照のため。
V1の製造済み基板との差分は基準マニフェストを参照。

2026-09-23: 回路図の旧GH6デバッグ端子J8を駆動V2と同じCortex Debug 1.27mm 2×5配列へ変更。1=MCUデジタル3.3VのVTref、2=SWDIO、3/5/9=GND、4=SWCLK、6=SWO、7/8=NC、10=NRST。UARTは独立した2.54mm 1×3スルーホールヘッダJ9（1=GND、2=MCU TX、3=MCU RX）へ変更。3.3Vロジック専用で給電ピンはない。ERC 0、変更箇所以外のネット接続比較を確認済み。詳細は`../../output/kicad-check/v2/odometry/swd-10pin-check.md`と`uart-header-check.md`。

J8の正式MPN・嵌合ケーブル・フットプリントは未確定で、回路図のFootprintは意図的に空欄。V2 PCBは旧GH6のまま、UART J9も未反映で、回路図との同期前に製造してはいけない。

ODOMのU3/U7/U9電源unit Cだけ回路図へ反映済み。ERC 0、XML netlistで6電源pinを確認。PCBの当該6padは未更新なので、回路図からPCBを更新し、電源配線と100nFを確認すること。
