# BladeBound Phase 0: Aurora Frost Design Contract

## 0. Research Log

Phase 0 is a greenfield frontend foundation for On Ice / BladeBound. Its single job is to prove the visual, routing, preference, accessibility, and rendering architecture before product content or business behavior arrives.

- **Brief synthesis:** The approved brief is the primary visual contract: expressive Aurora Frost 3D on public pages, quiet flat chrome in admin, complete light and dark themes, and a motion preference that respects the operating system until the user chooses otherwise.
- **Embedded reference lane:** The supplied frontend references were used for anti-template discipline, material layering, accessible motion, responsive composition, and React performance. The intended visual family combines cold-luxury optical materials with the precision of skate-blade machining. No outside brand is copied.
- **Real-product screen lane:** Skipped. This task prohibits Gemini-backed services and provides a decision-complete visual brief; Phase 0 does not need live-product scraping to resolve layout or content.
- **Imagen / Gemini concept lane:** Explicitly skipped because the task prohibits Gemini, Imagen, Stitch, and Gemini-dependent services. No generated imagery is used.
- **Local visual research:** The subject vocabulary is ice refraction, aurora light, sharpened steel, rink tracings, and cold atmospheric depth. These inform tokens and primitives rather than decorative stock imagery.
- **Tooling note:** Tailwind is intentionally not used. Authored CSS variables are the more direct contract for optical material layers, theme parity, and a small Phase 0 surface.

## 1. Direction and Principles

### Design read

Aurora Frost is a cold-luxury digital environment for skaters and operators. It should feel engineered rather than magical: translucent ice, silver blade edges, deep navy distance, and aurora color captured inside material rather than sprayed on top.

### Design dials

- **Public variance:** 7/10. Offset composition, generous fields, and one persistent atmospheric scene.
- **Public motion:** 5/10. A slow environmental drift and short state transitions. No scroll spectacle in Phase 0.
- **Public density:** 3/10. Content-minimal foundation stubs with deliberate negative space.
- **Admin variance:** 3/10. Predictable rails, compact headers, and stable content geometry.
- **Admin motion:** 2/10. Feedback only, under 200ms.
- **Admin density:** 7/10. Efficient chrome without fabricated operational data.

### Signature

The signature is a **blade-cut aurora plane**: an abstract field of translucent ice planes and silver arcs that sits behind every public route. It conveys the product world without pretending to be product photography or a finished commerce experience.

### Aesthetic risk

The public interface uses high-key near-white glass in both themes instead of the common neon-on-black aurora treatment. Depth comes from rim lighting, layered translucency, and navy atmospheric falloff. This keeps the direction distinctive and legible.

## 2. Color System

All UI color is semantic. Aurora color is atmospheric and never used for body copy.

### Core ramps

| Token | Light | Dark | Use |
|---|---:|---:|---|
| `--ice-0` | `#f8fcff` | `#dce9f2` | highest highlight |
| `--ice-1` | `#edf6fb` | `#b8cad8` | panel fill / muted text in dark |
| `--ice-2` | `#d7e7f0` | `#70889b` | borders and disabled detail |
| `--navy-0` | `#e8f0f6` | `#172637` | soft atmospheric field |
| `--navy-1` | `#183049` | `#0b1725` | primary text / dark surface |
| `--navy-2` | `#0a1b2e` | `#06101c` | strongest text / page depth |
| `--silver-0` | `#ffffff` | `#f2f7fa` | specular edge |
| `--silver-1` | `#b9c9d4` | `#91a5b5` | blade edge / secondary border |
| `--aurora` | `#2c8f96` | `#67c5c3` | single interactive accent |
| `--aurora-soft` | `#8bd4d2` | `#225b64` | atmosphere only |
| `--critical` | `#a33b4b` | `#ff9aab` | failure state only |

### Theme surfaces

- Light canvas: `#eaf3f8`, cooled with blue-grey radial atmosphere.
- Dark canvas: `#071320`, lifted with desaturated cyan haze.
- Primary text targets at least 7:1 against the canvas where practical.
- Interactive accent targets at least 4.5:1 for normal text and 3:1 for large text or non-text controls.
- Public and admin share semantic color names but not material intensity.
- One accent is locked across both tiers: aurora teal.

## 3. Typography

