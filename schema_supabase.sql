-- ============================================================
--  ON ICE - Supabase/Postgres Schema
-- ============================================================

CREATE TABLE IF NOT EXISTS settings (
  id          BIGSERIAL PRIMARY KEY,
  setting_key TEXT    NOT NULL UNIQUE,
  setting_val TEXT    NOT NULL DEFAULT '',
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO settings (setting_key, setting_val) VALUES
  ('blog_name',      'On Ice'),
  ('tagline',        'Every day on the ice is a story worth telling.'),
  ('hero_quote',     'The ice does not lie - and neither does hard work.'),
  ('coach_title',    'Head Coach'),
  ('whatsapp_link',  ''),
  ('contact_email',  '')
ON CONFLICT (setting_key) DO NOTHING;

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

CREATE TABLE IF NOT EXISTS posts (
  id         TEXT    NOT NULL PRIMARY KEY,
  title      TEXT    NOT NULL,
  excerpt    TEXT    NOT NULL DEFAULT '',
  body       TEXT    NOT NULL,
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

INSERT INTO posts (id, title, excerpt, body, author, read_time, pinned, post_date) VALUES
('p1', 'First Day Back After the Break', 'After two weeks away, stepping back onto the ice today reminded me exactly why I fell in love with this sport.', '<p>After two weeks away, stepping back onto the ice today reminded me exactly why I fell in love with this sport.</p>', 'The Coach', 4, 1, '2024-04-10'),
('p2', 'Breakthrough Moment with the Junior Group', 'Sometimes coaching is about waiting for the right moment. Today was one of those moments.', '<p>Sometimes coaching is about waiting for the right moment.</p>', 'The Coach', 3, 0, '2024-04-03'),
('p3', 'Competition Week - What Goes Through My Mind', 'Standing at the boards during competition week is a different kind of pressure.', '<p>Standing at the boards during competition week is a different kind of pressure.</p>', 'The Coach', 4, 0, '2024-03-22'),
('p4', 'An Ordinary Tuesday That Turned Into Something Special', 'Not every training day has a dramatic story.', '<p>Not every training day has a dramatic story.</p>', 'The Coach', 3, 0, '2024-03-14')
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS techniques (
  id         TEXT    NOT NULL PRIMARY KEY,
  title      TEXT    NOT NULL,
  icon       TEXT    NOT NULL DEFAULT '',
  excerpt    TEXT    NOT NULL DEFAULT '',
  body       TEXT    NOT NULL DEFAULT '',
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO techniques (id, title, icon, excerpt, body, sort_order) VALUES
('t1','Landing Your First Axel','target','The Axel is the only jump that takes off from a forward outside edge.','<h3>Why It Is Different</h3><p>The Axel takes off forward.</p>',1),
('t2','Spin Centering','spin','Traveling spins are the most common problem in figure skating.','<h3>Weight Placement</h3><p>Spin on the ball of your foot.</p>',2),
('t3','Power Crossovers','power','Crossovers are the foundation of all speed and edge work.','<h3>The Push</h3><p>The power comes from the under-push.</p>',3),
('t4','Mental Prep for Competition','trophy','The mental game of skating is just as important as the physical.','<h3>Box Breathing</h3><p>Four counts in. Hold four. Out four. Hold four.</p>',4)
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS custom_pages (
  id         TEXT NOT NULL PRIMARY KEY,
  name       TEXT NOT NULL,
  slug       TEXT NOT NULL UNIQUE,
  body       TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gallery_items (
  id          TEXT    NOT NULL PRIMARY KEY,
  emoji       TEXT    NOT NULL DEFAULT '',
  title       TEXT    NOT NULL,
  description TEXT    NOT NULL DEFAULT '',
  tag         TEXT    NOT NULL DEFAULT 'Training',
  image_path  TEXT    NOT NULL DEFAULT '',
  sort_order  INTEGER NOT NULL DEFAULT 0,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contact_messages (
  id         BIGSERIAL PRIMARY KEY,
  name       TEXT    NOT NULL,
  email      TEXT    NOT NULL,
  subject    TEXT    NOT NULL DEFAULT '',
  message    TEXT    NOT NULL,
  is_read    INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
  id          TEXT    NOT NULL PRIMARY KEY,
  name        TEXT    NOT NULL,
  description TEXT    NOT NULL DEFAULT '',
  base_price  REAL    NOT NULL DEFAULT 0.0,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS product_images (
  id          TEXT    NOT NULL PRIMARY KEY,
  product_id  TEXT    NOT NULL,
  color_match TEXT    NOT NULL DEFAULT '',
  image_url   TEXT    NOT NULL,
  sort_order  INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS media_library (
  id          TEXT    NOT NULL PRIMARY KEY,
  media_type  TEXT    NOT NULL CHECK(media_type IN ('image','video')),
  url         TEXT    NOT NULL,
  alt_text    TEXT    NOT NULL DEFAULT '',
  uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_tokens (
  id           TEXT    NOT NULL PRIMARY KEY,
  platform     TEXT    NOT NULL CHECK(platform IN ('facebook','instagram')),
  access_token TEXT    NOT NULL,
  expires_at   TIMESTAMP DEFAULT NULL,
  updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
  id                  TEXT    NOT NULL PRIMARY KEY,
  name                TEXT    NOT NULL,
  address             TEXT    NOT NULL,
  total_amount        REAL    NOT NULL,
  payment_method      TEXT    NOT NULL,
  status              TEXT    NOT NULL DEFAULT 'completed',
  order_token         TEXT    NOT NULL UNIQUE,
  razorpay_payment_id TEXT    DEFAULT NULL UNIQUE,
  razorpay_order_id   TEXT    DEFAULT NULL,
  paytm_txn_id        TEXT    DEFAULT NULL UNIQUE,
  customer_email      TEXT    DEFAULT '',
  customer_phone      TEXT    DEFAULT '',
  created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id          TEXT    NOT NULL PRIMARY KEY,
  event_type  TEXT    NOT NULL,
  actor_id    TEXT    DEFAULT NULL,
  ip_address  TEXT    DEFAULT NULL,
  detail      TEXT    NOT NULL DEFAULT '',
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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
