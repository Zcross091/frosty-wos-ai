---
name: 3d-interactive-ui-design
description: Guidelines and patterns for developing high-performance, visually attractive 3D interactive user interfaces with rich color dynamics (multicolor vibrant and monochromatic single-color palettes).
version: 1.0.0
---

# 3D Interactive UI Development Skill

## Role & Mission
Act as an expert Creative Technologist and Senior Frontend Architect. Design and implement responsive, visually striking, performant WebGL/3D-powered interfaces that blend spatial 3D elements with flat UI/UX ergonomics.

---

## 1. Core Architecture & Tech Stack

* **3D Canvas & Engine:** Three.js / React Three Fiber (`@react-three/fiber`), `@react-three/drei`, or Spline runtime.
* **Animation & Physics:** Framer Motion / `@react-spring/three`, GSAP, Rapier physics (`@react-three/rapier`).
* **Styling & Structure:** Tailwind CSS, CSS Custom Properties (Tokens), Glassmorphism / Backdrop filters.
* **Icons & Typography:** Lucide React / Tabler Icons, Inter / Space Grotesk / Geist font families.

---

## 2. Visual Themes & Color Schemes

### A. Multicolor Dynamic (Vibrant / Holographic / Neo-Digital)
* **Palette Structure:**
  * Background: Deep slate/obsidian (`#0a0b10`) or crisp high-contrast off-white (`#f8fafc`).
  * Accents: Triple gradient pairings (e.g., Electric Cyan `#06b6d4`, Hyper Violet `#8b5cf6`, Hot Pink `#ec4899`).
* **3D Material Techniques:**
  * `MeshPhysicalMaterial` with transmission (`0.85`), roughness (`0.1`), metalness (`0.1`), and clearcoat (`1.0`).
  * Iridescent and Fresnel shaders to cast rainbow specular highlights upon rotation.

### B. Single-Color Monochromatic (Sleek Minimalist / Neumorphic / Brutalist)
* **Palette Structure:**
  * Base Hue: Pick a single base color (e.g., Emerald `#10b981`, Deep Cobalt `#1e40af`, or Titanium Amber `#f59e0b`).
  * Value Scale: 90% lightness variation (from 50-tint to 950-shade) of that exact hue.
* **3D Material Techniques:**
  * Focus on light play, ambient occlusion (SSAO), directional shadows, and matte/satin finishes (`roughness: 0.3-0.5`).
  * Rim lighting / backlighting with identical hue at higher intensity to silhouette objects.

---

## 3. UI Layering & Spatial Composition

* **Z-Index Layering:**
  * `Layer 0 (Canvas):` `<Canvas>` container locked to `fixed inset-0 pointer-events-none` (enable `pointer-events-auto` on mesh targets).
  * `Layer 1 (Atmosphere):` Ambient particle systems, floating glowing orbs, soft noise textures.
  * `Layer 2 (Content Layer):` Glassmorphic panels (`backdrop-blur-md bg-white/5 border border-white/10`).
  * `Layer 3 (HUD / Overlays):` Floating toolbars, modal sheets, interactive 3D gizmos.
* **Cursor & Viewport Interaction:**
  * Parallax camera drift mapped to normalized mouse coordinates `(x: [-1, 1], y: [-1, 1])`.
  * Raycasting hover states on 3D objects with spring-based scaling (`scale: 1.0 -> 1.15`).

---

## 4. Performance & Engineering Standards

1. **Geometry Optimization:** Keep low-poly counts (< 50k vertices for UI models); use instanced meshes (`<Instances>`) for repeated particles or cards.
2. **Lighting Efficiency:** Limit active dynamic shadow-casting lights to **1 directional light**. Use environment maps (`<Environment preset="city" />`) for ambient reflections.
3. **Frame Budget:** Target steady 60–120 FPS. Clamp Pixel Ratio:
   ```jsx
   <Canvas
     dpr={[1, 2]}
     performance={{ min: 0.5 }}
     gl={{ powerPreference: "high-performance", antialias: true }}
   >
   ```
4. **Graceful Degradation:** Detect WebGL support and provide CSS 2.5D fallbacks for low-power or mobile devices.

---

## 5. Golden Rules for the AI Generator

* **Never ship static blocks:** Always pair 3D canvases with reactive mouse/touch tilt, subtle idle float rotations, and animated entry transitions.
* **Ensure Readability:** Never place busy 3D geometry directly behind low-contrast body text. Always soften backgrounds with blur masks or vignettes.
* **Clean State Management:** Keep 3D animation ticks isolated inside `useFrame` loops to prevent triggering React DOM re-renders.
