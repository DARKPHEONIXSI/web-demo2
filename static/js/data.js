/* ═══════════════════════════════════════════════════════════
   data.js — Mock Data for On Ice 3D Website
   ═══════════════════════════════════════════════════════════ */

const SITE = {
  name: 'On Ice',
  tagline: 'Train the edge. Tell the story. Skate with intent.',
  description: 'A premium rink journal for skaters, parents, and coaches who care about technique, artistry, competition prep, and the gear that earns its place in the bag.',
};

const POSTS = [
  {
    id: 1, slug: 'first-day-back-on-the-ice',
    title: 'First Day Back on the Ice — Resetting Habits After a Break',
    excerpt: 'Returning to the rink after a long pause can feel overwhelming. Here\'s a structured approach to rebuild confidence without rushing the edges.',
    category: 'Training', tags: ['mindset', 'comebacks', 'edges'],
    author: 'Coach Simar', post_date: '2026-06-12', read_time: 5,
    cover_image: 'assets/images/blog_1.png', pinned: true,
    content: `<p>After a break—whether it's two weeks or two months—the first session back on the ice deserves its own plan. Most skaters make the mistake of trying to pick up where they left off, and that's where frustration sets in.</p><h2>Start With Edges, Not Jumps</h2><p>Spend the first 15 minutes on forward and backward crossovers. Feel the blade. Don't chase speed—chase control. Your edges will tell you everything about where your body is after time away.</p><h2>Three-Session Rule</h2><p>Give yourself three full sessions before judging your progress. Session one is about reconnecting. Session two is about remembering. Session three is where the real work begins.</p><p>The ice doesn't forget you. But it does require you to show up with patience.</p>`
  },
  {
    id: 2, slug: 'mastering-the-axel-jump',
    title: 'Mastering the Axel — The Jump That Changes Everything',
    excerpt: 'The Axel is the gatekeeper of competitive skating. Understanding its mechanics separates recreational from competitive skaters.',
    category: 'Technique', tags: ['jumps', 'axel', 'competition'],
    author: 'Coach Simar', post_date: '2026-05-28', read_time: 7,
    cover_image: 'assets/images/blog_2.png', pinned: false,
    content: `<p>The Axel is the only jump that takes off from a forward edge, and that single difference makes it the most feared and respected element in figure skating.</p><h2>The Approach</h2><p>A clean Axel starts long before the takeoff. Your entry edge should be confident—a deep outside edge on the left foot (for counterclockwise jumpers) with your arms controlled and your core engaged.</p><h2>The Snap</h2><p>The rotation happens because of the snap, not because of the swing. Too many skaters try to muscle their way through the air. The best Axels look effortless because the technique is doing the work.</p><p>Practice the waltz jump. If your waltz jump isn't clean, your Axel won't be either.</p>`
  },
  {
    id: 3, slug: 'choosing-your-first-competition-dress',
    title: 'Choosing Your First Competition Dress — Function Over Flash',
    excerpt: 'Your competition outfit should support your skating, not distract from it. A practical guide to choosing what to wear when it counts.',
    category: 'Competition', tags: ['gear', 'competition', 'apparel'],
    author: 'Coach Simar', post_date: '2026-05-15', read_time: 4,
    cover_image: 'assets/images/blog_3.png', pinned: false,
    content: `<p>Your first competition dress doesn't need to be the most expensive thing in your bag. It needs to fit, move with you, and make you feel confident under the lights.</p><h2>Fabric Matters</h2><p>Look for stretch fabrics that won't ride up during spins. Mesh panels can add visual interest without adding weight. Avoid anything that restricts your arm movement.</p><h2>Color Psychology</h2><p>Judges notice presentation. Dark colors photograph well and create strong lines. If your program is lyrical, softer tones work. If it's powerful, go bold.</p><p>The best dress is the one you forget you're wearing because it moves exactly like you do.</p>`
  },
  {
    id: 4, slug: 'off-ice-training-for-skaters',
    title: 'Off-Ice Training That Actually Transfers to the Rink',
    excerpt: 'Not all gym work helps your skating. Here are the exercises that directly improve your balance, rotation, and edge control.',
    category: 'Training', tags: ['off-ice', 'strength', 'balance'],
    author: 'Coach Simar', post_date: '2026-04-30', read_time: 6,
    cover_image: 'assets/images/coach_advice.png', pinned: false,
    content: `<p>Off-ice training should be skating-specific. Running on a treadmill won't improve your sit spin. But single-leg squats might.</p><h2>Core First</h2><p>Every element in skating starts from the core. Planks, hollow body holds, and rotational medicine ball throws build the stability you need for clean positions in the air and on the ice.</p><h2>Single-Leg Everything</h2><p>Skating is essentially a series of single-leg movements. Train that way. Single-leg deadlifts, pistol squats, and balance board work will transfer directly to your edge quality.</p>`
  },
  {
    id: 5, slug: 'understanding-isu-scoring',
    title: 'Understanding ISU Scoring — What the Numbers Actually Mean',
    excerpt: 'GOE, PCS, TES — the scoring system can feel opaque. Here\'s a plain-language breakdown of how judges evaluate your skating.',
    category: 'Competition', tags: ['ISU', 'scoring', 'rules'],
    author: 'Coach Simar', post_date: '2026-04-18', read_time: 8,
    cover_image: 'assets/images/elite_ice.png', pinned: false,
    content: `<p>The ISU judging system has two main components: Technical Element Score (TES) and Program Component Score (PCS). Together, they determine your total score.</p><h2>Technical Elements</h2><p>Every jump, spin, and step sequence has a base value. Judges then add or subtract Grade of Execution (GOE) based on quality. A beautifully executed triple Salchow with +3 GOE scores more than a shaky triple Lutz with -2 GOE.</p><h2>Program Components</h2><p>PCS covers five areas: Skating Skills, Transitions, Performance, Composition, and Interpretation. These scores reward the artistry and completeness of your program, not just the tricks.</p>`
  },
  {
    id: 6, slug: 'blade-care-essentials',
    title: 'Blade Care Essentials — Protect Your Most Important Tool',
    excerpt: 'Your blades are precision instruments. Proper sharpening, drying, and storage habits extend their life and protect your skating.',
    category: 'Gear', tags: ['blades', 'maintenance', 'gear'],
    author: 'Coach Simar', post_date: '2026-04-05', read_time: 4,
    cover_image: 'assets/images/rink_roller.png', pinned: false,
    content: `<p>A dull blade doesn't just feel wrong—it's dangerous. Proper blade care is one of the simplest ways to improve your skating immediately.</p><h2>After Every Session</h2><p>Wipe your blades dry with a soft cloth. Never put blade guards on wet blades—that's how rust starts. Use soakers for storage, guards for walking.</p><h2>Sharpening Schedule</h2><p>Most skaters need a sharpening every 20-40 hours of ice time. Find a sharpener who understands figure skating—hockey sharpening is completely different and will ruin your edges.</p>`
  }
];

