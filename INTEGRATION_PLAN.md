# Integration Plan

## Phase 1 status: backend JSON read APIs

Phase 1 is implemented as additive Flask routes in `api.py`. Existing SSR/Jinja
pages, authentication behavior, and mutation routes remain in place.

### Public reads

| Endpoint | Status | Notes |
| --- | --- | --- |
| `GET /api/get_posts` | Existing | Preserved unchanged; published posts only. |
| `GET /api/get_products` | Added | Active products only; includes the first image by `sort_order` when available. |
| `GET /api/get_product?id=PRODUCT_ID` | Added | Active product with variants, images, and approved reviews; missing/inactive is `404`. |
| `GET /api/get_gallery` | Added | Gallery items ordered by `sort_order`. |
| `GET /api/get_techniques` | Added | Techniques ordered by `sort_order`. |
| `GET /api/get_pages` | Added | Custom pages ordered by creation time. |
| `GET /api/get_page?id=PAGE_ID` | Added | Custom page detail; missing is `404`. |

### Authenticated user reads

All routes use `@jwt_required` and the existing HttpOnly access-token cookie.

| Endpoint | Status | Notes |
| --- | --- | --- |
| `GET /api/profile/orders` | Added | Latest 20 orders for the authenticated user. |
| `GET /api/order/detail?token=ORDER_TOKEN` | Added | Owner or admin only; includes variant-aware tracking items. |
| `GET /api/invoice/detail?token=ORDER_TOKEN` | Added | Owner or admin only; includes invoice items. |

Order detail and invoice detail mirror the SSR ownership rule in `app.py`:
an absent token returns `404`, while an existing order requested by a different
non-admin user returns `403`.

### Admin reads

All routes use `@admin_required`.

| Endpoint | Status | Notes |
| --- | --- | --- |
| `GET /api/admin/dashboard` | Added | Counts, completed-order revenue, unread messages, and low-stock products. |
| `GET /api/admin/orders` | Added | Latest 100 orders. |
| `GET /api/admin/products` | Added | All product statuses with primary image. |
| `GET /api/admin/posts` | Added | Published and draft posts. |
| `GET /api/admin/messages` | Added | Latest 50 contact messages. |
| `GET /api/admin/users` | Added | Explicit non-secret fields only; password and JWT/refresh tokens are excluded. |
| `GET /api/admin/media` | Added | Media-library records. |

No admin JSON endpoint queries `social_tokens`; `access_token` values are not
included in any Phase 1 response.

## Existing endpoints preserved

- Auth: register, login, Google login, refresh, current user, password change,
  and logout under `/auth/*`.
- Public/user actions: contact, comments, reviews, wishlist, cart quote/save/load,
  Razorpay create/verify/webhook, order cancellation, and return requests.
- Admin mutations: uploads/media, posts, techniques, custom pages, settings,
  gallery, messages, users, products, variants, product images, order status,
  and refunds.
- Paytm endpoints remain present but intentionally return `501`; Phase 1 does
  not implement or activate Paytm.
- All SSR routes in `app.py` and admin SSR routes in `admin_bp.py` remain the
  rendering surface for the current frontend.

## Blockers and skips

- No frontend integration was attempted in Phase 1.
- No schema migration was needed; queries use columns already defined by
  `schema.sql` and the existing runtime schema additions in `models.py`.
- Paytm remains blocked on merchant credentials and frontend activation and is
  explicitly outside this phase.
- PostgreSQL-specific integration tests were not added; the read SQL uses the
  project database adapter's existing portable query conventions.

## Verification

- Focused tests: `python -m pytest tests/test_read_apis.py -q`
- Full regression suite: `python -m pytest -q`
- Focused coverage includes public visibility, product relations, anonymous
  auth failures, owner/admin order access, wrong-owner denial, absent orders,
  admin denial for normal users, admin success, and secret-field exclusion.

## Phase 2 implications

1. Define and version the frontend-facing response contracts before replacing
   SSR data loading; Phase 1 intentionally keeps the existing `{ok, msg, ...}`
   convention rather than introducing a second envelope.
2. Continue using HttpOnly cookies and existing JWT decorators; do not move
   credentials into browser storage.
3. Add pagination/filter parameters before using admin orders, posts, products,
   messages, or users for unbounded production datasets.
4. Decide whether order/payment identifiers need field-level redaction for any
   future non-admin support role before adding role variants.
5. Add PostgreSQL-backed integration coverage before a database cutover, while
   keeping the SQLite fixture suite as the fast regression gate.

## Phase 2 status: frontend foundation

Phase 2 is implemented in `frontend` as infrastructure only. The existing route
stubs and visual shell remain in place; no public pages, admin pages, assets, or
visual effects were ported in this phase.

