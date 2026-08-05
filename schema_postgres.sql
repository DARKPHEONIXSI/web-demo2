-- ============================================================
--  ON ICE - Postgres Schema
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

INSERT INTO posts (id, title, excerpt, body, category, tags, slug, author, read_time, pinned, post_date) VALUES
('p1', 'First Day Back After the Break', 'After two weeks away, stepping back onto the ice today reminded me exactly why I fell in love with this sport.', '<p>After two weeks away, stepping back onto the ice today reminded me exactly why I fell in love with this sport.</p>', 'Training', 'practice,comeback', 'first-day-back-after-the-break', 'The Coach', 4, 1, '2024-04-10'),
('p2', 'Breakthrough Moment with the Junior Group', 'Sometimes coaching is about waiting for the right moment. Today was one of those moments.', '<p>Sometimes coaching is about waiting for the right moment.</p>', 'Coaching', 'juniors,axel', 'breakthrough-moment-with-the-junior-group', 'The Coach', 3, 0, '2024-04-03'),
('p3', 'Competition Week - What Goes Through My Mind', 'Standing at the boards during competition week is a different kind of pressure.', '<p>Standing at the boards during competition week is a different kind of pressure.</p>', 'Competition', 'competition,mindset', 'competition-week-what-goes-through-my-mind', 'The Coach', 4, 0, '2024-03-22'),
('p4', 'An Ordinary Tuesday That Turned Into Something Special', 'Not every training day has a dramatic story.', '<p>Not every training day has a dramatic story.</p>', 'Training', 'progress,practice', 'an-ordinary-tuesday-that-turned-into-something-special', 'The Coach', 3, 0, '2024-03-14')
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
  seo_title  TEXT NOT NULL DEFAULT '',
  seo_description TEXT NOT NULL DEFAULT '',
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
  category    TEXT    NOT NULL DEFAULT '',
  badge       TEXT    NOT NULL DEFAULT '',
  sku         TEXT    NOT NULL DEFAULT '',
  status      TEXT    NOT NULL DEFAULT 'active',
  stock_quantity INTEGER NOT NULL DEFAULT 0,
  base_price  NUMERIC(12,2) NOT NULL DEFAULT 0.00,
  sale_price  NUMERIC(12,2) DEFAULT NULL,
  seo_title   TEXT    NOT NULL DEFAULT '',
  seo_description TEXT NOT NULL DEFAULT '',
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_variants (
  id             TEXT    NOT NULL PRIMARY KEY,
  product_id     TEXT    NOT NULL,
  color          TEXT    NOT NULL DEFAULT '',
  size           TEXT    NOT NULL DEFAULT '',
  stock_quantity INTEGER NOT NULL DEFAULT 0,
  price_override NUMERIC(12,2) DEFAULT NULL,
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
  user_id             TEXT    DEFAULT NULL,
  name                TEXT    NOT NULL,
  address             TEXT    NOT NULL,
  total_amount        NUMERIC(12,2) NOT NULL,
  shipping_amount     NUMERIC(12,2) NOT NULL DEFAULT 0,
  tax_amount          NUMERIC(12,2) NOT NULL DEFAULT 0,
  discount_amount     NUMERIC(12,2) NOT NULL DEFAULT 0,
  payment_method      TEXT    NOT NULL,
  status              TEXT    NOT NULL DEFAULT 'completed',
  fulfillment_status  TEXT    NOT NULL DEFAULT 'pending',
  tracking_number     TEXT    NOT NULL DEFAULT '',
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
  price_at_time      NUMERIC(12,2) NOT NULL,
  FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT,
  FOREIGN KEY(product_variant_id) REFERENCES product_variants(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS post_comments (
  id BIGSERIAL PRIMARY KEY,
  post_id TEXT NOT NULL,
  user_id TEXT DEFAULT NULL,
  name TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'approved',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_reviews (
  id BIGSERIAL PRIMARY KEY,
  product_id TEXT NOT NULL,
  user_id TEXT DEFAULT NULL,
  name TEXT NOT NULL,
  rating INTEGER NOT NULL DEFAULT 5,
  body TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'approved',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wishlist_items (
  user_id TEXT NOT NULL,
  product_id TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS coupons (
  code TEXT NOT NULL PRIMARY KEY,
  discount_type TEXT NOT NULL DEFAULT 'percent',
  discount_value NUMERIC(12,2) NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1,
  expires_at TEXT DEFAULT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS return_requests (
  id TEXT NOT NULL PRIMARY KEY,
  order_id TEXT NOT NULL,
  user_id TEXT DEFAULT NULL,
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'requested',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cart_items (
  user_id TEXT NOT NULL,
  product_id TEXT NOT NULL,
  variant_id TEXT NOT NULL DEFAULT '',
  quantity INTEGER NOT NULL DEFAULT 1,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, product_id, variant_id)
);

CREATE TABLE IF NOT EXISTS analytics_events (
  id BIGSERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,
  object_id TEXT NOT NULL DEFAULT '',
  user_id TEXT DEFAULT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posts_status_date ON posts(status, post_date DESC);
CREATE INDEX IF NOT EXISTS idx_posts_author_id ON posts(author_id);
CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_product_images_product_id ON product_images(product_id);
CREATE INDEX IF NOT EXISTS idx_gallery_items_sort_order ON gallery_items(sort_order);
CREATE INDEX IF NOT EXISTS idx_media_library_uploaded_at ON media_library(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_variant_id ON order_items(product_variant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_product_reviews_product_id ON product_reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_return_requests_order_id ON return_requests(order_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type, created_at);

ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE techniques ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE gallery_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_library ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE wishlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE coupons ENABLE ROW LEVEL SECURITY;
ALTER TABLE return_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE cart_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;
