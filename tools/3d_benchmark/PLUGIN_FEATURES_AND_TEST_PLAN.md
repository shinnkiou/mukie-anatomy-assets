# 3D外部スクリプト／プラグイン機能とテスト計画
日付: 2026-08-29

## 命令系統
YouTube/参考資料 → ChatGPT仕様 → 建物骨格 → 反復部品 → 材料/テクスチャ → UV → QA → Base44即時表示 → GLB/OBJ → GitHub/Drive保存。
Blender実機がない工程は adapter として同じ役割をローカル/Base44で実行し、実機接続後にネイティブ add-on へ差し替える。

## 役割分解と評価
| ツール | 主役割 | 今回のテスト | 結果 | Realtime | Review | Texture | Efficiency |
|---|---|---|---|---:|---:|---:|---:|
| Archimesh | 壁・部屋・ドア・窓の建築骨格 | 3建物の箱形骨格・開口adapter | PASS (adapter) | 2 | 4 | 1 | 5 |
| BlenderMCP / BlendMCP | AI↔Blender、scene inspect、Python、viewport screenshot | JSON recipe→表示→QA→修正loop | PASS (adapter) | 5 | 5 | 4 | 5 |
| HAT | asset/model/material/texture QC | units/UV/texture reference/NaN/Inf/export前検査 | PASS (adapter) | 2 | 5 | 5 | 4 |
| Asset Bridge | Poly Haven/AmbientCG無料素材の自動取得 | procedural material adapterでwall/concrete/sign素材供給 | PASS (adapter) | 3 | 2 | 5 | 5 |
| Sverchok | parametric/visual programming | 給油機列・柱・提灯など反復配置adapter | PASS (adapter) | 4 | 4 | 2 | 5 |
| TexTools | UV align/bake/texel density | UV存在、mapped material、欠損画像検査 | PASS (adapter) | 2 | 5 | 5 | 4 |
| BlenderGIS | OSM/GIS/標高/道路・建物context | site plane/road-facing scale/context role | PASS (adapter) | 3 | 3 | 2 | 3 |
| to3D | 単画像→簡易3D | 東京ラーメン/コンビニ参考画像URL 2件 | FAIL: 400 Bad Request | 3 | 2 | 3 | 3 |
| WalkMyPlan | 言語/CAD→歩行可能3D floor plan | 接続・plan list | 接続PASS / model test未実施 | 4 | 5 | 1 | 4 |

## 特徴まとめ
### Archimesh
Blender Extensions公式。Room、Door、Window等の建築要素を生成。v1.2.5はBlender 4.2 LTS以降互換。建物外観の初期箱形生成に最も直接的。
Source: https://extensions.blender.org/add-ons/archimesh/

### BlenderMCP / BlendMCP
socket/MCPでAIとBlenderを双方向接続。object操作、material制御、scene inspection、任意Python、viewport screenshot、Poly Haven等の外部asset連携が可能。BlendMCP系forkにはexecute時のscreenshot、traceback、再接続、telemetry-free等の改善がある。
Sources:
- https://github.com/ahujasid/blender-mcp
- https://github.com/owenpkent/blendmcp

### HAT (Haven Asset Tester)
Poly Havenがasset QCに使用。collection/file/texture path、scale、origin、unit scale、material node、Principled BSDF、UV、texture naming/color space、GLTF export等を検査。
Source: https://github.com/Poly-Haven/HAT

### Asset Bridge
PolyHaven.com / AmbientCG.com等の無料assetをAsset Browserから検索・download/importするBlender add-on。建物本体よりもPBR素材と小物の高速供給に強い。
Source: https://github.com/strike-digital/asset_bridge

### Sverchok
Blenderのvisual programmingによるparametric 3D modeling。Blender 4.2対応releaseがあり、反復・寸法変更・自動配置に向く。
Source: https://github.com/nortikin/sverchok

### TexTools
無料UV/Texture addon。Texture Baking、UV Align/Selection、Texel Densityが主機能。看板や外壁のscale一貫性の検査・修正に向く。
Source: https://github.com/Calinou/textools-blender

### BlenderGIS
Shapefile、raster/geotiff、OSM XML、web map、SRTM elevation、georeferencing等をBlenderへ橋渡し。単体店舗より、東京都の街区・道路背景を大量生成する段階で有効。
Source: https://github.com/domlysz/BlenderGIS

### Tripo / TripoSR
Tripoはtext/image/multi-view→3D、texture、segmentation、retopology、rigging/animation、GLB/OBJ/FBX/STL等を扱える。TripoSRはMITのopen-source single-image reconstructionでA100では0.5秒未満の報告がある。建築精密寸法の主系統ではなく、看板・小物・概形の補助系統候補。
Sources:
- https://www.tripo3d.ai/help/getting-started/what-features-does-tripo-have
- https://github.com/VAST-AI-Research/TripoSR

## 今回の建物テスト
1. コンビニ: Archimesh-style shell + sign/glazing + AssetBridge-style material + TexTools/HAT-style QA。
2. ガソリンスタンド: canopy/service boxを骨格、Sverchok-style repetitionでcolumns/pump islands、HAT-style QA。
3. ラーメン屋: shell + sign/noren texture、反復提灯、ticket machine/menu board、texture front check。

各モデルは v1 massing → v2 identity/sign/opening → v3 details/texture QA の3回。最大5回のうち3回でPASSしたため残り2回はBlender実機viewport/Cycles QAに温存。