### Package and dev server foundation

- Added direct npm dependencies: `gsap`, `@gsap/react`, `chart.js`, and
  `zustand`.
- Added Vite dev proxy entries for `/api` and `/auth` to
  `http://127.0.0.1:5000` so local React requests can reach Flask while using
  relative URLs.

### API modules

Created typed frontend API modules under `frontend/src/api`:

- `client.ts`: shared request helper, `ApiError`, cookie-backed requests,
  query support, form body support, and once-only `/auth/refresh` retry.
- `auth.ts`: login, register, logout, refresh, current user, and password
  change wrappers.
- `posts.ts`, `products.ts`, `gallery.ts`, `techniques.ts`, `pages.ts`: public
  Phase 1 read wrappers.
- `cart.ts`: quote/save/load wrappers using form-encoded cart payloads.
- `orders.ts`: profile orders, order detail, invoice detail, cancellation, and
  return request wrappers.
- `admin.ts`: admin read wrappers for dashboard, orders, products, posts,
  messages, users, and media.

The client never stores JWTs, never reads JWTs from browser storage, and does
not send `Authorization` or `Bearer` headers. Auth remains HttpOnly-cookie based.

### Stores

Created Zustand stores under `frontend/src/store`:

- `authStore.ts`: session status, current user, loading/error state, and auth
  actions. Tokens are not persisted.
- `cartStore.ts`: local cart items, quote state, save/load actions, and API
  serialization.
- `productStore.ts`: product list, product detail cache, loading/error state.

The existing `AuthShellContext` now reads session status from `authStore` while
preserving the current modal shell behavior.

### Phase 2 verification

- Focused Phase 2 tests cover dependency/proxy metadata, API client credentials
  and refresh behavior, endpoint wrapper paths/form bodies, and store state
  transitions.
- The test setup includes an in-memory `localStorage` shim for this Windows/Node
  test runtime, where the global storage object is otherwise unavailable.

### Phase 3 implications

1. Public pages can now consume `src/api/*` wrappers and `productStore` instead
   of runtime mock data.
2. Checkout and profile work should reuse `cartStore`, `authStore`, and
   `orders.ts` rather than introducing page-local API calls.
3. Visual effects can use the installed GSAP packages in Phase 6, but no GSAP
   runtime code was added in Phase 2.
4. Admin pages can use `admin.ts` read wrappers first, then add mutation wrappers
   only where the page actually needs them.

## Phase 3 status: assets and design tokens

Phase 3 is implemented as static asset and design-token infrastructure only.
Existing public/admin route stubs remain in place.

### Assets copied

- Copied `simar-website/assets/logo.jpg` to `frontend/public/assets/logo.jpg`.
- Copied the 16 source images from `simar-website/assets/images` to
  `frontend/public/assets/images`.
- Frontend paths are absolute Vite public paths, for example
  `/assets/images/hero_skating.png`.

### Design tokens

- Extended `frontend/src/styles/tokens.css` with selected glacial gradients,
  borders, shadows, font aliases, container widths, nav height, and transition
  aliases from `glacial-3d.css`.
- Added `frontend/src/styles/tokens.ts` as a typed mirror for public asset paths
  and token name groups.
- The source `glacial-3d.css` was not pasted or imported wholesale.

### Admin theme concepts

- Updated `frontend/src/styles/admin.css` with soft admin panel/shadow/status
  concepts from `admin-theme.css`.
- Legacy layout selectors, global `body:has(...)` hiding, mock chart styling,
  and full dashboard UI were not ported.

### Phase 4 implications

1. Public page implementation can now use the copied public images and typed
   asset paths from `src/styles/tokens.ts`.
2. Page components should consume existing CSS variables rather than duplicating
   source-site color values.
3. Admin page work should keep the current `.admin-shell`/`.admin-rail` layout
   contract and use the new quiet status utilities where needed.

## Phase 4 status: bounded public page implementation

Phase 4 replaces the all-public-stub route behavior for the content/read-only
public surface only. Admin pages, commerce mutations, account workflows, legal
content, rules pages, and payment/status flows remain intentionally deferred.

### Implemented public routes

- `/` and `/home`: public landing page using Phase 3 hero imagery and read-only
  summary counts from product, post, and technique reads when available.
- `/shop`: product discovery using `productStore.loadProducts()` with client-side
  search only; no cart mutation is wired.
- `/product/:id`: read-only product detail using `productStore.loadProduct(id)`;
  variants, reviews, stock, and price are displayed without add-to-cart behavior.
- `/post/:slug`: read-only post summary route using `postsApi.getPosts()` and
  slug matching; raw post body HTML is not rendered.
