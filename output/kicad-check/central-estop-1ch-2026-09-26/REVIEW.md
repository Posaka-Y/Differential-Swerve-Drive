# E-stop監視1ch化 2026-09-26

ユーザー指定によりU401 LTV-847S 4chをLTV-817S 1chへ変更。ループ監視R401/R402/D401/R409/TP401を保持。ボタン別・予備の16部品とU401 unit2〜4を削除。J401は4pin（1ループ送出、2戻り、3LED24V、4帰路）で型番未確定。J402はコンタクタコイル2線を維持。158実部品。物理NC直列遮断・reset/Hi-Z OFF・明示再アームを維持。

Lite-On製データシートDS-70-96-0016 Rev.Nを入手し、1=A/2=K/3=E/4=C、CTR min50%@5mA、外形を確認。Isolator:LTV-817Sは標準ライブラリあり。SMDIP-4_W9.53mmは候補として割当、購入実物照合は未完了。

S04は未配線。今回ERCや実機試験は実施していない。前回ERCは変更前の結果。ファームは未変更。旧ボタン別GPIO pad6/7は予約。最新PDF S04A/Teensy表を更新しページ10を目視確認。退避before/に保存。原本を初期配置生成器で再生成しない。

資料: https://datasheet.octopart.com/LTV-817-A-Lite-On-datasheet-86641585.pdf （Lite-On発行資料のミラー、LiteOn-LTV8x7.pdfを保存）。メーカー直接URLは拒否応答のため取得失敗。
