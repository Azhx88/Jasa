import os
import re
import random

TEMPLATE_PATH = 'template.html'

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='utf-16') as f:
            return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

html = read_file(TEMPLATE_PATH)

# ========================
# LAYOUT EXTRACTION
# ========================

head_match = re.search(r'(<!DOCTYPE html>.*?<style>.*?</style>\n</head>)', html, re.DOTALL)
head_content = head_match.group(1) if head_match else ""
# Remove SPA CSS
head_content = re.sub(r'/\* SPA ROUTE SYSTEM \*/.*?\n    }', '', head_content, flags=re.DOTALL)
# Inject default scroll reveal
head_content = head_content.replace('</head>', """
  <style>
    /* Scroll Reveal */
    .reveal { opacity: 0; transform: translateY(20px); transition: all 0.6s ease-out; }
    .reveal.visible { opacity: 1; transform: translateY(0); }
  </style>
</head>""")

body_start_match = re.search(r'(<body>.*?<div class="whatsapp-float">.*?</a>\n  </div>)', html, re.DOTALL)
body_start_content = body_start_match.group(1) if body_start_match else "<body>"

nav_match = re.search(r'(<nav id="navbar">.*?</nav>)', html, re.DOTALL)
nav_content = nav_match.group(1) if nav_match else ""

footer_match = re.search(r'(<footer>.*?</footer>)', html, re.DOTALL)
footer_content = footer_match.group(1) if footer_match else ""

js_content = """
  </main>
  {footer}
  <script>
    // ─── NAV COMPACT ON SCROLL ───
    window.addEventListener('scroll', () => {
      document.getElementById('navbar').style.padding = scrollY > 65 ? '10px 60px' : '15px 60px';
    });

    // ─── FORM HANDLER ───
    function handleSubmit(e) {
      e.preventDefault();
      const b = e.target.querySelector('.submit-btn');
      if(b) {
        b.textContent = "🙏 Sent! We'll contact you soon";
        b.style.background = 'linear-gradient(135deg,#128C7E,#25D366)';
        setTimeout(() => { b.textContent = 'Send Enquiry 🙏'; b.style.background = ''; e.target.reset(); }, 3000);
      }
    }

    // ─── HAMBURGER MENU ───
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    const navItems = document.querySelectorAll('.nav-links a');

    if (hamburger) {
      hamburger.addEventListener('click', () => {
        navLinks.classList.toggle('active');
      });
    }

    navItems.forEach(item => {
      item.addEventListener('click', () => {
        navLinks.classList.remove('active');
      });
    });

    // ─── SCROLL REVEAL ───
    const revealElements = document.querySelectorAll('.reveal');
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -50px 0px' });

    revealElements.forEach(el => revealObserver.observe(el));
    
    // Quick reveal for elements already in viewport on load
    setTimeout(() => {
      document.querySelectorAll('.hero-eyebrow, .hero-title, .hero-subtitle, .hero-btns').forEach(el => {
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
      });
    }, 100);
  </script>
</body>
</html>
"""

# Extract content for each route section from template.html
routes_content = {}

# We need to extract the marquee specifically since it might be outside standard route tags
m_marquee = re.search(r'(<div class="marquee-strip">.*?</div><!-- marquee-strip -->)', html, re.DOTALL)
marquee_content = m_marquee.group(1).strip() if m_marquee else ""

for route in ['home', 'quality', 'wholesale', 'contact']:
    # The template uses data-route wrapped inside a comment <!-- ROUTE: NAME --> ... <!-- /route:name -->
    m = re.search(f'<!-- ROUTE: {route.upper()} -->(.*?)<!-- /route:{route} -->', html, re.DOTALL)
    if not m:
        # Fallback to finding <div class="route-page" data-route="...">
        m = re.search(f'<div class="route-page"[^>]*data-route="{route}"[^>]*>(.*?)</div><!-- /route:', html, re.DOTALL)
    if m:
        # Strip container if present
        c = m.group(1).strip()
        routes_content[route] = c

# Special case: Dhoop list is inside "home" or "products" depending on edits. It's usually <section id="products">
# Special case: Agarbatti list is <section id="agarbatti">
m_dhoop = re.search(r'(<section id="products".*?</section>)', html, re.DOTALL)
if m_dhoop:
    routes_content['dhoop'] = m_dhoop.group(1).strip()
else:
    # try the wrapper
    m_dhoop2 = re.search(r'<!-- ROUTE: PRODUCTS -->(.*?)<!-- /route:products -->', html, re.DOTALL | re.IGNORECASE)
    if m_dhoop2: routes_content['dhoop'] = m_dhoop2.group(1).strip()

m_agar = re.search(r'(<section id="agarbatti".*?</section>)', html, re.DOTALL)
if m_agar:
    routes_content['agarbatti'] = m_agar.group(1).strip()
else:
    m_agar2 = re.search(r'<!-- ROUTE: AGARBATTI -->(.*?)<!-- /route:agarbatti -->', html, re.DOTALL | re.IGNORECASE)
    if m_agar2: routes_content['agarbatti'] = m_agar2.group(1).strip()

# But wait, 'home' route previously contained the Hero AND dhoop AND agarbatti sections?
# If so, we should ONLY take the hero section for `index.html`.
if 'home' in routes_content:
    hc = routes_content['home']
    m_hero = re.search(r'(<section class="hero" id="home".*?</section>)', hc, re.DOTALL)
    if m_hero:
        routes_content['home'] = m_hero.group(1).strip() + "\n\n      <!-- MARQUEE -->\n      " + marquee_content

