# 中央基板 Rev.1 人が読む回路図PDF 改訂記録 (2026-09-23)

対象PDF: `output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-23.pdf` (A3横13ページ)。生成器: `tmp/pdfs/build_central_board_rev1_schematic_2026_09_23.py`。2026-09-14版PDF/生成器は保存した。中央KiCad回路図・PCBの変更は本作業に含まれない。

## 変更点

- 5V入力/eFuse、USB diode-OR、6本のPPTC枝を拡大ページへ分離し、部品・ピン・ネットを手入力で追いやすくした。外部`SD-25B-5`の5V入力を維持する。
- **同日最終決定**: CAN1↔ODOM V2、CAN3↔駆動V2、CAN2↔自己給電LED/スイッチングノードの専用CANポートを、すべて横向きJST GH3の`1=COMM_A、2=COMM_B、3=GND`に統一した。5V/GND給電ハーネスは別に維持し、CANのGND線を負荷電流の帰路にしない。J323汎用拡張だけは4pin `+5V_EXP/GND/COMM_A/COMM_B`を維持する。CANトランシーバ、TVS、終端の共通回路を独立ページへ配置した。
- 旧J402 5線の別体`CONTACTOR_DRIVER`案を削除。J402をE228コイル2線の暫定ポート、J403を24V制御入力の暫定ポートとし、中央基板上のU402 `SN74AHCT1G125DBVR`、Q401 `IRLML0100TRPBF`、入力/ゲートプルダウン、ゲート抵抗をピン番号とともに描いた。コイル用ヒューズF401とクランプD4xxは配置候補を示すが、型番/定数は未選定。クランプは破線の未決定素子として描き、短絡配線ではないと注記した。
- E-stop 2個のNC直列接点によるコイル供給遮断を、Teensy/CANを通らない物理経路として記載した。LTV-847Sは診断専用で、チャンネルごとのLED/トランジスタピン対を維持する。`MOTOR_PWR_EN`はTeensy pad 4 / pin 2から中央U402へ直結し、Reset/Hi-Z/LowでQ401 OFFを確認対象とした。
- E228主接点の専用フィードバック監視は載せない。J401の補助接点入力はE-stopボタン用であり、コンタクタ接点監視ではない。制御5Vと中央↔駆動CANはOFF指令後も生かし、駆動MCUから中央へC620応答消失を補助診断として報告する。表示は`OFF指令中・C620応答なし`とし、CAN無応答だけを根拠に`遮断確認済み`としない。中央↔駆動CAN自体が不通なら状態を`不明/古い情報`として区別する。ハードNCループ、Reset/Hi-Z時OFF、明示的な再アームは維持する。
- PJRC公式寸法図に基づき、Teensy 4.1のソケット列中心間を**15.24 mm**に訂正。旧文書の17.78 mmは基板幅であり列間隔ではない。新しい`DifferentialSwerve:Teensy41_Socket_2x24`の使用と、対応する単一48pinシンボルが必要なことを示した。既存中央PCBのJ3/J4位置はTeensyを装着できないため流用しない。
- 外部I/Oの図を「1信号の例」と明示し、J501-J507の実際のpin数・順序を別表にした。13ページ全体で大きな図と注記を分け、ページ番号と参照先を付けた。

## KiCad転記前の未確定事項

1. 専用CANの横向きJST GH3基板側/相手ハウジング/圧着端子/footprintのpin 1向きとケーブル視点を照合する。J323の4pin pin順を流用しない。
2. F401の型番・定格・配置、LED枝の保護、24V制御供給源の最大条件。
3. E228コイルのクランプ方式/極性/定数/実装場所。E-stop時の解放時間、Q401のVDSピークを測定して決める。
4. J402/J403の正式MPN・pin順・キー、コイル線と24V帰路のハーネス。
5. 5V制御GND、24Vコイル帰路、各CAN参照GNDの結合点。コイル電流を静かな制御GNDに直列に流さない。
6. Teensyソケット実部品とランド/ドリルの適合、VUSBパッド取り出し方法。組立前に1:1印刷で確認。
7. F205/F206の実負荷・突入、Matek I2Cのプルアップ電圧、U401のfootprint。
8. U402の電源投入/遮断過渡と`MOTOR_PWR_EN`のReset/Hi-Z時OFFを実機で確認。

部品ピン・仕様の確認元: [TI SN74AHCT1G125](https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf)、[Infineon IRLML0100](https://www.infineon.com/assets/row/public/documents/24/49/infineon-irlml0100-datasheet-en.pdf)、[PJRC Teensy 4.1寸法図](https://www.pjrc.com/teensy/dimensions_teensy41.png)、[PJRCソケット情報](https://www.pjrc.com/store/socket_24x1.html)。他の旧版から維持した回路値は`CENTRAL_BOARD_REV1_KICAD_ENTRY_REFERENCE.md`の出典を参照する。