const PRODUCTS = [
  {
    id: 1, name: 'Pro Edge Blades MK-IV',
    description: 'Competition-grade carbon steel blades with precision-ground edges. Designed for advanced skaters who demand consistent performance on every element.',
    base_price: 12999.00, sale_price: 10499.00,
    category: 'Blades', badge: 'Best Seller', stock_quantity: 8,
    image: 'assets/images/shop_1.png', sku: 'BLD-MK4-001',
    variants: [
      { id: 'v1', label: 'Size 9.0', price: 10499 },
      { id: 'v2', label: 'Size 9.5', price: 10499 },
      { id: 'v3', label: 'Size 10.0', price: 10799 }
    ],
    reviews: [
      { user: 'Aria K.', rating: 5, text: 'Best blades I\'ve ever skated on. The edge hold is incredible.', date: '2026-05-20' },
      { user: 'Marcus T.', rating: 4, text: 'Great quality, took a session to break in but worth it.', date: '2026-04-15' }
    ]
  },
  {
    id: 2, name: 'Glacier Training Jacket',
    description: 'Lightweight, breathable warmup jacket with four-way stretch fabric. Keeps you warm during practice without restricting movement.',
    base_price: 3499.00, sale_price: null,
    category: 'Apparel', badge: 'New', stock_quantity: 24,
    image: 'assets/images/shop_2.png', sku: 'APP-GLJ-002',
    variants: [
      { id: 'v4', label: 'S', price: 3499 },
      { id: 'v5', label: 'M', price: 3499 },
      { id: 'v6', label: 'L', price: 3499 }
    ],
    reviews: [
      { user: 'Priya S.', rating: 5, text: 'Perfect for morning practice. Love the fit!', date: '2026-06-01' }
    ]
  },
  {
    id: 3, name: 'Arctic Grip Boot Covers',
    description: 'Premium neoprene boot covers that protect your boots from ice chips and moisture. Custom-fit elastic ensures they stay put during training.',
    base_price: 1299.00, sale_price: 999.00,
    category: 'Accessories', badge: 'Sale', stock_quantity: 42,
    image: 'assets/images/shop_3.png', sku: 'ACC-BGC-003',
    variants: [],
    reviews: []
  },
  {
    id: 4, name: 'Competition Practice Dress — Aurora',
    description: 'Hand-embellished practice dress with Swarovski crystals. Aurora-inspired gradient from deep blue to emerald. Performance stretch fabric.',
    base_price: 8999.00, sale_price: null,
    category: 'Apparel', badge: 'Premium', stock_quantity: 5,
    image: 'assets/images/shop_4.png', sku: 'APP-CPD-004',
    variants: [
      { id: 'v7', label: 'XS', price: 8999 },
      { id: 'v8', label: 'S', price: 8999 },
      { id: 'v9', label: 'M', price: 9299 }
    ],
    reviews: [
      { user: 'Elena V.', rating: 5, text: 'Stunning dress. The crystals catch the light beautifully.', date: '2026-05-10' },
      { user: 'Coach Diana', rating: 5, text: 'My student wore this to regionals. Looked amazing.', date: '2026-04-28' }
    ]
  },
  {
    id: 5, name: 'Edge Guard Pro Set',
    description: 'Premium blade guards and soakers combo. Hard guards for walking, soft terry soakers for storage. Keeps your blades rust-free.',
    base_price: 799.00, sale_price: null,
    category: 'Accessories', badge: '', stock_quantity: 67,
    image: 'assets/images/pro_ice.png', sku: 'ACC-EGP-005',
    variants: [],
    reviews: [
      { user: 'Tom R.', rating: 4, text: 'Good quality guards. The soakers are soft and absorbent.', date: '2026-03-15' }
    ]
  },
  {
    id: 6, name: 'Rink Roller Training Wheels',
    description: 'Off-ice jump training wheels that simulate the feel of a landing. Adjustable resistance for progressive training from singles to triples.',
    base_price: 5999.00, sale_price: 4499.00,
    category: 'Training', badge: 'Sale', stock_quantity: 0,
    image: 'assets/images/street_roller.png', sku: 'TRN-RTW-006',
    variants: [],
    reviews: []
  }
];

