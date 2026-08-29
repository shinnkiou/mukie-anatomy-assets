# YouTube動画 文字起こし実行プロンプト

対象URL: https://youtu.be/JFFL7bq18QQ?si=RM-3soCDW_VYDVNB

目的は、動画を後続の3D/Blender自動化へ再利用できるデータへ変換すること。字幕/音声、時刻、操作、結果、失敗、修正、使用ツールを対応付ける。

1. 動画ID・タイトル・長さ・チャンネル・公開日・説明欄を取得。
2. YouTube字幕を列挙し、日本語公式/自動字幕を最優先。
3. 字幕がない場合のみローカルWhisper系へフォールバック。有料クラウドAPIは初期経路にしない。
4. `TRANSCRIPT_RAW.txt`、`TRANSCRIPT_TIMESTAMPED.txt`、`TRANSCRIPT_STRUCTURED.json`、`VIDEO_INFO.json` を生成。
5. 自動字幕の重複は意味を壊さない範囲で除去。聞き取れない語を勝手に補完しない。
6. Blender/MCP/AI/プロンプト/モデル/リグ/アニメーション/マテリアル/テクスチャ/レンダー/スクリーンショット等を抽出。
7. JSONイベントへ start_sec/end_sec/transcript/action/tool/result/error/correction/reusable_knowledge を保存。
8. 「再実装すべき機能」「失敗点」「改善点」を最後にまとめる。

品質条件: UTF-8、推測は確認済み情報と分離、途中成果を消さない、エラーは `ERROR_REPORT.json` に保存、再実行で既存成果を不用意に破壊しない。
