# 中央回路 PDF可読性・Teensy用途ラベル 2026-09-29

## 成果物

- `output/pdf/CENTRAL_BOARD_REV1_SCHEMATIC_2026-09-29.pdf`：A3横15ページ、画像0、文字/配線を直接描画。旧9/26版は保持。
- `S02B_star_teensy-1.kicad_sch`：GPIO用途global labelを追加し、予約NCを明示。C212とそのGNDだけ表示干渉回避のため移動。
- `central-teensy-pinmap.json`：GPIO4/5の廃止済みE-stop個別監視を予約NCへ訂正。

## 検証

- `before/`へ作業前プロジェクトを退避。比較基準は今回開始時の保存版。
- 新規用途global label30個（電源含む）、C212移動先の3V3ラベル1個。全使用40padのネット名と予約8padの未接続をnetlistで確認。
- 元の複数端子ネットは全て保持され、分断0。新しい接続はTeensyと既存CAN1/2/3 TX/RX、Teensy pad15/C212の3V3網への合流。`net-audit.json`参照。
- `READ_SW_N`2箇所を正本の`REARM_SW_N`へ統一。C212の3V3/GNDの接続維持を照合。
- ERC217→194。変更前: pin_not_connected196、isolated_pin_label6、pin_not_driven6、power_pin_not_driven6、unconnected_wire_endpoint3。
- 変更後: pin_not_connected159、isolated_pin_label23、pin_not_driven3、power_pin_not_driven6、unconnected_wire_endpoint3。ラベルは用途予約も示すため、相手側が未配線の23件を残す。規則/除外の緩和なし。最終回路/製造合格ではない。
- PDF全15ページをPNGへ描画し、全体と個別ページを目視確認。本文/端子10〜23pt。テキスト境界のページ外0、テキスト同士の矩形重なり0、全15ページに画像埋込みなし。主要信号/端子/実測値の抽出を確認。
- KiCad SVGのTeensy部を拡大描画し、用途ラベルとNC予約表示、C212干渉解消を確認。

## 残件

- GPIO4pin×4組はPDF p14に反映、S05は旧J507 10pinのまま。部品型番/footprintは図面照合後に更新。
- 保存済みCAN番号はU/D/R/SW311・312・313、専用J311〜J316。PDFはこれに合わせた対応表。旧転記表とは番号が異なる。設計要求のJ323は現保存版にない。
- PMD22-03-24Rの型番・端子・X1-X2押下時点灯、20V/0.2W・24V/約0.3Wはユーザー実測情報。メーカーの該当内部結線図は今回検索で取得できなかった。11-12使用方針と実測による接点確認を区別。
- LED枝保護、F401、クランプ、帰路結合点、USB取出し、正式コネクタは未確定。24V/0.3Wは約12.5mA、1個測定なら2個で約25mA。
- 本PDFは設計リファレンスであり、手配線途中のKiCad全ネットの完全一致出力ではない。今回の回路変更範囲はS02Bの用途ラベル/表示整理のみ。

KiCadエディタで旧保存版を開いている場合は、外部変更を再読込してから編集を続ける。
