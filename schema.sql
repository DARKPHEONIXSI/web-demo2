-- ============================================================
--  ON ICE — SQLite Schema (with JWT & Order Tokens)
-- ============================================================

-- SETTINGS
CREATE TABLE IF NOT EXISTS settings (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  setting_key TEXT    NOT NULL UNIQUE,
  setting_val TEXT    NOT NULL DEFAULT '',
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO settings (setting_key, setting_val) VALUES
  ('blog_name',      'On Ice'),
  ('tagline',        'Every day on the ice is a story worth telling.'),
  ('hero_quote',     'The ice does not lie — and neither does hard work.'),
  ('coach_title',    'Head Coach'),
  ('whatsapp_link',  ''),
  ('contact_email',  '');

-- USERS
CREATE TABLE IF NOT EXISTS users (
  id                 TEXT    NOT NULL PRIMARY KEY,
  username           TEXT    NOT NULL UNIQUE,
  password           TEXT    NOT NULL DEFAULT '',
  google_email       TEXT    DEFAULT NULL,
  is_google          INTEGER NOT NULL DEFAULT 0,
  role               TEXT    NOT NULL DEFAULT 'user' CHECK(role IN ('user','admin')),
  jwt_token          TEXT    DEFAULT NULL,
  jwt_expires_at     TIMESTAMP DEFAULT NULL,
  refresh_token      TEXT    DEFAULT NULL,
  refresh_expires_at TIMESTAMP DEFAULT NULL,
  created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- POSTS
CREATE TABLE IF NOT EXISTS posts (
  id         TEXT    NOT NULL PRIMARY KEY,
  title      TEXT    NOT NULL,
  excerpt    TEXT    NOT NULL DEFAULT '',
  body       TEXT    NOT NULL,
  cover_image TEXT   NOT NULL DEFAULT '',
  category   TEXT    NOT NULL DEFAULT '',
  tags       TEXT    NOT NULL DEFAULT '',
  slug       TEXT    NOT NULL UNIQUE,
  seo_title  TEXT    NOT NULL DEFAULT '',
  seo_description TEXT NOT NULL DEFAULT '',
  author     TEXT    NOT NULL DEFAULT 'The Coach',
  author_id  TEXT    DEFAULT NULL,
  read_time  INTEGER NOT NULL DEFAULT 4,
  pinned     INTEGER NOT NULL DEFAULT 0,
  status     TEXT    NOT NULL DEFAULT 'published' CHECK(status IN ('draft','published')),
  post_date  TEXT    NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Seed posts
INSERT OR IGNORE INTO posts (id, title, excerpt, body, category, tags, slug, author, read_time, pinned, post_date) VALUES
('p1',
 'First Day Back After the Break',
 'After two weeks away, stepping back onto the ice today reminded me exactly why I fell in love with this sport.',
 '<p>After two weeks away, stepping back onto the ice today reminded me exactly why I fell in love with this sport. The rink was empty when I arrived — just me, the cold air, and that familiar feeling of blades connecting with ice.</p><p>We started slow. Light stroking drills, some backward crossovers to warm up the legs. By the third lap I could feel the rust shaking off.</p><blockquote>"The ice does not care about your yesterday — only what you do today."</blockquote><p>Tomorrow we go again. Early start. Can''t wait.</p>',
 'Training', 'practice,comeback', 'first-day-back-after-the-break', 'The Coach', 4, 1, '2024-04-10'),
('p2',
 'Breakthrough Moment with the Junior Group',
 'Sometimes coaching is about waiting for the right moment. Today was one of those moments.',
 '<p>Sometimes coaching is about waiting for the right moment. Today was one of those moments for three of my students who have been working on their Axels for the past two months.</p><p>After the session, one of them skated over and said "Coach, I felt it." That is exactly what we are always chasing.</p>',
 'Coaching', 'juniors,axel', 'breakthrough-moment-with-the-junior-group', 'The Coach', 3, 0, '2024-04-03'),
('p3',
 'Competition Week — What Goes Through My Mind',
 'Standing at the boards during competition week is a different kind of pressure.',
 '<p>Standing at the boards during competition week is a different kind of pressure. As the coach, my job is mostly done. Three of the four skated personal bests. The fourth had a fall but finished with their head high.</p>',
 'Competition', 'competition,mindset', 'competition-week-what-goes-through-my-mind', 'The Coach', 4, 0, '2024-03-22'),
('p4',
 'An Ordinary Tuesday That Turned Into Something Special',
 'Not every training day has a dramatic story. But sometimes the ordinary ones leave the biggest impression.',
 '<p>Not every training day has a dramatic story. But halfway through the session I saw something shift — the posture changed, the chin came up. <strong>"That was it. That was what I have been waiting to see."</strong></p>',
 'Training', 'progress,practice', 'an-ordinary-tuesday-that-turned-into-something-special', 'The Coach', 3, 0, '2024-03-14');

-- TECHNIQUES
CREATE TABLE IF NOT EXISTS techniques (
  id         TEXT    NOT NULL PRIMARY KEY,
  title      TEXT    NOT NULL,
  icon       TEXT    NOT NULL DEFAULT '⛸',
  excerpt    TEXT    NOT NULL DEFAULT '',
  body       TEXT    NOT NULL DEFAULT '',
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO techniques (id, title, icon, excerpt, body, sort_order) VALUES
('t1','Landing Your First Axel','🎯',
 'The Axel is the only jump that takes off from a forward outside edge. Here is the complete breakdown.',
 '<h3>Why It Is Different</h3><p>The Axel takes off forward — making it the most challenging single jump.</p><h3>The Take-Off</h3><p>Drive your free knee up hard and fast. <strong>One explosive motion.</strong></p><blockquote>"The Axel does not care how badly you want it — only how well you have prepared."</blockquote>',
 1),
('t2','Spin Centering','🌀',
 'Traveling spins are the most common problem in figure skating. The real fix is simpler than you think.',
 '<h3>Weight Placement</h3><p>Spin on the <strong>ball of your foot</strong>, just behind the toe pick.</p><h3>The Sticker Drill</h3><p>Place a circle sticker on the ice. Spin on it for 5 full rotations without leaving it.</p>',
 2),
('t3','Power Crossovers','⚡',
 'Crossovers are the foundation of all speed and edge work. Master these and everything else improves.',
 '<h3>The Push</h3><p>The power comes from the <strong>under-push</strong> — the inside leg pushing directly to the side.</p><blockquote>"Speed is a side effect of good technique — not the goal."</blockquote>',
 3),
('t4','Mental Prep for Competition','🏆',
 'The mental game of skating is just as important as the physical. This is how to prepare your mind.',
 '<h3>Box Breathing</h3><p>Four counts in. Hold four. Out four. Hold four.</p><blockquote>"Preparation is confidence. Confidence is performance."</blockquote>',
 4);

-- CUSTOM PAGES
CREATE TABLE IF NOT EXISTS custom_pages (
  id         TEXT NOT NULL PRIMARY KEY,
  name       TEXT NOT NULL,
  slug       TEXT NOT NULL UNIQUE,
  body       TEXT NOT NULL DEFAULT '',
  seo_title  TEXT NOT NULL DEFAULT '',
  seo_description TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- GALLERY
CREATE TABLE IF NOT EXISTS gallery_items (
  id          TEXT    NOT NULL PRIMARY KEY,
  emoji       TEXT    NOT NULL DEFAULT '⛸',
  title       TEXT    NOT NULL,
  description TEXT    NOT NULL DEFAULT '',
  tag         TEXT    NOT NULL DEFAULT 'Training',
  image_path  TEXT    NOT NULL DEFAULT '',
  sort_order  INTEGER NOT NULL DEFAULT 0,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO gallery_items (id, emoji, title, description, tag, sort_order) VALUES
('g1','⛸','Morning Practice','Early ice session before the rink opens to the public.','Training',1),
('g2','🏆','Competition Day','Skaters lined up and ready. The energy in the rink was electric.','Competition',2),
('g3','🌀','Spin Drills','Perfecting centering technique during intermediate group practice.','Technique',3),
('g4','🎯','Jump Training','Axel progression work with the junior group. Big breakthroughs today.','Training',4),
('g5','❄','Winter Showcase','Annual showcase performance — all levels performing their programs.','Event',5),
('g6','⚡','Edge Work','Power crossover drills building speed and edge confidence.','Technique',6),
('g7','🎭','Costume Fitting','Getting ready for the regional competition. Costumes looking sharp.','Competition',7),
('g8','🌟','Personal Best','A skater lands their first clean Axel in competition. Unforgettable.','Milestone',8),
('g9','🏅','Podium Moment','Three students on the podium at the regional qualifier.','Competition',9);

-- CONTACT MESSAGES
CREATE TABLE IF NOT EXISTS contact_messages (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT    NOT NULL,
  email      TEXT    NOT NULL,
  subject    TEXT    NOT NULL DEFAULT '',
  message    TEXT    NOT NULL,
  is_read    INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- PRODUCTS (E-Commerce)
CREATE TABLE IF NOT EXISTS products (
  id          TEXT    NOT NULL PRIMARY KEY,
  name        TEXT    NOT NULL,
  description TEXT    NOT NULL DEFAULT '',
  category    TEXT    NOT NULL DEFAULT '',
  badge       TEXT    NOT NULL DEFAULT '',
  sku         TEXT    NOT NULL DEFAULT '',
  status      TEXT    NOT NULL DEFAULT 'active' CHECK(status IN ('active','draft','archived')),
  stock_quantity INTEGER NOT NULL DEFAULT 0,
  base_price  REAL    NOT NULL DEFAULT 0.0,
  sale_price  REAL    DEFAULT NULL,
  seo_title   TEXT    NOT NULL DEFAULT '',
  seo_description TEXT NOT NULL DEFAULT '',
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- PRODUCT VARIANTS
CREATE TABLE IF NOT EXISTS product_variants (
  id             TEXT    NOT NULL PRIMARY KEY,
  product_id     TEXT    NOT NULL,
  color          TEXT    NOT NULL DEFAULT '',
  size           TEXT    NOT NULL DEFAULT '',
  stock_quantity INTEGER NOT NULL DEFAULT 0,
  price_override REAL    DEFAULT NULL,
  FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
  UNIQUE(product_id, color, size)
);

-- PRODUCT IMAGES
CREATE TABLE IF NOT EXISTS product_images (
  id          TEXT    NOT NULL PRIMARY KEY,
  product_id  TEXT    NOT NULL,
  color_match TEXT    NOT NULL DEFAULT '',
  image_url   TEXT    NOT NULL,
  sort_order  INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- MEDIA LIBRARY
CREATE TABLE IF NOT EXISTS media_library (
  id          TEXT    NOT NULL PRIMARY KEY,
  media_type  TEXT    NOT NULL CHECK(media_type IN ('image','video')),
  url         TEXT    NOT NULL,
  alt_text    TEXT    NOT NULL DEFAULT '',
  uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- SOCIAL TOKENS
CREATE TABLE IF NOT EXISTS social_tokens (
  id           TEXT    NOT NULL PRIMARY KEY,
  platform     TEXT    NOT NULL CHECK(platform IN ('facebook','instagram')),
  access_token TEXT    NOT NULL,
  expires_at   TIMESTAMP DEFAULT NULL,
  updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ORDERS
CREATE TABLE IF NOT EXISTS orders (
  id                 TEXT    NOT NULL PRIMARY KEY,
  user_id            TEXT    DEFAULT NULL,
  name               TEXT    NOT NULL,
  address            TEXT    NOT NULL,
  total_amount       REAL    NOT NULL,
  shipping_amount    REAL    NOT NULL DEFAULT 0,
  tax_amount         REAL    NOT NULL DEFAULT 0,
  discount_amount    REAL    NOT NULL DEFAULT 0,
  payment_method     TEXT    NOT NULL,
  status             TEXT    NOT NULL DEFAULT 'completed' CHECK(status IN ('pending','completed','payment_failed','cancelled','refunded')),
  fulfillment_status TEXT    NOT NULL DEFAULT 'pending' CHECK(fulfillment_status IN ('pending','packed','shipped','delivered','cancelled','returned')),
  tracking_number    TEXT    NOT NULL DEFAULT '',
  order_token        TEXT    NOT NULL UNIQUE,
  razorpay_payment_id TEXT   DEFAULT NULL UNIQUE,
  razorpay_order_id   TEXT   DEFAULT NULL,
  paytm_txn_id         TEXT   DEFAULT NULL UNIQUE,
  customer_email       TEXT   DEFAULT '',
  customer_phone       TEXT   DEFAULT '',
  created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku ON products(sku) WHERE sku <> '';

-- AUDIT LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
  id          TEXT    NOT NULL PRIMARY KEY,
  event_type  TEXT    NOT NULL,
  actor_id    TEXT    DEFAULT NULL,
  ip_address  TEXT    DEFAULT NULL,
  detail      TEXT    NOT NULL DEFAULT '',
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ORDER ITEMS
CREATE TABLE IF NOT EXISTS order_items (
  id                 TEXT    NOT NULL PRIMARY KEY,
  order_id           TEXT    NOT NULL,
  product_id         TEXT    NOT NULL,
  product_variant_id TEXT    DEFAULT NULL,
  quantity           INTEGER NOT NULL DEFAULT 1,
  price_at_time      REAL    NOT NULL,
  FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT,
  FOREIGN KEY(product_variant_id) REFERENCES product_variants(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS post_comments (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id    TEXT NOT NULL,
  user_id    TEXT DEFAULT NULL,
  name       TEXT NOT NULL,
  body       TEXT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'approved',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_reviews (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id TEXT NOT NULL,
  user_id    TEXT DEFAULT NULL,
  name       TEXT NOT NULL,
  rating     INTEGER NOT NULL DEFAULT 5,
  body       TEXT NOT NULL DEFAULT '',
  status     TEXT NOT NULL DEFAULT 'approved',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wishlist_items (
  user_id    TEXT NOT NULL,
  product_id TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS coupons (
  code           TEXT NOT NULL PRIMARY KEY,
  discount_type  TEXT NOT NULL DEFAULT 'percent',
  discount_value REAL NOT NULL DEFAULT 0,
  active         INTEGER NOT NULL DEFAULT 1,
  expires_at     TEXT DEFAULT NULL,
  created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS return_requests (
  id         TEXT NOT NULL PRIMARY KEY,
  order_id   TEXT NOT NULL,
  user_id    TEXT DEFAULT NULL,
  reason     TEXT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'requested',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cart_items (
  user_id    TEXT NOT NULL,
  product_id TEXT NOT NULL,
  variant_id TEXT NOT NULL DEFAULT '',
  quantity   INTEGER NOT NULL DEFAULT 1,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, product_id, variant_id)
);

CREATE TABLE IF NOT EXISTS analytics_events (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  object_id  TEXT NOT NULL DEFAULT '',
  user_id    TEXT DEFAULT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_product_reviews_product_id ON product_reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_return_requests_order_id ON return_requests(order_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type, created_at);
