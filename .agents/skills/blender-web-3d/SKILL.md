---
name: blender-web-3d
description: Engineer cinematic, Awwwards-caliber 3D animated websites using modern WebGL, Three.js, React Three Fiber, GLSL shaders, GSAP ScrollTrigger, and post-processing to achieve visual fidelity comparable to Blender renders in real-time browsers.
---

# Blender Web 3D

A skill for engineering cinematic, Awwwards-caliber 3D animated websites using modern WebGL, Three.js, React Three Fiber, GLSL shaders, GSAP ScrollTrigger, and post-processing to achieve visual fidelity comparable to Blender renders in real-time browsers.

## When to Use

Use this skill when the user asks to:
- Create high-end 3D landing pages, portfolio sites, or interactive web experiences.
- Build Three.js, React Three Fiber (R3F), or WebGL scenes with realistic lighting, shadows, and materials.
- Implement custom GLSL vertex and fragment shaders for wave distortion, noise, morphing, or raymarching.
- Connect 3D camera paths and mesh transformations to scroll position using GSAP ScrollTrigger or Lenis.
- Add cinematic post-processing (Bloom, Depth of Field, Chromatic Aberration, Film Grain, Vignette, ACES Tone Mapping).
- Recreate Blender-style materials (frosted glass, metallic iridescence, subsurface scattering, velvet, clearcoat).

## Core Architecture & Stack Selection

Select the simplest architecture that fulfills the requirements without unnecessary dependencies.

- **Standalone HTML/Three.js:** Best for standalone embeds, single-file prototypes, and pure Three.js applications. Load Three.js and GSAP via ES modules from CDNs (`unpkg`/`esm.sh`).
- **React Three Fiber (R3F) + Drei + Postprocessing:** Best for modern React/Next.js web applications, complex component hierarchies, and declarative scene graphs.
- **Animation & Smoothing:** Use GSAP with ScrollTrigger for deterministic scroll timelines. Use Lenis or smooth lerping for butter-smooth camera easing.

## Step-by-Step Implementation Workflow

### 1. Scene Foundation and Camera Setup
Set up a physically accurate environment with proper color management.
- Configure renderer with `antialias: true`, `powerPreference: 'high-performance'`, and alpha transparency where needed.
- Set `renderer.outputColorSpace = THREE.SRGBColorSpace` and `renderer.toneMapping = THREE.ACESFilmicToneMapping` with `toneMappingExposure = 1.0` to prevent washed-out colors.
- Enable shadow mapping: `renderer.shadowMap.enabled = true` and `renderer.shadowMap.type = THREE.PCFSoftShadowMap`.
- Always clamp pixel ratio: `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))` to prevent mobile GPU throttling.

### 2. Blender-Grade Lighting & Environment
High-end 3D realism comes from multi-point lighting contrast, environment reflection, and subtle color grading.
- **Environment Map:** Use high dynamic range image (HDRI) environment lighting via RGBELoader or Drei's `<Environment preset="city" />` to give metallic and glass surfaces realistic reflections.
- **Three-Point Cinematic Setup:**
  - **Key Light:** Directional light with soft shadow bias (`bias = -0.0001`, `mapSize.set(2048, 2048)`).
  - **Fill Light:** Soft ambient light or low-intensity point light with contrasting tint (e.g., warm key light + cool fill).
  - **Rim/Back Light:** High-intensity light positioned behind the subject to define sharp silhouettes.
  - **Contact Shadows:** Place subtle contact shadow planes or use Drei's `<ContactShadows />` beneath objects to ground them.

### 3. Realistic PBR Materials
To achieve Blender-like physical surfaces, leverage `MeshPhysicalMaterial`:
- **Frosted Glass / Refraction:** `roughness: 0.15`, `transmission: 0.95`, `thickness: 1.2`, `ior: 1.5`, `specularIntensity: 1.0`
- **Iridescent / Cyberpunk Metal:** `metalness: 0.9`, `roughness: 0.1`, `iridescence: 0.8`, `iridescenceIOR: 1.3`, `clearcoat: 1.0`
- **Velvet / Soft Fabric:** `sheen: 1.0`, `sheenColor: new THREE.Color('#ff00aa')`, `sheenRoughness: 0.5`

### 4. Custom GLSL Shaders and Procedural Effects
When standard materials cannot achieve organic movement, use `ShaderMaterial` or `CustomShaderMaterial`:
- Use Simplex / Perlin noise in the vertex shader for fluid mesh wave deformation.
- Pass `uTime`, `uMouse`, and `uResolution` uniforms into shaders for dynamic micro-interactions.
- Implement Fresnel equation in fragment shaders for glowing atmospheric edges.
- For particle fields, use `THREE.Points` or `InstancedMesh` with GPU-driven attributes to maintain 60 FPS across tens of thousands of elements.

### 5. Camera Choreography and GSAP Scroll Synchronization
Connect 3D transformations to user scrolling and cursor movement:
- **Smooth Mouse Parallax:** Track normalized mouse coordinates (-1 to 1). In the animation loop, lerp camera or mesh position: `currentPos.lerp(targetPos, 0.05)`.
- **GSAP ScrollTrigger:** Pin the 3D canvas container during page scroll. Create a timeline tied to scroll progress (`scrub: 1` or `scrub: true`). Animate camera position, target coordinates, FOV, and object rotations along keyframe milestones.

