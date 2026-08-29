# Video → 3D Research Pipeline

ChatGPT/Base44/GitHub連携用の無料優先パイプラインです。

## 現在の対象
- YouTube: `JFFL7bq18QQ`
- 目的: Blender/MCP系動画を時刻付き文字起こしし、重要フレームを自動撮影して3D自動化の再利用データにする。

## 実行
```bash
python tools/video3d/extract_youtube.py "https://youtu.be/JFFL7bq18QQ" --out output --max-frames 12
```

初回は `yt-dlp`, `imageio-ffmpeg`, `pillow` をユーザー領域へ自動導入します。OpenAI APIや有料クラウドAPIは必須ではありません。

## 出力
- `TRANSCRIPT_RAW.txt`
- `TRANSCRIPT_TIMESTAMPED.txt`
- `TRANSCRIPT_STRUCTURED.json`
- `ERROR_REPORT.json`
- `screenshots/SCREENSHOT_INDEX.json`
- `screenshots/CONTACT_SHEET.jpg`

## 3D側の交換形式
Web/Base44とBlenderの主交換形式はGLB。OBJはデバッグ/テクスチャ参照確認、STLは形状のみ、FBXは既存資産互換用とする。

## QA原則
`命令 → 実行 → 観測 → 修正` を最大5回。原本を上書きせず、各ラウンドの結果とエラーを保存する。
