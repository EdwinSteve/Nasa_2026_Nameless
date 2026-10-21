---
name: SURCO Agritech System
colors:
  surface: '#f7f9ff'
  surface-dim: '#cfdbeb'
  surface-bright: '#f7f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#edf4ff'
  surface-container: '#e3efff'
  surface-container-high: '#dde9f9'
  surface-container-highest: '#d7e4f3'
  on-surface: '#111d28'
  on-surface-variant: '#414941'
  inverse-surface: '#26323d'
  inverse-on-surface: '#e8f2ff'
  outline: '#717970'
  outline-variant: '#c1c9be'
  surface-tint: '#3a6843'
  primary: '#043616'
  on-primary: '#ffffff'
  primary-container: '#1f4d2b'
  on-primary-container: '#8cbd92'
  inverse-primary: '#a0d3a6'
  secondary: '#176d32'
  on-secondary: '#ffffff'
  secondary-container: '#a2f6ac'
  on-secondary-container: '#207338'
  tertiary: '#4d2100'
  on-tertiary: '#ffffff'
  tertiary-container: '#6f3300'
  on-tertiary-container: '#ff974e'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#bbefc0'
  primary-fixed-dim: '#a0d3a6'
  on-primary-fixed: '#00210b'
  on-primary-fixed-variant: '#22502d'
  secondary-fixed: '#a2f6ac'
  secondary-fixed-dim: '#87d992'
  on-secondary-fixed: '#002109'
  on-secondary-fixed-variant: '#005321'
  tertiary-fixed: '#ffdbc7'
  tertiary-fixed-dim: '#ffb689'
  on-tertiary-fixed: '#311300'
  on-tertiary-fixed-variant: '#733500'
  background: '#f7f9ff'
  on-background: '#111d28'
  surface-variant: '#d7e4f3'
typography:
  display-metric:
    fontFamily: Nunito Sans
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 52px
    letterSpacing: -0.02em
  headline-xl:
    fontFamily: Nunito Sans
    fontSize: 36px
    fontWeight: '800'
    lineHeight: 44px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Nunito Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Nunito Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-sm:
    fontFamily: Nunito Sans
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 28px
  body-xl:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 30px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 26px
  label-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 18px
    letterSpacing: 0.04em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-mobile: 0.75rem
  margin: 1.25rem
  margin-mobile: 1rem
  space-xs: 0.375rem
  space-sm: 0.75rem
  space-md: 1.25rem
  space-lg: 1.75rem
  space-xl: 2.5rem
---

## Brand & Style

This design system is tailored for smallholder coffee and specialty crop farmers operating in high-sunlight rural settings across the Andean slopes of Neiva and the Huila department. The visual tone balances practical utility with community warmth, engineered specifically for outdoor visibility, one-handed field operation, and immediate cognitive clarity under direct glare.

The visual aesthetic sits at the intersection of **Tactile Field Utility** and **Warm Modernism**:
- **Tactile Warmth:** Natural, earth-grounded tones avoid clinical sterile tech aesthetics. Instead, interfaces feel resilient, tangible, and respectful of agrarian labor.
- **High-Sunlight Legibility:** Prioritizes optical separation, high-contrast text ratios, large typographic metrics, and oversized interactive components designed for weathered hands, moisture, and variable phone screen qualities.
- **Cognitive Simplicity:** Complex agronomic intelligence (weather data, satellite indicators, soil metrics) is flattened into immediate, scannable visual indicators and badges.

## Colors

The color system is optimized for extreme contrast under daylight and solar exposure, using an earthy, natural spectrum directly derived from the Huila agricultural ecosystem:

- **Primary (`#1F4D2B` - Deep Field Green):** Serves as the primary operational anchor for headers, primary actions, and navigational framing. Provides deep visual stability.
- **Secondary / Success (`#6DBE7A` - Fresh Leaf Green):** Applied to crop health indicators, optimal soil moisture states, confirmation banners, and positive harvest trajectories.
- **Accent / Alert (`#E8833A` - Sun Orange):** Applied to pest alerts, drought flags, critical harvest schedules, and urgent notifications. High chromacity guarantees instant recognition.
- **Water / Rain (`#4A90C8` - Sky Blue):** Reserved exclusively for rainfall estimates, water storage, evapotranspiration, and irrigation data.
- **Soil / Earth (`#8B5E34` - Soil Brown):** Designates substrate data, fertilizer schedules, compost metrics, and physical land partitions.
- **Canvas (`#F7F3EA` - Warm Cream):** Minimizes optical fatigue and glare caused by harsh pure whites when viewing devices in open fields.
- **Surface (`#FFFFFF` - Crisp White):** Clean containment for cards, metric sheets, and actionable panels.
- **Typography Main (`#14202B` - Dark Ink):** Delivers ultra-high contrast (exceeding WCAG AAA) against cream and white surfaces.
- **Typography Muted (`#4B5B67` - Slated Field Dust):** Retains strict legibility for metadata, units, and timestamps without muddying visual hierarchy.

## Typography