def get_template(depth, filename='', active_route=''):
    prefix = '../' * depth
    prefix_path = prefix if depth > 0 else './'
    prefix_index = prefix + 'index.html'
    
    head = head_content.replace('url(\'public/', f"url('{prefix}public/")
    
    # Fix Nav Links globally
    nav = nav_content
    # Clean up any SPA hash fragments
    nav = nav.replace('href="#/home"', f'href="{prefix_index}"')
    
    nav = nav.replace('href="#/products"', f'href="{prefix}dhoop.html"')
    nav = nav.replace('href="index.html#products"', f'href="{prefix}dhoop.html"')
    nav = nav.replace('data-route="products"', '') # remove SPA markers
    
    nav = nav.replace('href="#/agarbatti"', f'href="{prefix}agarbatti.html"')
    nav = nav.replace('href="index.html#agarbatti"', f'href="{prefix}agarbatti.html"')
    nav = nav.replace('data-route="agarbatti"', '')
    
    nav = nav.replace('href="#/quality"', f'href="{prefix}quality.html"')
    nav = nav.replace('data-route="quality"', '')
    
    nav = nav.replace('href="#/wholesale"', f'href="{prefix}wholesale.html"')
    nav = nav.replace('data-route="wholesale"', '')
    
    nav = nav.replace('href="#/contact"', f'href="{prefix}contact.html"')
    nav = nav.replace('data-route="contact"', '')
    
    nav = nav.replace('href="about.html"', f'href="{prefix}about.html"')
    nav = nav.replace('href="#/home" class="nav-logo"', f'href="{prefix_index}" class="nav-logo"')
    nav = nav.replace('data-route="home"', '')
    
    # Apply active classes manually
    nav = nav.replace('class="nav-active"', '') # strip existings
    
    if active_route == 'home':
        nav = nav.replace(f'href="{prefix_index}"', f'href="{prefix_index}" class="nav-active"')
        nav = nav.replace('class="nav-logo" class="nav-active"', 'class="nav-logo"') # fix overlap
        nav = nav.replace('class="nav-active" class="nav-logo"', 'class="nav-logo"') # fix other overlap
    elif active_route == 'dhoop':
        nav = nav.replace(f'href="{prefix}dhoop.html"', f'href="{prefix}dhoop.html" class="nav-active"')
        nav = nav.replace(f'href="{prefix}dhoop.html" class="dropbtn"', f'href="{prefix}dhoop.html" class="dropbtn nav-active"')
    elif active_route == 'agarbatti':
        nav = nav.replace(f'href="{prefix}agarbatti.html"', f'href="{prefix}agarbatti.html" class="nav-active"')
        nav = nav.replace(f'href="{prefix}dhoop.html" class="dropbtn"', f'href="{prefix}dhoop.html" class="dropbtn nav-active"')
    elif active_route == 'quality':
        nav = nav.replace(f'href="{prefix}quality.html"', f'href="{prefix}quality.html" class="nav-active"')
    elif active_route == 'wholesale':
        nav = nav.replace(f'href="{prefix}wholesale.html"', f'href="{prefix}wholesale.html" class="nav-active"')
    elif active_route == 'contact':
        nav = nav.replace(f'class="nav-cta"', f'class="nav-cta nav-active"')

    body_start = body_start_content

    footer = footer_content
    footer = footer.replace('href="#/home"', f'href="{prefix_index}"')
    footer = footer.replace('href="#/quality"', f'href="{prefix}quality.html"')
    footer = footer.replace('href="#/wholesale"', f'href="{prefix}wholesale.html"')
    footer = footer.replace('href="#/contact"', f'href="{prefix}contact.html"')
    footer = footer.replace('href="about.html"', f'href="{prefix}about.html"')
    
    footer = footer.replace('href="#/products"', f'href="{prefix}dhoop.html"')
    footer = footer.replace('href="index.html#products"', f'href="{prefix}dhoop.html"')
    footer = footer.replace('href="#/agarbatti"', f'href="{prefix}agarbatti.html"')
    footer = footer.replace('href="index.html#agarbatti"', f'href="{prefix}agarbatti.html"')

    p_js = js_content.replace('{footer}', footer)
    
    return head, body_start, nav, footer, p_js, prefix_index, prefix

def create_top_page(route_name, filename):
    print(f"Creating top-level page: {filename} from route {route_name}")
    content = routes_content.get(route_name, '')
    if not content:
        print(f"Warning: route {route_name} content not found.")
        return
        
    head, body_start, nav, _, p_js, p_index, p_asset = get_template(0, filename, route_name)
    
    # fix asset paths in content
    content = content.replace('src="public/', 'src="./public/')
    
    # Ensure inner product links use the correct dhoop/agarbatti structure if any
    content = content.replace('href="#/products"', 'href="dhoop.html"')
    content = content.replace('href="index.html#products"', 'href="dhoop.html"')
    content = content.replace('href="#/agarbatti"', 'href="agarbatti.html"')
    content = content.replace('href="index.html#agarbatti"', 'href="agarbatti.html"')
    content = content.replace('href="#/quality"', 'href="quality.html"')
    content = content.replace('href="#/wholesale"', 'href="wholesale.html"')
    content = content.replace('href="#/contact"', 'href="contact.html"')
    
    # Extra padding if it's not the hero homepage
    extra_pad = 'style="padding-top:100px"' if route_name != 'home' else ''
    
    full_html = head + body_start + nav + f'\n<main {extra_pad}>\n{content}\n' + p_js
    write_file(f'c:/Users/ashwi/.gemini/antigravity/scratch/jasa/{filename}', full_html)