const GALLERY = [
  { id: 1, src: 'assets/images/hero_skating.png', caption: 'Performance under the spotlight', category: 'Performance' },
  { id: 2, src: 'assets/images/gallery_skating.png', caption: 'Graceful spiral sequence', category: 'Practice' },
  { id: 3, src: 'assets/images/blog_1.png', caption: 'Morning practice at the rink', category: 'Practice' },
  { id: 4, src: 'assets/images/blog_2.png', caption: 'Competition warmup routine', category: 'Competition' },
  { id: 5, src: 'assets/images/blog_3.png', caption: 'Backstage preparation', category: 'Competition' },
  { id: 6, src: 'assets/images/coach_advice.png', caption: 'Coach giving edge feedback', category: 'Coaching' },
  { id: 7, src: 'assets/images/techniques_skating.png', caption: 'Spin position drill', category: 'Practice' },
  { id: 8, src: 'assets/images/contact_skating.png', caption: 'Quiet moments before the music', category: 'Performance' },
];

const TECHNIQUES = [
  {
    category: 'Edges & Turns',
    items: [
      { name: 'Forward Inside Edge', level: 'Beginner', description: 'The foundation of all skating. Practice on a circle, focusing on knee bend and body alignment over the skating hip.' },
      { name: 'Forward Outside Edge', level: 'Beginner', description: 'Counter to the inside edge. Requires leaning away from the circle center while maintaining balance.' },
      { name: 'Three-Turn', level: 'Intermediate', description: 'A one-foot turn from forward to backward (or vice versa) that traces the number 3 on the ice.' },
      { name: 'Mohawk Turn', level: 'Intermediate', description: 'A two-foot turn where you step from one foot to the other, changing direction while maintaining the same edge.' },
      { name: 'Bracket Turn', level: 'Advanced', description: 'Counter-rotated single-foot turn. The hardest of the basic turns, requiring precise edge control against the natural rotation.' },
    ]
  },
  {
    category: 'Jumps',
    items: [
      { name: 'Waltz Jump', level: 'Beginner', description: 'Half-rotation jump from a forward outside edge. The entry point to all jumping technique.' },
      { name: 'Salchow', level: 'Intermediate', description: 'Takes off from a back inside edge. Named after Ulrich Salchow. One of the first multi-rotation jumps learned.' },
      { name: 'Toe Loop', level: 'Intermediate', description: 'Assisted by a toe pick from the free foot. Takes off from a back outside edge.' },
      { name: 'Loop Jump', level: 'Intermediate', description: 'Takes off and lands on the same back outside edge. No toe assist—pure edge jump.' },
      { name: 'Axel', level: 'Advanced', description: 'The only jump that takes off from a forward edge (forward outside). Requires an extra half rotation, making it the most difficult jump per rotation count.' },
    ]
  },
  {
    category: 'Spins',
    items: [
      { name: 'Two-Foot Spin', level: 'Beginner', description: 'Entry-level spin on both feet. Focus on centering and finding the sweet spot of the blade.' },
      { name: 'One-Foot Upright Spin', level: 'Beginner', description: 'Basic scratch spin position. Arms pull in to increase rotation speed.' },
      { name: 'Sit Spin', level: 'Intermediate', description: 'Spinning in a sitting position with the free leg extended forward. Requires strong thigh muscles and balance.' },
      { name: 'Camel Spin', level: 'Intermediate', description: 'Spinning with the free leg extended behind, parallel to the ice. Tests flexibility and core strength.' },
      { name: 'Layback Spin', level: 'Advanced', description: 'Upper body arches backward while spinning. One of the most visually beautiful spins in skating.' },
    ]
  },
  {
    category: 'Off-Ice Drills',
    items: [
      { name: 'Single-Leg Balance Board', level: 'All Levels', description: 'Stand on a wobble board on one foot for 30-60 seconds. Directly improves edge stability.' },
      { name: 'Rotational Jump Training', level: 'Intermediate', description: 'Practice jump rotations on a spinning platform or harness system to build air awareness.' },
      { name: 'Core Stability Circuit', level: 'All Levels', description: 'Planks, hollow body holds, and Russian twists. 3 sets of 12 reps each, 3x per week.' },
    ]
  }
];

