# BAR NEVATIA — high-quality 3D design spec (2026-08-30)

## Straight route
Research → prediction board → Japanese residential-grid shell → exterior → interior architecture → furniture → props/equipment → shader/lighting → modular GLB exports → combined GLB → render QA → up to 10 automatic corrections → Base44/GitHub/Drive readback.

## Design basis
- Fictional neighborhood bar, not a copy of a real venue.
- User references: dark/warm wood counter, pendant lights, horizontal wood bands, framed menu cards, beer tap, pump bottles, back-bar blur/glass and colorful machine/soft-drink equipment.
- Residential planning basis: 910 mm shaku module. Working shell: 8 × 10 modules = 7.28 m × 9.10 m, one storey, low gable roof.
- Seating: 8 counter stools + 6 table chairs + 2-person window bench.
- Parking: three east-side stalls; visual study uses ~2.5 m × 6.0 m class dimensions. This is not a site/legal compliance drawing.
- Exterior design vocabulary: dark wood cladding, dark-blue door, frosted street window, modest illuminated sign, visible outdoor AC/utility hardware, planter and parking wheel stops.

## Blender material working presets
These are artistic working presets based on Principled/OpenPBR behavior, not measured material scans.
- Walnut: metallic 0, roughness 0.48–0.62, procedural noise/bump.
- Blackened metal: metallic ~0.8, roughness ~0.36.
- Steel: metallic ~0.92, roughness ~0.33.
- Brass: metallic 1.0, roughness ~0.27.
- Glass: IOR ~1.45, transmission 0.75–1.0, roughness 0.08 clear / ~0.32 frosted.
- Plaster: roughness ~0.86, fine bump.
- Lighting: 2700K-like warm key/cove/pendant appearance plus cool low-level parking fill.

## Modular build system
The Blender script creates six separate collections and exports major modules independently before final assembly:
SHELL / EXTERIOR / INTERIOR / FURNITURE / PROPS / LIGHTING.

Major prop set includes spirits bottles, glassware, tap tower, sink, ice bin, under-counter fridge, soft-drink fridge/cans, soda gun, POS terminal, menu frames, pump bottles, napkins/coasters, signboard, AC units, drainpipe, meter, parking sign and wheel stops.

## QA
- Machine geometry/material checks: mesh count, material count, non-finite transforms, zero scales, empty meshes.
- Visual proxy QA: exterior oblique + counter render every iteration; mean luminance, black ratio and highlight clipping proxy.
- Auto-fixes: exposure and interior fill adjustments; stop when pass after at least 3 rounds or at 10 rounds maximum.
- Final renders: exterior front/oblique, interior counter/wide, top plan.

## Scope
Visual 3D design study only. It does not verify building code, fire code, liquor licensing, accessibility, structural design, ventilation, evacuation, or parking/legal compliance.