def create_about_page():
    print("Creating about.html")
    head, body_start, nav, footer, js, p_index, p_asset = get_template(0, 'about.html')
    
    about_css = """
    /* About Page Styles */
    .hero-eyebrow::before, .hero-eyebrow::after { content: '✦'; color: var(--gold); font-size: .6rem; }
    .heritage-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; max-width: 1200px; margin: 0 auto; align-items: stretch; }
    .pillars-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 30px; max-width: 1200px; margin: 0 auto; margin-bottom:40px; }
    .stats-row { display: flex; justify-content: space-around; max-width: 1000px; margin: 0 auto; background: var(--card-bg); padding: 40px; border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 4px 20px rgba(100,40,10,0.05); }
    .stat-item { text-align: center; }
    .stat-item h3 { font-family: 'Cinzel Decorative', serif; font-size: 2.5rem; color: var(--gold); }
    .stat-item p { font-size: .9rem; letter-spacing: .15em; text-transform: uppercase; color: var(--mid-text); margin-top: 5px; }
    @media (max-width: 900px) {
        .heritage-grid { grid-template-columns: 1fr; }
        .pillars-grid { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 600px) {
        .pillars-grid { grid-template-columns: 1fr; }
        .stats-row { flex-direction: column; gap: 30px; }
    }
    """
    head = head.replace('</style>', about_css + '\n  </style>')
    
    content = f"""
    <!-- ABOUT HERO -->
    <section class="hero reveal" style="padding-top:160px;min-height:75vh;display:flex;align-items:center;">
        <div class="hero-content">
            <div class="hero-eyebrow" style="margin-bottom:15px;display:flex;align-items:center;justify-content:center;gap:14px;color:var(--saffron);font-size:.65rem;letter-spacing:.42em;text-transform:uppercase;">Our Sacred Story</div>
            <h1 class="hero-title" style="margin-bottom:20px;">Born From Devotion,<br><span class="highlight">Crafted With Tradition</span></h1>
            <p class="hero-subtitle" style="font-size:1.1rem;margin-bottom:40px;">For over 25 years, Jasa has carried the sacred fragrance of ancient Bharat into millions of homes, temples, and hearts across India.</p>
            <div class="hero-btns">
                <a href="{p_index}#products" class="btn-primary">Explore Our Products</a>
            </div>
        </div>
    </section>

    <!-- FOUNDING STORY -->
    <section>
        <div class="section-header">
            <div class="section-eyebrow">The Origin</div>
            <h2 class="section-title">A Journey of Faith</h2>
        </div>
        <div class="heritage-grid">
            <div class="text-col">
                <p class="prod-desc">Founded in a small workshop on the Bengaluru–Mysuru Highway, Karnataka, Jasa began with a simple mission: to preserve the authentic, unadulterated fragrances of our ancestors. It started as a family tradition of blending pure benzoin, loban, and chandan passed down from our grandparents.</p>
                <p class="prod-desc">What began by supplying local temples has now grown to serve 15,000+ customers across 28 states. Yet, our core remains identical. We do not use machines to roll our sticks, nor do we dilute our resins with harmful chemicals.</p>
                <blockquote style="font-family:'Cinzel Decorative', serif; font-size:1.5rem; color:var(--dark-text); margin:30px 0; border-left:2px solid var(--gold); padding-left:20px;">"When sambrani smoke rises, it carries our prayers directly to the divine."</blockquote>
            </div>
            <div class="img-col glass" style="display:flex;align-items:center;justify-content:center;padding:40px;border-radius:16px;">
                <svg width="120" height="120" viewBox="0 0 24 24" fill="var(--gold)"><path d="M12 2C8 6 6 9 6 12c0 3.3 2.7 6 6 6s6-2.7 6-6c0-3-2-6-6-10zM8 12c0-2.2 1.8-4 4-4s4 1.8 4 4-1.8 4-4 4-4-1.8-4-4z"/><path d="M12 20c-4.4 0-8-1.8-8-4h16c0 2.2-3.6 4-8 4z"/></svg>
            </div>
        </div>
    </section>

    <!-- OUR VALUES -->
    <section style="background:linear-gradient(to bottom, transparent, rgba(200,150,50,0.05), transparent);">
        <div class="section-header reveal">
            <div class="section-eyebrow">Our Pillars</div>
            <h2 class="section-title">What We Stand For</h2>
        </div>
        <div class="pillars-grid">
            <div class="pillar-card glass reveal" style="padding:40px 30px; border-radius:12px;">
                <div class="pillar-icon" style="margin-bottom:20px;width:40px;height:40px;"><svg viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="1.5"><path d="M12 22C12 22 4 16 4 9a8 8 0 0116 0c0 7-8 13-8 13z"/><path d="M12 22V9"/></svg></div>
                <h3 style="font-family:'Cinzel Decorative',serif;font-size:1.3rem;margin-bottom:10px;color:var(--dark-text)">Purity</h3>
                <p style="font-size:.9rem;color:var(--mid-text);line-height:1.6">Every ingredient is sourced from nature. We use zero synthetic fragrances, zero artificial binders. What you burn is exactly what the earth gave us.</p>
            </div>
            <div class="pillar-card glass reveal" style="padding:40px 30px; border-radius:12px;">
                <div class="pillar-icon" style="margin-bottom:20px;width:40px;height:40px;"><svg viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="1.5"><path d="M3 21h18M6 21V10M18 21V10"/><path d="M2 10l10-7 10 7"/></svg></div>
                <h3 style="font-family:'Cinzel Decorative',serif;font-size:1.3rem;margin-bottom:10px;color:var(--dark-text)">Tradition</h3>
                <p style="font-size:.9rem;color:var(--mid-text);line-height:1.6">Our recipes come from Vedic texts and generations of lived practice. We do not modernize what is already perfect.</p>
            </div>
            <div class="pillar-card glass reveal" style="padding:40px 30px; border-radius:12px;">
                <div class="pillar-icon" style="margin-bottom:20px;width:40px;height:40px;"><svg viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="1.5"><path d="M12 3c0 0-1 3 0 5s3 3 2 6c-1 2-3 3-3 3"/><path d="M12 3c0 0 1 3 0 5s-3 3-2 6c1 2 3 3 3 3"/><ellipse cx="12" cy="17.5" rx="4" ry="1.5"/><path d="M8 21h8"/></svg></div>
                <h3 style="font-family:'Cinzel Decorative',serif;font-size:1.3rem;margin-bottom:10px;color:var(--dark-text)">Devotion</h3>
                <p style="font-size:.9rem;color:var(--mid-text);line-height:1.6">Every batch is prepared with intention. We believe the energy of the maker enters the product — so we craft with prayer.</p>
            </div>
            <div class="pillar-card glass reveal" style="padding:40px 30px; border-radius:12px;">
                <div class="pillar-icon" style="margin-bottom:20px;width:40px;height:40px;"><svg viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="1.5"><circle cx="12" cy="7" r="4"/><path d="M5.5 21v-2a4 4 0 014-4h5a4 4 0 014 4v2"/></svg></div>
                <h3 style="font-family:'Cinzel Decorative',serif;font-size:1.3rem;margin-bottom:10px;color:var(--dark-text)">Community</h3>
                <p style="font-size:.9rem;color:var(--mid-text);line-height:1.6">We support local farmers, traditional rollers, and forest-dependent artisans. Jasa is a family that extends beyond our walls.</p>
            </div>
        </div>
    </section>

    <!-- TEAM / CRAFT -->
    <section>
        <div class="section-header reveal">
            <div class="section-eyebrow">The Hands Behind Jasa</div>
            <h2 class="section-title">Crafted by Human Hands, Not Machines</h2>
            <p style="max-width:700px;margin:20px auto;color:var(--mid-text);font-size:1.05rem;line-height:1.8;">Industrial production strips fragrance of its soul. At Jasa, our artisans still measure resins by texture and blend herbs by aroma. From the gentle hand-rolling of agarbatti to the sun-drying of our dhoop cones, human touch is our finest ingredient.</p>
        </div>
        <div style="display:flex;justify-content:center;gap:30px;margin-top:40px;font-family:'Cinzel Decorative',serif;font-size:1.2rem;color:var(--saffron);">
           <span>✦ 40+ Artisans</span>
           <span>✦ 100% Handcrafted</span>
           <span>✦ 3 Generations</span>
        </div>
    </section>

    <!-- STATS -->
    <section style="padding-top:20px;padding-bottom:100px;" class="reveal">
        <div class="stats-row">
            <div class="stat-item"><h3>25+</h3><p>Years</p></div>
            <div class="stat-item"><h3>50+</h3><p>Variants</p></div>
            <div class="stat-item"><h3>15K+</h3><p>Customers</p></div>
            <div class="stat-item"><h3>28</h3><p>States</p></div>
        </div>
    </section>

    <!-- WHOLESALE BANNER -->
    <section class="reveal">
        <div class="wholesale-banner glass" style="max-width:1100px;margin:0 auto;padding:60px 40px;text-align:center;border-radius:16px;">
            <div class="section-eyebrow">Partner with Jasa</div>
            <h2 class="section-title" style="margin-bottom:15px;font-size:2rem;">Wholesale & Bulk Supplies</h2>
            <p style="color:var(--mid-text);margin-bottom:30px;font-size:1rem;max-width:600px;margin-left:auto;margin-right:auto;">Supplying temples, ashrams, and retail stores across India with premium quality at wholesale prices.</p>
            <a href="https://wa.me/917598465053?text=I+want+wholesale+details" target="_blank" class="btn-primary">Request Wholesale Catalog</a>
        </div>
    </section>

    """
    
    full_html = head + body_start + nav + f'\n<main>\n{content}\n' + js
    write_file('c:/Users/ashwi/.gemini/antigravity/scratch/jasa/about.html', full_html)