- **Display:** Cormorant Garamond, variable/fallback weights 500 and 600. Used only for public route titles and the wordmark. Its sharp terminals echo blade profiles.
- **Body and UI:** Inter, weights 400, 500, 600, and 700. The brief explicitly requires Inter; it supports quiet, compact admin controls.
- **Fallbacks:** display falls back to Georgia; body falls back to system sans-serif.
- **Loading:** fonts are locally package-resolved through `@fontsource` and use swap behavior.

### Type tokens

- `--type-display-xl`: clamp(3rem, 8vw, 6.5rem), line-height 0.92, tracking -0.035em.
- `--type-display-md`: clamp(2.4rem, 6vw, 4.8rem), line-height 0.96.
- `--type-title`: clamp(1.7rem, 3vw, 2.5rem), line-height 1.05.
- `--type-body`: 1rem, line-height 1.65, maximum measure 64ch.
- `--type-small`: 0.8125rem, line-height 1.45.
- `--type-label`: 0.75rem, line-height 1.2, tracking 0.08em; no decorative all-caps section eyebrows.

## 4. Spacing, Geometry, and Responsive Rules

### Spacing tokens

`--space-1` 0.25rem; `--space-2` 0.5rem; `--space-3` 0.75rem; `--space-4` 1rem; `--space-5` 1.5rem; `--space-6` 2rem; `--space-7` 3rem; `--space-8` 4.5rem; `--space-9` 7rem.

### Radius tokens

- `--radius-control`: 0.75rem.
- `--radius-panel`: 1.5rem.
- `--radius-shell`: 2rem.
- Buttons use control radius, panels use panel radius, and modal shells use shell radius. Pills are reserved for binary segmented controls only.

### Layout

Public desktop:

```text
┌ persistent top bar ────────────────────────────────┐
│ wordmark               route nav      preferences │
├───────────────────────────────────────────────────┤
│                         atmospheric 3D field       │
│      route title                                  │
│      short foundation copy     offset glass panel │
│      one relevant action                           │
└───────────────────────────────────────────────────┘
```

Admin desktop:

```text
┌ rail ─────────┬ compact command header ────────────┐
│ admin routes  │ theme / motion / account controls │
│               ├───────────────────────────────────┤
│               │ flat dense content surface        │
└───────────────┴───────────────────────────────────┘
```

- Page content max width: 90rem; reading measure: 64ch.
- At 768px and below, public offset grids collapse to one column and nav becomes a compact menu.
- Admin rail becomes a horizontal, scrollable route strip. No content is hidden behind hover.
- At 375px, minimum page gutter is 1rem and all controls maintain a 44px target.
- Public route hero content fits the first dynamic viewport with title, copy, and action visible.

## 5. Depth and Frosted Material

`FrostedGlassPanel` is a material stack, not a blur utility.

1. **Fill:** translucent theme surface plus a subtle vertical ice gradient.
2. **Diffusion:** backdrop blur and saturation where supported.
3. **Rim:** outer low-contrast border and a bright inset top edge.
4. **Sheen:** restrained radial highlight positioned above the content plane.
5. **Depth:** navy-tinted ambient shadow plus a shallow inner shadow.
6. **Fallback:** an opaque, high-contrast surface when transparency or blur is unavailable.

Depth tokens:

- `--shadow-frost`: 0 24px 80px rgba(7, 23, 38, 0.18).
- `--shadow-float`: 0 12px 32px rgba(7, 23, 38, 0.14).
- `--rim-light`: inset 0 1px rgba(255, 255, 255, 0.72).
- `--rim-dark`: inset 0 -1px rgba(12, 39, 60, 0.12).

Admin uses opaque fills, one-pixel borders, no backdrop blur, and only `--shadow-float` for the authentication modal.

## 6. Rendering and Motion Tiers

### Public full tier

- One persistent, reusable `AuroraScene` mounts behind public route content.
- The canvas is `aria-hidden`, pointer-events none, and outside the reading order.
- Motion is slow transform/opacity or render-loop scene motion with no user task attached.
- Route changes do not recreate a separate canvas for each page.

### Public quiet tier

- Activated by reduced-motion preference, explicit motion-off choice, unavailable WebGL, or a scene error.
- Replaces Canvas with a static authored-CSS atmosphere built from gradients and blurred planes.
- Maintains comparable contrast and visual balance without animation.