- `/techniques`: read-only technique guide list using `techniquesApi`.
- `/gallery`: responsive image grid using `galleryApi` and public asset path
  normalization.
- `/about` and `/contact`: static public storytelling/form-shell pages using
  typed Phase 3 assets. Contact submission remains deferred.

### Deferred public routes

The following public routes now render a shared deferred page with explicit
Phase 4 boundary copy: `/checkout`, `/profile`, `/order/:id`, `/invoice/:id`,
`/return/:id`, `/legal`, `/success`, `/payment-failed`, `/page`, `/rules`, and
`/isu-rules`.

### Frontend boundaries

- `frontend/src/pages/public/publicAssetPath.ts` normalizes legacy-style image
  paths into Vite public asset paths.
- `frontend/src/pages/public/PublicPageState.tsx` provides small accessible
  loading, empty, and error states for read-only pages.
- `frontend/src/styles/public-pages.css` contains scoped Phase 4 public-page
  layout rules and consumes existing CSS variables. Legacy source CSS is not
  imported or pasted wholesale.
- Public page source does not add `Authorization` headers, browser token storage,
  `/auth/` calls, GSAP/ScrollTrigger code, or new Three.js imports.

### Phase 5 implications

1. Commerce work should add explicit cart/checkout mutations behind tests rather
   than extending the Phase 4 read-only pages implicitly.
2. Account/order/invoice/return routes should be implemented as authenticated
   cookie-session pages using the existing `orders.ts` and `authStore` contracts.
3. Admin implementation can proceed separately from the public route work and
   should keep the admin shell Canvas-free.

## Phase 5 status: commerce and account public routes

Phase 5 activates the public commerce/account routes that were deferred in
Phase 4, while keeping real payment processing, admin implementation, legal/rule
content, and managed custom pages out of scope.

### Activated routes

- `/checkout`: loads the current cookie-session cart, refreshes a cart quote,
  saves the cart, and can clear local cart state. It does not create orders or
  call payment providers.
- `/profile`: checks the current cookie session through `authStore`, displays
  the current user id/role, and lists latest profile orders with order/invoice
  links.
- `/order/:id`: treats `id` as the existing order token and loads authenticated
  order detail through `ordersApi.getOrderDetail()`. Cancellation is an explicit
  user click through `ordersApi.cancelOrder()`.
- `/invoice/:id`: loads authenticated invoice detail through
  `ordersApi.getInvoiceDetail()` and renders an invoice-safe summary.
- `/return/:id`: loads order context, requires a non-empty reason, and submits a
  return request through `ordersApi.requestReturn()`.

### Still deferred

`/legal`, `/success`, `/payment-failed`, `/page`, `/rules`, and `/isu-rules`
remain on the shared deferred page. Admin routes remain on `AdminStubPage`.

### Security and payment boundary

Phase 5 continues to use HttpOnly cookie-backed auth through the existing API
client. Public page source does not add browser token storage, bearer headers,
payment-provider activation, GSAP/ScrollTrigger code, or new Three.js imports.

### Phase 6 implications

1. Payment activation should be a separate phase with provider-specific tests,
   server contract confirmation, and failure/retry UX.
2. Legal/rules/custom-page content can be implemented as managed read-only pages
   without mixing into payment or account work.
3. Admin implementation remains a separate Canvas-free lane.

## Phase 6 status: read-only legal, rules, and managed content

Phase 6 activates the safe managed-content lane from the Phase 5 implications.
Payment status and provider activation remain deferred, and admin routes remain
on the existing stubbed admin surface.

### Activated routes

- `/legal`: static policy hub for terms, privacy, shipping/returns, and refund
  boundaries.
- `/rules` and `/isu-rules`: shared read-only rules reference page with ISU rule
  categories and an external official-source link.
- `/page`: managed custom-page reader using `pagesApi.getPages()` and
  `pagesApi.getPage(id)`. Page body is rendered as plain text in Phase 6 rather
  than inserted as HTML.

### Still deferred

`/success` and `/payment-failed` remain on the shared deferred page because they
are payment-status surfaces. No provider script, payment creation, payment
verification, or Paytm flow is activated.

### Boundary

Public Phase 6 page source does not add browser token storage, bearer headers,
payment-provider calls, admin API calls, GSAP/ScrollTrigger code, or new Three.js
imports. Admin implementation remains a separate Canvas-free lane.

### Phase 7 implications

1. Payment activation can be considered only after confirming exact backend
   provider contracts, adding provider-specific tests, and defining recovery UX.
2. Admin read implementation can proceed separately using `admin.ts` wrappers and
   the quiet admin shell.