PRODUCT_SPECS = {
    "classic-sambrani.html": {
        "type": "dhoop",
        "img": "public/002.webp",
        "cat": "Traditional Cup Series",
        "name": "Classic Sambrani Cups",
        "sub": "ಸಾಂಬ್ರಾಣಿ ಕಪ್ — Benzoin Resin Blend",
        "quals": ["100% Natural", "Long Lasting", "Traditional"],
        "desc": "The quintessential fragrance of South Indian devotion. Handcrafted using premium loban (benzoin) resin, these cups produce a rich, cleansing smoke that immediately dispels negative energy. Perfect for daily puja, hair-drying rituals, and air purification.",
        "ext_desc": "Inspired by the ancestral practice of throwing sambrani stones onto hot coals, our cup design offers the same intense fragrance with complete convenience. The cup burns evenly, releasing the unmistakable scent that defines Indian temples.",
        "specs": ["Warm Resin / Benzoin", "15–20 min per cup", "10 cups, 30 cups, 100 cups", "Home puja, temples, meditation", "Pure Benzoin Resin"]
    },
    "computer-sambrani.html": {
        "type": "dhoop",
        "img": "public/003.webp",
        "cat": "Modern Series",
        "name": "Computer Sambrani",
        "sub": "Electric Dhoop Diffuser System",
        "quals": ["Smokeless Option", "Electric Safe", "Continuous Scent"],
        "desc": "A modern evolution of traditional dhoop designed for contemporary spaces. This innovative system uses gentle heat to release the essential oils within the sambrani disc, producing a rich, continuous fragrance with almost zero smoke.",
        "ext_desc": "Perfect for closed apartments, offices, and asthma-sensitive environments. The steady release of fragrance purifies the air without overpowering the room, maintaining a subtle aura of sanctity for hours.",
        "specs": ["Soft Resin / Smokeless", "Continuous (electric)", "10 discs, 50 discs", "Apartments, offices, smoke-free spaces", "Specially formulated resin disc"]
    },
    "loban-dhoop.html": {
        "type": "dhoop",
        "img": "public/004.webp",
        "cat": "Resin Collection",
        "name": "Loban Dhoop Sticks",
        "sub": "Pure Frankincense — Benzoin Blend",
        "quals": ["Anti-Bacterial", "Vastu Cleansing", "Deep Aroma"],
        "desc": "Thick, potent dhoop sticks densely packed with pure loban resin. Revered in Ayurvedic and Sufi traditions for its unmatched ability to clear heavy energies and purify stagnant air, bringing a deep, grounding atmosphere to any space.",
        "ext_desc": "The smoke of loban is known for its antimicrobial properties. We hand-blend the crushed resin with an earthy base to ensure a steady, consistent burn that fills large halls and courtyards effortlessly.",
        "specs": ["Deep Frankincense / Earthy", "40–45 min per stick", "10 sticks, 25 sticks, 100 sticks", "Daily puja, vastu cleansing, meditation", "Pure Loban (Benzoin) Resin"]
    },
    "kesar-rose-sambrani.html": {
        "type": "dhoop",
        "img": "public/005.webp",
        "cat": "Floral Series",
        "name": "Kesar Rose Sambrani",
        "sub": "Saffron & Rose Petal Infusion",
        "quals": ["Kesar Infused", "Gift Box", "Festive Special"],
        "desc": "An indulgent, regal blend combining the fiery warmth of pure kesar (saffron) with the sweet devotion of Indian rose petals. This sambrani cup creates a luxurious, uplifting fragrance reserved for special prayers and celebrations.",
        "ext_desc": "Often chosen for weddings, housewarmings, and Diwali poojas, this blend carries the essence of abundance. The delicate saffron notes linger long after the cup has finished burning.",
        "specs": ["Floral / Saffron-Rose", "15–18 min per cup", "10 cups, 30 cups", "Weddings, festivals, gifting, special puja", "Saffron strands + Rose petals"]
    },
    "gugal-dhoop-cones.html": {
        "type": "dhoop",
        "img": "public/006.webp",
        "cat": "Herbal Series",
        "name": "Gugal Dhoop Cones",
        "sub": "Sacred Commiphora Mukul Blend",
        "quals": ["Ayurvedic", "Air Purifying", "Stress Relief"],
        "desc": "Crafted from authentic Guggulu (Commiphora mukul) resin, these dhoop cones carry the profound, sacred fragrance of ancient yagnas. Known to calm the nervous system and induce deep meditative states.",
        "ext_desc": "Gugal has been burned in Indian homes since antiquity to ward off negativity and promote healing. Our cones are dense, slow-burning, and entirely free of synthetic fillers.",
        "specs": ["Earthy / Sacred Resin", "20–25 min per cone", "12 cones, 36 cones, 108 cones", "Spiritual practice, temples, stress relief", "Commiphora Mukul (Gugal) Resin"]
    },
    "chandan-sambrani-powder.html": {
        "type": "dhoop",
        "img": "public/007.webp",
        "cat": "Wood Series",
        "name": "Chandan Sambrani Powder",
        "sub": "Sandalwood & Sambrani Fusion",
        "quals": ["Pure Sandalwood", "Meditation Grade", "Bulk Pack Available"],
        "desc": "A remarkable fusion of finely ground Mysore sandalwood dust and premium sambrani resin. This powder is designed to be sprinkled over hot coals, releasing an instantly divine, creamy-woody fragrance that elevates consciousness.",
        "ext_desc": "The immediate release of smoke from this powder makes it ideal for rapid room cleansing or large temple gatherings where an instant spiritual atmosphere is required.",
        "specs": ["Woody / Sandalwood", "Varies by quantity", "50g, 100g, 500g, 1kg", "Meditation halls, bulk temple supply, daily puja", "Mysore Sandalwood + Sambrani Resin"]
    },
    "marikolunthu.html": {
        "type": "agarbatti",
        "img": "public/111.webp",
        "cat": "Herbal Series",
        "name": "Marikolunthu Agarbatti",
        "sub": "Plectranthus amboinicus — Sacred Herb Sticks",
        "quals": ["Herbal Blend", "Temple Grade", "Long Lasting"],
        "desc": "Marikolunthu — the sacred Indian borage — is a revered herb in South Indian temple traditions. Its warm, earthy, camphor-like fragrance purifies spaces, invokes blessings, and deepens meditation. Handrolled with pure herb extract and natural binding. A true offering of nature's sanctity.",
        "ext_desc": "Traditionally woven into garlands for deities, this unique botanical brings a deeply traditional, green freshness to the air. Highly recommended for morning prayers.",
        "specs": ["Herbal / Camphor-Earthy", "30–35 min per stick", "10 sticks, 25 sticks, 100 sticks", "Temple offerings, meditation, air purification", "Plectranthus amboinicus herb extract"]
    },
    "jasmine.html": {
        "type": "agarbatti",
        "img": "public/222.webp",
        "cat": "Floral Series",
        "name": "Jasmine Agarbatti",
        "sub": "Mallipoo — South Indian Jasmine Sticks",
        "quals": ["Pure Floral", "Uplifting", "Morning Puja"],
        "desc": "The intoxicating essence of fresh Mallipoo (South Indian Jasmine) captured in a slow-burning stick. This Agarbatti releases a rich, sweet, devotional fragrance that has graced temple offerings and bridal ceremonies for centuries. Ideal for morning and evening puja, meditation, and sacred rituals.",
        "ext_desc": "Jasmine has a profound effect on the mind, inducing optimism and peace. Our extraction process ensures the truest representation of blooming jasmine flowers.",
        "specs": ["Sweet Floral / Jasmine", "30–35 min per stick", "10 sticks, 25 sticks, 100 sticks", "Morning puja, bridal ceremonies, daily devotion", "Pure Mallipoo Jasmine extract"]
    },
    "rose.html": {
        "type": "agarbatti",
        "img": "public/333.webp",
        "cat": "Floral Series",
        "name": "Rose Agarbatti",
        "sub": "Gulab — Rose Petal Incense Sticks",
        "quals": ["Pure Rose", "Romantic", "Deity Offering"],
        "desc": "A tribute to the divine flower. Made from deeply fragrant Indian rose petals and essential oils, this Agarbatti fills any space with the warm, timeless fragrance of the Gulab. Beloved for daily puja, offerings to deities, and creating a serene atmosphere in homes and temples.",
        "ext_desc": "Rose frequency aligns with the heart chakra, making this incense a perfect choice for heart-centered meditation or creating an atmosphere of unconditional love in the home.",
        "specs": ["Warm Floral / Rose", "30–35 min per stick", "10 sticks, 25 sticks, 100 sticks", "Daily puja, deity offerings, home fragrance", "Rose petal extract + masala base"]
    },
    "sandal.html": {
        "type": "agarbatti",
        "img": "public/444.webp",
        "cat": "Classic Series",
        "name": "Sandal Agarbatti",
        "sub": "Chandan — Pure Sandalwood Incense Sticks",
        "quals": ["Pure Sandalwood", "Temple Standard", "Woody"],
        "desc": "The crown jewel of Indian fragrances. Our premium Sandalwood sticks are made with authentic Mysore sandalwood extract, offering a deep, creamy, meditative aroma that has accompanied prayers for millennia. Every stick is a bridge between the earthly and the divine.",
        "ext_desc": "Sandalwood cools the mind and grounds the spirit. Highly recommended for intense focus, study, or any spiritual discipline requiring deep concentration.",
        "specs": ["Creamy / Woody Sandalwood", "35–40 min per stick", "10 sticks, 25 sticks, 100 sticks", "Meditation, premium puja, temple supply", "Mysore Sandalwood extract"]
    },
    "pineapple.html": {
        "type": "agarbatti",
        "img": "public/555.webp",
        "cat": "Fruity Series",
        "name": "Pineapple Agarbatti",
        "sub": "Tropical — Pineapple Incense Sticks",
        "quals": ["Tropical Scent", "Fresh", "Festive Aroma"],
        "desc": "A surprisingly sweet, uplifting, and refreshing twist on traditional incense. The vibrant, juicy scent of pineapple creates an instantly welcoming and cheerful fragrance that brightens living spaces and mood. Perfect for homes, gifting, and festive occasions.",
        "ext_desc": "This delightfully unexpected aroma bridges traditional incense crafting with a modern, fruity profile. Loved by younger generations and perfect for casual home fragrancing.",
        "specs": ["Fresh / Tropical Fruity", "25–30 min per stick", "10 sticks, 25 sticks, 100 sticks", "Home fragrance, gifting, festive occasions", "Pineapple fragrance + natural base"]
    },
    "natural.html": {
        "type": "agarbatti",
        "img": "public/666.webp",
        "cat": "Pure Series",
        "name": "Natural Agarbatti",
        "sub": "Masala Sticks — 100% Natural Blend",
        "quals": ["Zero Chemicals", "Eco-Friendly", "Soft Aroma"],
        "desc": "For those seeking the absolute purest burn. These un-perfumed, rustic masala sticks contain only crushed herbs, barks, and natural resins. Highly recommended for children, elderly, and those sensitive to chemical fragrances. Clean burning, minimal smoke, maximum sanctity.",
        "ext_desc": "Visually distinct with its coarse, masala-coated texture. The scent profile is incredibly earthy, reminiscent of a forest floor after the first monsoon rains.",
        "specs": ["Earthy / Pure Herbal", "30–35 min per stick", "10 sticks, 25 sticks, 100 sticks", "Allergy-sensitive users, children, eco-conscious homes", "Wild herbs + natural resin blend"]
    },
    "royal.html": {
        "type": "agarbatti",
        "img": "public/777.webp",
        "cat": "Premium Series",
        "name": "Royal Agarbatti",
        "sub": "Shahi — Premium Luxury Incense Sticks",
        "quals": ["Premium Blend", "Long Burning", "Luxury Scent"],
        "desc": "Our most majestic creation. The Royal blend is an opulent, rich mix of rare resins, musk undertones, saffron, and aged agarwood/sandalwood. Each Royal stick burns for over an hour, releasing a complex, majestic fragrance suited for special occasions, gifting, and premium pooja rooms.",
        "ext_desc": "Formulated for connoisseurs of fine incense. The scent evolves dynamically as it burns, layering sweet, woody, and spicy notes throughout the room.",
        "specs": ["Complex / Oud-Musk-Saffron", "55–65 min per stick", "6 sticks, 12 sticks, 50 sticks", "Special occasions, luxury gifting, premium puja rooms", "Oud + Musk + Saffron + Sandalwood blend"]
    },
    "traditional.html": {
        "type": "agarbatti",
        "img": "public/888.webp",
        "cat": "Heritage Series",
        "name": "Traditional Agarbatti",
        "sub": "Parambarai — Ancestral Recipe Sticks",
        "quals": ["Ancient Recipe", "Devotional", "Authentic"],
        "desc": "Crafted exactly as it was 50 years ago. This robust, potent fragrance relies on a closely guarded family recipe. The thick, dark sticks are heavily coated in a resinous masala. The heavy base of benzoin, vetiver, tulsi, and neem bark creates an unmistakably authentic fragrance.",
        "ext_desc": "This is the fragrance of old India—uncompromising, strong, and deeply evocative of grand temple corridors and ancestral homes.",
        "specs": ["Ancestral / Resin-Herb", "35–40 min per stick", "10 sticks, 25 sticks, 100 sticks", "Temple supply, daily puja, heritage lovers", "Benzoin + Vetiver + Tulsi + Neem bark"]
    }
}