### 6. Post-Processing Pipeline
Post-processing gives 3D web scenes a filmic, photorealistic grade:
- **Bloom:** Low threshold (0.8 - 0.95), subtle radius (0.4 - 0.75) for selective emissive glow without overexposure.
- **Chromatic Aberration & Lens Distortion:** Very subtle offset (0.001 - 0.003) on screen peripheries to mimic physical camera lenses.
- **Film Grain / Noise:** Subtle overlay to eliminate color banding on dark gradients.
- **Vignette:** Darkened edges to draw focus to central 3D heroes.

### 7. Performance and Lifecycle Optimization
- Dispose of geometries, materials, textures, and render targets upon component unmount or route transition.
- Merge static geometries using `BufferGeometryUtils.mergeGeometries`.
- Use `InstancedMesh` for repeated objects to minimize draw calls to a single call.
- Provide a sleek, animated HTML/CSS loading screen with progress percentage while assets load.

## Complete Self-Contained Implementation Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cinematic 3D Experience</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #08080a; color: #f0f0f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; overflow-x: hidden; }
    #webgl-canvas { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 1; pointer-events: none; }
    .content { position: relative; z-index: 2; pointer-events: auto; }
    section { height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 0 10vw; }
    h1 { font-size: clamp(2.5rem, 6vw, 5rem); font-weight: 800; letter-spacing: -0.02em; max-width: 800px; line-height: 1.1; }
    p { margin-top: 1.5rem; font-size: 1.25rem; color: #a0a0b0; max-width: 500px; }
  </style>
</head>
<body>
  <canvas id="webgl-canvas"></canvas>
  <div class="content">
    <section id="hero">
      <h1>Sculpted in Code.</h1>
      <p>Interactive 3D geometry rendered with real-time physical lighting and cinematic post-processing.</p>
    </section>
    <section id="features">
      <h1>Fluid Materials.</h1>
      <p>Refractive glass and metallic iridescence reacting smoothly to your scroll trajectory.</p>
    </section>
    <section id="outro">
      <h1>Blender Quality.</h1>
      <p>Seamless 60fps rendering in modern web browsers.</p>
    </section>
  </div>
  <script type="module">
    import * as THREE from 'https://esm.sh/three@0.160.0';
    import { EffectComposer } from 'https://esm.sh/three@0.160.0/examples/jsm/postprocessing/EffectComposer.js';
    import { RenderPass } from 'https://esm.sh/three@0.160.0/examples/jsm/postprocessing/RenderPass.js';
    import { UnrealBloomPass } from 'https://esm.sh/three@0.160.0/examples/jsm/postprocessing/UnrealBloomPass.js';
    import gsap from 'https://esm.sh/gsap@3.12.5';
    import { ScrollTrigger } from 'https://esm.sh/gsap@3.12.5/ScrollTrigger.js';

    gsap.registerPlugin(ScrollTrigger);

    const canvas = document.getElementById('webgl-canvas');
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x08080a, 0.05);

    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 0, 6);

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0x7090ff, 2.5);
    keyLight.position.set(5, 5, 5);
    keyLight.castShadow = true;
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0xff5533, 2.0);
    rimLight.position.set(-5, -2, -3);
    scene.add(rimLight);

    // Hero Object (Torus Knot with Physical Glass/Metallic Material)
    const geometry = new THREE.TorusKnotGeometry(1.2, 0.35, 200, 32);
    const material = new THREE.MeshPhysicalMaterial({
      color: 0x222233,
      metalness: 0.2,
      roughness: 0.1,
      transmission: 0.85,
      thickness: 1.5,
      ior: 1.52,
      clearcoat: 1.0,
      clearcoatRoughness: 0.1,
      reflectivity: 0.9,
    });
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    // Post Processing
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      0.4, // Strength
      0.5, // Radius
      0.85 // Threshold
    );
    composer.addPass(bloomPass);

    // GSAP Scroll Animations
    gsap.timeline({
      scrollTrigger: {
        trigger: '.content',
        start: 'top top',
        end: 'bottom bottom',
        scrub: 1.5
      }
    })
    .to(mesh.rotation, { x: Math.PI * 2, y: Math.PI * 3, ease: 'none' }, 0)
    .to(mesh.position, { x: 1.8, y: -0.5, z: 1, ease: 'power1.inOut' }, 0)
    .to(camera.position, { z: 4.5, ease: 'power1.inOut' }, 0.5);

    // Smooth Mouse Interaction
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    window.addEventListener('mousemove', (e) => {
      mouse.targetX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouse.targetY = (e.clientY / window.innerHeight - 0.5) * 2;
    });

    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
      composer.setSize(window.innerWidth, window.innerHeight);
    });

    const clock = new THREE.Clock();
    function animate() {
      requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      mesh.rotation.z = elapsedTime * 0.1;
      camera.position.x = mouse.x * 0.5;
      camera.position.y = -mouse.y * 0.5;
      camera.lookAt(scene.position);

      composer.render();
    }
    animate();
  </script>
</body>
</html>
```

## Gotchas & Troubleshooting
- **Blown-out Bloom:** Never set Bloom strength above 1.0 or threshold below 0.7 without testing across multiple screens. Use selective bloom layers for specific glowing elements rather than applying heavy bloom to the whole scene.
- **Mobile Performance Drops:** Always clamp `pixelRatio` to 2. On low-end devices, disable expensive passes like Screen Space Reflections or Depth of Field and reduce shadow map dimensions to 1024.
- **Transparency Sorting Glitches:** When rendering overlapping transparent meshes, set `depthWrite: false` or manually manage `renderOrder` to avoid clipping artifacts.
- **Texture Banding:** Always ensure 8-bit gradients have subtle dither or film grain applied in post-processing to avoid visible stepping.