Typography is calibrated to solve readability issues in harsh tropical sunlight, low-cost device screens, and rapid scanning while walking across uneven terrain.

- **Headlines (`Nunito Sans`):** Rounded terminals evoke an approachable, communal tone without sacrificing visual weight. Used for lot names, critical alerts, and metric headers.
- **Body & Data (`Inter`):** Engineered with open counters, tall x-height, and neutral geometry. The minimum body font size is restricted to **18px** across the board to ensure legibility when holding devices at arm's length.
- **Telemetry & Numbers:** Large numerical metrics scale from `32px` to `48px` using heavy weights (`700`/`800`) to communicate vital crop metrics (e.g., rainfall millimeters, soil humidity percentages, market pricing per arroba) at a glance.

## Layout & Spacing

The layout is built primarily around a mobile-first fluid single-column hierarchy, scaling to an expansive multi-column grid on tablets or kiosk hardware at rural cooperatives.

- **Field-Ready Density:** Rather than tight information packing, the system employs generous breathing room. This prevents accidental mis-taps when screens are smudged with dirt or used with wet hands.
- **Touch Target Threshold:** All tap boundaries enforce an absolute minimum dimension of **56px × 56px**, regardless of the visual glyph or text size within.
- **Rhythm:** Spacing follows comfortable steps centered around `1.25rem` (`20px`) baseline paddings within cards and content containers, creating consistent vertical cadences across complex operational forms.

## Elevation & Depth

Because subtle shadows wash out entirely under direct outdoor sunlight, this design system avoids relying on low-contrast blurred elevation:

- **Structural Outlines:** Depth is primarily established through structured containment: pure white card surfaces placed on the warm cream canvas, reinforced by clean `1.5px` borders in neutral tint (`rgba(20, 32, 43, 0.08)`).
- **Physical Grounding:** Critical actionable surfaces (e.g., summary trays, active inputs, primary floating action bars) use a single tactile, directional shadow: `0px 4px 12px rgba(20, 32, 43, 0.08)`.
- **Active State Projection:** Pressed states depress visually rather than floating higher, providing immediate physical feedback that a command has been registered.

## Shapes

The design system embraces a high-radius, pill-influenced shape language (`roundedness: 3`):

- **Cards and Panels:** Standard containers carry an organic `1.25rem` (`20px`) border radius. This softens the interface, creating friendly framing for soil, crop, and weather figures.
- **Interactive Controls:** Buttons, chips, status pills, and numeric badge indicators feature full pill geometry (`9999px` / fully rounded caps), accentuating physical affordance and fingertip comfort.
- **Nested Shapes:** Internal nested elements (e.g., sub-cards, visual bars) scale down proportionally to `0.75rem` (`12px`) to maintain harmonious corner curves.

## Components

### Buttons
- **Primary Action:** Solid Deep Field Green (`#1F4D2B`) background with pure white text (`#FFFFFF`), full pill radius, minimum height of `56px`, and horizontal padding of `28px`. Font is `Inter` bold 18px.
- **Secondary Action:** Transparent fill with a `2px` solid Deep Field Green border and `#1F4D2B` text. Minimum height `56px`.
- **Alert / Destructive:** Solid Sun Orange (`#E8833A`) or deep rust red background with white typography for irreversible actions or immediate pest escalation triggers.

### Chips & Badges ('Dato NASA')
- Compact pill-shaped metadata markers designed for data provenance, such as satellite feeds, soil sensors, or cooperative advisories.
- **Style:** Fully rounded caps, padding of `6px 14px`.
- **Telemetry Accent:** NASA/satellite badges utilize a pale Sky Blue tint (`#EBF3FA`) background with Sky Blue text (`#4A90C8`) and a bold micro-label `label-sm` font.
- **Organic Quality:** Soil or moisture status chips combine soft organic tints with dark readable ink.

### Cards
- Surface color is pure `#FFFFFF` against the `#F7F3EA` cream background.
- Standard border-radius is `20px` with an internal padding of `20px` (`1.25rem`).
- Metric cards feature prominent Nunito Sans numeric headings (`36px` to `48px`) paired with Inter 18px descriptive subtexts to allow fast, distant scanning.

### Input Fields
- Minimum height of `60px` with a `16px` corner radius.
- Background uses pure white with an explicit `1.5px` border in `#4B5B67` (darkened to `#1F4D2B` on focus).
- Text size is locked to `18px` minimum to avoid iOS zoom and guarantee readability while inputting farm data in the field.

### Checkboxes & Radio Buttons
- Oversized hit boxes: visual controls are `28px × 28px` centered inside a minimum `56px × 56px` touch area.
- Checked state uses primary Deep Field Green `#1F4D2B` with heavy check indicators to remain legible under glare.

### Data Tiles & Metric Trackers
- Specialized dual-tier cards tailored for weather projections (precipitation, UV exposure, rainfall accumulations).
- High visual contrast separating the numerical magnitude (e.g., "18 mm") from its agronomic evaluation (e.g., "Adecuado para siembra").