def create_product_page(file_path):
    print(f"Creating product page: {file_path}")
    depth = file_path.count('/')
    spec = PRODUCT_SPECS[file_path]
    head, body_start, nav, footer, js, p_index, p_asset = get_template(depth, '', spec.get('type'))
    
    is_dhoop = spec.get('type') == 'dhoop'
    
    prod_css = """
    /* Product Page Specific Styles */
    .prod-breadcrumb { font-size: .85rem; color: var(--gold); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 20px; font-weight: 600; display:flex; align-items:center; gap:8px;}
    .prod-breadcrumb a { color: var(--gold); text-decoration: none; transition: color 0.2s; }
    .prod-breadcrumb a:hover { color: var(--saffron); }
    
    .product-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; max-width: 1200px; margin: 0 auto; align-items: start; }
    
    .prod-detail-img { min-height: 480px; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
    .prod-thumb-row { display: flex; gap: 10px; margin-top: 15px; }
    .prod-thumb { width: 80px; height: 80px; border-radius: 8px; background: var(--card-bg); border: 1px solid var(--border); transition: 0.2s border; overflow: hidden; }
    
    .prod-meta-row { margin: 25px 0; display: flex; gap: 10px; flex-wrap: wrap; }
    .meta-pill { font-size: 0.75rem; background: rgba(200, 150, 40, 0.1); color: var(--dark-text); padding: 5px 12px; border-radius: 20px; border: 1px solid var(--gold); letter-spacing: 0.5px; }
    
    .prod-specs { width: 100%; border-collapse: collapse; margin-top: 30px; font-size: 0.9rem; }
    .prod-specs tr { border-bottom: 1px solid var(--border); }
    .prod-specs td { padding: 12px 0; color: var(--mid-text); }
    .prod-specs td:first-child { font-weight: 600; color: var(--dark-text); width: 35%; }
    
    .use-step-card-row { display: flex; gap: 30px; max-width: 1100px; margin: 0 auto; }
    .use-step-card { flex: 1; min-width: 250px; padding: 40px 30px; border-radius: 12px; border: 1px solid var(--border); text-align: center; }
    .use-step-icon { width: 50px; height: 50px; background: rgba(200,150,20,0.1); color: var(--gold); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 1.2rem; font-weight: bold; border: 1px solid var(--gold); }
    
    .related-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; max-width: 1100px; margin: 0 auto; }
    
    .btn-secondary { background: transparent; color: var(--dark-text); border: 1px solid var(--gold); padding: 14px 42px; font-family: 'Noto Serif', serif; font-size: .79rem; letter-spacing: .2em; text-transform: uppercase; cursor: pointer; transition: all .3s; text-decoration: none; display: inline-flex; justify-content: center; align-items: center; }
    .btn-secondary:hover { background: rgba(200,150,20,0.05); transform: translateY(-3px); box-shadow: 0 10px 30px var(--card-shadow); }

    @media (max-width: 900px) {
        .product-detail-grid { grid-template-columns: 1fr; }
        .use-step-card-row { flex-direction: column; }
        .related-grid { grid-template-columns: 1fr; }
    }
    """
    head = head.replace('</style>', prod_css + '\n  </style>')
    
    # Pick 3 related products
    all_keys = list(PRODUCT_SPECS.keys())
    all_keys.remove(file_path)
    related = random.sample(all_keys, 3)
    
    related_html = ""
    for r_path in related:
        r_spec = PRODUCT_SPECS[r_path]
        rel_link = f"{p_asset}{r_path}"
        
        related_html += f"""
            <div class="pillar-card glass" style="padding:30px; border-radius:12px; text-align:center;">
                <h3 style="font-family:'Cinzel Decorative',serif;font-size:1.3rem;margin-bottom:10px;color:var(--dark-text)">{r_spec['name']}</h3>
                <p style="font-size:.9rem;color:var(--mid-text);margin-bottom:20px;">{r_spec['sub']}</p>
                <a href="{rel_link}" style="text-decoration:none; color:var(--saffron); font-size:0.8rem; letter-spacing:1px; text-transform:uppercase; border-bottom:1px solid var(--saffron); padding-bottom:3px;">View Product</a>
            </div>
        """
    
    # use correct base image (e.g. 111.webp, 222.webp) loosely inferred. 
    # the user already populated images in earlier index HTML. We leave image href as empty string for now, but ideally we match what was there.
    # To avoid changing user's work, we leave it as previous template pattern
    
    content = f"""
    <!-- PRODUCT HERO -->
    <section class="hero reveal" style="padding-top:160px; min-height:50vh; display:flex; align-items:center;">
        <div class="hero-content">
            <div class="prod-breadcrumb">
                <a href="{p_index}">Home</a> <span>/</span> <a href="{p_asset}{'dhoop.html' if is_dhoop else 'agarbatti.html'}">{'Dhoop' if is_dhoop else 'Agarbatti'}</a> <span>/</span> <span style="color:var(--dark-text);">{spec['name']}</span>
            </div>
            <div class="hero-eyebrow" style="margin-top:20px; margin-bottom:15px;display:flex;align-items:center;justify-content:center;gap:14px;color:var(--saffron);font-size:.65rem;letter-spacing:.42em;text-transform:uppercase;">{spec['cat']}</div>
            <h1 class="hero-title" style="font-size: clamp(2rem, 5vw, 4.5rem); margin-bottom:20px;">{spec['name']}</h1>
            <p class="hero-subtitle" style="font-family: 'Cormorant Garamond', serif; font-style: italic; font-size:1.2rem; color:var(--light-text); font-weight:700; margin-bottom:35px;">{spec['sub']}</p>
            <div class="hero-btns" style="margin-top: 30px;">
                <a href="https://wa.me/917598465053?text=I+want+to+order+{spec['name'].replace(' ', '+')}" target="_blank" class="btn-primary" style="background: linear-gradient(135deg, #128C7E, #25D366); box-shadow: 0 4px 15px rgba(18,140,126,0.3); border:none;">Order on WhatsApp</a>
                <a href="{p_asset}{'dhoop.html' if is_dhoop else 'agarbatti.html'}" class="btn-secondary">Back to All Products</a>
            </div>
        </div>
    </section>

    <!-- PRODUCT DETAILS -->
    <section>
        <div class="product-detail-grid">
            <div class="product-img-panel reveal">
                <div class="prod-detail-img">
                    <img src="{p_asset}{spec['img']}" alt="{spec['name']}" style="width:100%;height:100%;object-fit:cover;border-radius:16px;display:block;">
                </div>
                <!-- Optional thumbs removed for purity -->
            </div>
            
            <div class="product-info-panel reveal" style="transition-delay: 0.1s;">
                <h2 style="font-family:'Cinzel Decorative',serif;font-size:2.2rem;color:var(--dark-text);margin-bottom:8px;">{spec['name']}</h2>
                <div style="font-family:'Cormorant Garamond',serif;font-style:italic;font-size:1.15rem;color:var(--light-text);margin-bottom:25px;font-weight:700;">{spec['sub']}</div>
                
                <div class="prod-divider" style="margin-bottom:25px; width:60px; height:1px; background:var(--gold);"></div>
                
                <div class="prod-qualities" style="margin-bottom:25px; display:flex; gap:8px; flex-wrap:wrap;">
                    {''.join(f'<span class="q-tag" style="font-size:0.7rem; padding:4px 12px; border:1px solid var(--gold); border-radius:20px; text-transform:uppercase; letter-spacing:1px;">{q}</span>' for q in spec['quals'])}
                </div>
                
                <div class="prod-meta-row">
                    <span class="meta-pill">Retail & Wholesale</span>
                    <span class="meta-pill">Pan India Delivery</span>
                    <span class="meta-pill">Custom Bulk Orders</span>
                </div>
                
                <p style="font-size:.95rem;color:var(--mid-text);line-height:1.8;margin-bottom:20px;">{spec['desc']}</p>
                <p style="font-size:.95rem;color:var(--mid-text);line-height:1.8;margin-bottom:35px;">{spec['ext_desc']}</p>
                
                <h3 style="font-family:'Cinzel Decorative',serif;font-size:1.1rem;color:var(--dark-text);margin-bottom:15px; border-bottom:1px solid var(--border); padding-bottom:10px;">Specifications</h3>
                <table class="prod-specs">
                    <tr><td>Fragrance Type</td><td>{spec['specs'][0]}</td></tr>
                    <tr><td>Burn Time</td><td>{spec['specs'][1]}</td></tr>
                    <tr><td>Pack Sizes</td><td>{spec['specs'][2]}</td></tr>
                    <tr><td>Best For</td><td>{spec['specs'][3]}</td></tr>
                    <tr><td>Key Ingredient</td><td>{spec['specs'][4]}</td></tr>
                </table>
                
                <div style="margin-top: 45px;">
                    <a href="https://wa.me/917598465053?text=I+want+to+order+{spec['name'].replace(' ', '+')}" target="_blank" class="btn-primary" style="display:block;width:100%;text-align:center;font-size:.9rem;padding:18px;">Enquire / Order Now</a>
                </div>
            </div>
        </div>
    </section>

    <!-- RITUAL GUIDE -->
    <section class="reveal" style="background:linear-gradient(to bottom, transparent, rgba(200,150,50,0.05), transparent);">
        <div class="section-header">
            <div class="section-eyebrow">Ritual Guide</div>
            <h2 class="section-title">How to Use {spec['name'].split()[0]}</h2>
        </div>
        <div class="use-step-card-row">
            <div class="use-step-card glass reveal">
                <div class="use-step-icon">1</div>
                <h3 style="font-family:'Cinzel Decorative',serif;color:var(--dark-text);margin-bottom:12px;">Prepare</h3>
                <p style="color:var(--mid-text);font-size:0.95rem;line-height:1.6;">Light the tip carefully until it glows red carefully. Place it securely on a fire-proof stand.</p>
            </div>
            <div class="use-step-card glass reveal" style="transition-delay:0.15s;">
                <div class="use-step-icon">2</div>
                <h3 style="font-family:'Cinzel Decorative',serif;color:var(--dark-text);margin-bottom:12px;">Intend</h3>
                <p style="color:var(--mid-text);font-size:0.95rem;line-height:1.6;">Close your eyes and breathe deeply. Set your prayer, manifestation, or personal intention.</p>
            </div>
            <div class="use-step-card glass reveal" style="transition-delay:0.3s;">
                <div class="use-step-icon">3</div>
                <h3 style="font-family:'Cinzel Decorative',serif;color:var(--dark-text);margin-bottom:12px;">Offer</h3>
                <p style="color:var(--mid-text);font-size:0.95rem;line-height:1.6;">Gently guide the sacred smoke around your space, letting the aroma elevate the environment's energy.</p>
            </div>
        </div>
    </section>

    <!-- RELATED PRODUCTS -->
    <section>
        <div class="section-header reveal">
            <div class="section-eyebrow">You May Also Like</div>
            <h2 class="section-title">Explore More Sacred Fragrances</h2>
        </div>
        <div class="related-grid reveal">
            {related_html}
        </div>
    </section>

    <!-- WHOLESALE BANNER -->
    <section class="reveal">
        <div class="wholesale-banner glass" style="max-width:1100px;margin:0 auto;padding:60px 40px;text-align:center;border-radius:16px;">
            <div class="section-eyebrow">Partner with Jasa</div>
            <h2 class="section-title" style="margin-bottom:15px;font-size:2rem;">Wholesale & Bulk Supplies</h2>
            <p style="color:var(--mid-text);margin-bottom:30px;font-size:1rem;max-width:600px;margin-left:auto;margin-right:auto;">Supplying temples, ashrams, and retail stores across India with premium quality at wholesale prices.</p>
            <a href="https://wa.me/917598465053?text=I+want+wholesale+details" target="_blank" class="btn-primary">Request Wholesale Catalog</a>
        </div>
    </section>
    """

    full_html = head + body_start + nav + f'\n<main>\n{content}\n' + js
    write_file(f'c:/Users/ashwi/.gemini/antigravity/scratch/jasa/{file_path}', full_html)

if __name__ == '__main__':
    print("Extracting SPA Routes...")
    create_top_page('home', 'index.html')
    create_top_page('dhoop', 'dhoop.html')
    create_top_page('agarbatti', 'agarbatti.html')
    create_top_page('quality', 'quality.html')
    create_top_page('wholesale', 'wholesale.html')
    create_top_page('contact', 'contact.html')
    
    create_about_page()
    for file_path in PRODUCT_SPECS.keys():
        create_product_page(file_path)
    print("Done generating pages successfully.")