const ORDERS = [
  {
    id: 'ORD-2026-001', token: 'abc123',
    date: '2026-06-10', status: 'Delivered',
    items: [
      { name: 'Pro Edge Blades MK-IV', qty: 1, price: 10499 },
      { name: 'Edge Guard Pro Set', qty: 1, price: 799 }
    ],
    subtotal: 11298, shipping: 299, tax: 2034, total: 13631,
    address: { name: 'Riya Sharma', line1: '42 Frost Lane', city: 'Chandigarh', state: 'Punjab', pin: '160017' },
    tracking: 'AWB-9876543210',
    timeline: [
      { status: 'Order Placed', date: '2026-06-10', done: true },
      { status: 'Payment Confirmed', date: '2026-06-10', done: true },
      { status: 'Shipped', date: '2026-06-12', done: true },
      { status: 'Out for Delivery', date: '2026-06-14', done: true },
      { status: 'Delivered', date: '2026-06-15', done: true },
    ]
  },
  {
    id: 'ORD-2026-002', token: 'def456',
    date: '2026-07-01', status: 'Shipped',
    items: [
      { name: 'Glacier Training Jacket', qty: 1, price: 3499 },
    ],
    subtotal: 3499, shipping: 149, tax: 630, total: 4278,
    address: { name: 'Riya Sharma', line1: '42 Frost Lane', city: 'Chandigarh', state: 'Punjab', pin: '160017' },
    tracking: 'AWB-1234567890',
    timeline: [
      { status: 'Order Placed', date: '2026-07-01', done: true },
      { status: 'Payment Confirmed', date: '2026-07-01', done: true },
      { status: 'Shipped', date: '2026-07-03', done: true },
      { status: 'Out for Delivery', date: '', done: false },
      { status: 'Delivered', date: '', done: false },
    ]
  },
  {
    id: 'ORD-2026-003', token: 'ghi789',
    date: '2026-07-14', status: 'Processing',
    items: [
      { name: 'Competition Practice Dress — Aurora', qty: 1, price: 8999 },
      { name: 'Arctic Grip Boot Covers', qty: 2, price: 999 }
    ],
    subtotal: 10997, shipping: 0, tax: 1979, total: 12976,
    address: { name: 'Riya Sharma', line1: '42 Frost Lane', city: 'Chandigarh', state: 'Punjab', pin: '160017' },
    tracking: null,
    timeline: [
      { status: 'Order Placed', date: '2026-07-14', done: true },
      { status: 'Payment Confirmed', date: '2026-07-14', done: true },
      { status: 'Shipped', date: '', done: false },
      { status: 'Out for Delivery', date: '', done: false },
      { status: 'Delivered', date: '', done: false },
    ]
  }
];