### Admin quiet tier

- Never imports or mounts Canvas, Three.js, parallax, or scroll-triggered motion.
- Interaction transitions are opacity, color, and transform only, 160ms default and never over 200ms.
- Motion preference remains globally controllable, but admin chrome stays quiet in either state.

### Motion tokens

- `--duration-fast`: 120ms.
- `--duration-ui`: 160ms.
- `--duration-route`: 420ms public only.
- `--ease-out`: cubic-bezier(0.16, 1, 0.3, 1).

## 7. Preferences and Accessibility

- Theme values: `light`, `dark`, `system`.
- Motion values: `full`, `reduced`, `system`.
- Namespaced persistence keys: `bladebound.preference.theme` and `bladebound.preference.motion`.
- A pre-React script in `index.html` resolves stored values before first paint.
- Without a stored motion choice, `prefers-reduced-motion: reduce` determines the initial rendered tier.
- A stored user choice overrides the media default.
- Preferences store no identity, bearer token, or authentication material.
- Focus rings use a two-layer aurora/surface outline and remain visible in both themes.
- Modal focus is trapped, Escape closes, backdrop click closes, and focus returns to the opener.
- Dialog labels, controls, and route landmarks use semantic HTML.
- The 3D scene is decorative only and never the sole carrier of information.
- Static fallback is the accessibility baseline, not a degraded error screen.

## 8. Reusable Primitives and States

### `FrostedGlassPanel`

Public content container with layered material. States: default and elevated. It never encodes business status.

### `AuroraScene` and `AuroraFallback`

Decorative public atmosphere with explicit full/static tier behavior and an error boundary.

### `PreferenceControls`

Global theme and motion controls. Labels communicate the resulting mode. Controls are available in both layouts.

### `PublicLayout`

Persistent public chrome, decorative atmosphere, route outlet, global controls, and authentication trigger.

### `AdminLayout`

Compact navigation, global controls, route outlet, and no 3D dependency in its module graph.

### `AuthModal`

An accessible modal shell for future cookie-backed authentication. Phase 0 copy states that sessions will use secure HttpOnly cookies. There is no auth route, API call, credential submission, or local token storage.

### Route stubs

Each route states its name and “Phase 0 foundation.” Stubs contain no fabricated products, orders, users, payments, or operational metrics. Optional media areas are neutral descriptive blur blocks only.

### Shared state cycle

- Loading: route-level Suspense uses a stable atmospheric shell and short text status.
- Empty: stubs explain that content begins in Phase 1.
- Error: route and scene boundaries use direct recovery copy and a retry action where meaningful.
- Success: preference changes are reflected immediately by control state and document attributes.

## 9. Architecture Contract

- Vite + React + strict TypeScript.
- HashRouter with the exact approved route map only.
- Route modules use `React.lazy` and Suspense.
- CSS variables and authored CSS; no Tailwind.
- Context owns preference and modal UI state. Auth state reserves a future cookie-session status but never stores a token.
- Three.js packages are isolated to public scene modules.
- Production must not include developer inspection tools. Any React inspection package must be development-only and dynamically gated.
- Source modules stay below 250 pure lines and own one clear responsibility.

## 10. Accepted Phase 0 Debt

- Route pages are intentionally content-minimal and share a typed stub composition.
- No real product imagery, data, API client, commerce flow, admin form, or authentication behavior exists.
- The WebGL capability check is pragmatic and client-side; broader device performance adaptation belongs to Phase 1.
- Font packages add local assets but full subset optimization is deferred until real content establishes glyph requirements.
- The admin mobile information architecture is foundational, not validated against real operational workflows.
- Playwright provides smoke coverage; full visual-regression baselines are deferred until Phase 1 content stabilizes.
- React Grab, React Scan, and React Doctor are development dependencies. Grab and Scan are dynamically loaded only in Vite development when the local opt-in key `bladebound.devtools` is `on`, which keeps admin Canvas-free by default and excludes them from production output. React Doctor remains a CLI-only diagnostic.

## 11. Phase Boundary