const ADMIN_STATS = {
  post_count: POSTS.length,
  tech_count: TECHNIQUES.reduce((sum, c) => sum + c.items.length, 0),
  product_count: PRODUCTS.length,
  gallery_count: GALLERY.length,
  unread_count: 3,
  revenue: 30885,
  order_count: ORDERS.length,
  user_count: 47,
  low_stock: PRODUCTS.filter(p => p.stock_quantity > 0 && p.stock_quantity <= 10),
};

const MESSAGES = [
  { id: 1, name: 'Ananya Patel', email: 'ananya@example.com', subject: 'Private lesson enquiry', message: 'Hi Coach, I\'m interested in booking private lessons for my daughter. She\'s 10 years old and has been skating for 2 years.', date: '2026-07-14', read: false },
  { id: 2, name: 'Vikram Singh', email: 'vikram@example.com', subject: 'Competition prep question', message: 'I have a regional competition in 3 months. Can you help me prepare a competitive program?', date: '2026-07-12', read: false },
  { id: 3, name: 'Meera Joshi', email: 'meera@example.com', subject: 'Blade sharpening recommendation', message: 'Can you recommend a good blade sharpener in the Delhi area? I\'ve been having trouble finding one who understands figure skating blades.', date: '2026-07-10', read: false },
];

const CATEGORIES = [...new Set(PRODUCTS.map(p => p.category))];
const POST_CATEGORIES = [...new Set(POSTS.map(p => p.category))];

// Cart helpers
function getCart() {
  try { return JSON.parse(localStorage.getItem('onice_cart') || '[]'); }
  catch(e) { return []; }
}
function saveCart(cart) {
  localStorage.setItem('onice_cart', JSON.stringify(cart));
  updateCartBadge();
}
function addToCart(productId, variantId) {
  const product = PRODUCTS.find(p => p.id === productId);
  if (!product || product.stock_quantity <= 0) return false;
  const cart = getCart();
  const variant = product.variants.find(v => v.id === variantId);
  cart.push({
    product_id: productId,
    variant_id: variantId || '',
    name: product.name + (variant ? ` (${variant.label})` : ''),
    price: variant ? variant.price : (product.sale_price || product.base_price),
    quantity: 1,
    image: product.image
  });
  saveCart(cart);
  return true;
}
function removeFromCart(index) {
  const cart = getCart();
  cart.splice(index, 1);
  saveCart(cart);
}
function clearCart() {
  localStorage.removeItem('onice_cart');
  updateCartBadge();
}
function updateCartBadge() {
  const badge = document.getElementById('cartBadge');
  if (!badge) return;
  const count = getCart().length;
  badge.style.display = count > 0 ? 'flex' : 'none';
  badge.textContent = count;
}