Phase 0 ends when the design contract, exact route shells, preference bootstrap, public full/static rendering tiers, admin isolation, reusable primitives, tests, and production build are verified. Phase 1 begins with real content models, commerce and authentication integration, admin workflows, photography, and business-specific interaction design. None of those belong in this implementation.

## 12. Phase 3 Asset and Token Contract

Phase 3 imports static source material and token vocabulary only. It does not replace route stubs, build public pages, build admin pages, or port Three.js/GSAP effects.

### Public asset paths

The `simar-website` source assets are copied into Vite public paths:

- Logo: `/assets/logo.jpg`.
- Images: `/assets/images/blog_1.png`, `/assets/images/blog_2.png`, `/assets/images/blog_3.png`, `/assets/images/coach_advice.png`, `/assets/images/contact_skating.png`, `/assets/images/elite_ice.png`, `/assets/images/gallery_skating.png`, `/assets/images/hero_skating.png`, `/assets/images/pro_ice.png`, `/assets/images/rink_roller.png`, `/assets/images/shop_1.png`, `/assets/images/shop_2.png`, `/assets/images/shop_3.png`, `/assets/images/shop_4.png`, `/assets/images/street_roller.png`, and `/assets/images/techniques_skating.png`.

React code should reference these as absolute public paths. Do not import copied images from `src`.

### Token extraction rule

`simar-website/css/glacial-3d.css` is source material, not a stylesheet dependency. Only selected custom properties are extracted into `frontend/src/styles/tokens.css`: glacial gradients, border aliases, shadow aliases, font aliases, container widths, nav height, and transition aliases. The 3,741-line legacy CSS file must not be pasted or imported wholesale.

`frontend/src/styles/tokens.ts` is a typed mirror for asset paths and token names. CSS remains the visual source of truth.

### Admin theme boundary

`simar-website/css/admin-theme.css` contributes soft admin surface concepts: raised panels, quiet hover lift, inset-active rail state, and status tone utilities. Legacy layout selectors such as `.admin-layout`, `.admin-sidebar`, `body:has(...)`, chart mockups, and dashboard page UI are intentionally not ported. Admin remains quiet, dense, and Canvas-free.

## 13. Phase 4 Public Page Contract

Phase 4 turns the public route shell into a narrow read-only content surface. It keeps the Aurora Frost atmosphere, exact route catalog, and admin boundary intact.

Implemented pages are `/`, `/home`, `/shop`, `/product/:id`, `/post/:slug`, `/techniques`, `/gallery`, `/about`, and `/contact`. These pages may call Phase 1 read endpoints through Phase 2 wrappers and stores. They must render useful static headings before data resolves so the frontend remains testable without Flask.

Commerce, account, payment/status, legal, rules, managed page, and admin routes remain deferred. Deferred routes must say so directly rather than implying incomplete behavior.

Public Phase 4 pages use copied assets through `publicAssets` or normalized `/assets/...` paths. They do not submit forms, mutate carts, call auth endpoints, store JWTs, add bearer headers, or add new GSAP/Three effects. Styling lives in scoped public-page CSS and consumes existing design variables.

## 14. Phase 5 Commerce and Account Contract

Phase 5 activates `/checkout`, `/profile`, `/order/:id`, `/invoice/:id`, and `/return/:id` as restrained public-account surfaces. They use the existing cookie-session stores and API wrappers, not browser token storage.

Checkout is a quote/save/load preview, not payment activation. Order cancellation and return requests require explicit button/form submission. Profile, order, invoice, and return pages must show protected-session copy when anonymous and must not hide the route behind a blank loading state.

Legal, rules, payment status, managed custom page, and admin routes remain deferred. Phase 5 styling stays within the public page CSS system and does not affect `.admin-shell` or introduce new motion/rendering dependencies.

## 15. Phase 6 Managed Content Contract

Phase 6 activates `/legal`, `/rules`, `/isu-rules`, and `/page` as read-only public content. It does not activate payment status routes, provider scripts, provider verification flows, or admin pages.

Managed custom pages use backend read APIs and render body content as plain text. This avoids introducing HTML rendering risk before an explicit sanitization/rendering policy is approved. Rules pages are reference cards with an external official-source link rather than a wholesale legacy template port.

`/success` and `/payment-failed` remain deferred because they are payment-status surfaces. Phase 6 styling stays scoped to public content cards and must not affect `.admin-shell`.
