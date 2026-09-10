"""
seed_vyapaaros_services.py
--------------------------
Run with project venv:
    venv\Scripts\python.exe seed_vyapaaros_services.py

Seeds all VyapaarOS services into the superadmin's BusinessClient
and indexes them into the ChromaDB vector store.
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vyapaaros_core.settings")
django.setup()

from django.contrib.auth.models import User
from agent_engine.models import BusinessClient, KnowledgeDocument
from agent_engine.vector_service import VectorRAGEngine

# ─── Find superadmin's business ───────────────────────────────────────────────
su = User.objects.filter(is_superuser=True).order_by("date_joined").first()
biz = BusinessClient.objects.filter(user=su).first()

if not biz:
    print("No VyapaarOS HQ business found. Run crawl_vyapaaros.py first.")
    exit(1)

print(f"Seeding services for: {biz.name}\n")

# ─── Service Definitions ──────────────────────────────────────────────────────
SERVICES = [
    {
        "title": "Business Portfolio Website",
        "content": """Product Name: Business Portfolio Website
Category: Web Development
Price (INR): Starting from 4999
Special Offer: Free Hosting + Free SSL Certificate included
Turnaround: 5-7 working days
Product Details: A stunning, professional business portfolio website built to impress your clients and grow your brand online. Perfect for freelancers, consultants, small businesses, and startups.
Features:
- Dark Mode & Light Mode toggle (user preference saved)
- 100% Mobile Responsive design (works perfectly on all screen sizes)
- Free SSL Certificate (HTTPS security, builds customer trust)
- Free Hosting for 1 year
- SEO-ready structure (helps in Google ranking)
- Fast loading speed (optimized performance)
- Contact form with WhatsApp integration
- Google Analytics setup
- Modern animations and premium UI design
- Easy content update support
Technology: HTML / CSS / JavaScript / React or Next.js (as per requirement)
Image URL: https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?auto=format&fit=crop&w=600&q=80"""
    },
    {
        "title": "Web Development (Custom Website)",
        "content": """Product Name: Custom Web Development
Category: Web Development
Price (INR): Starting from 7999
Turnaround: 7-14 working days
Product Details: Full-stack custom web development for businesses that need more than a portfolio — including e-commerce, service booking, admin panels, and complex web applications.
Features:
- Custom design as per brand guidelines
- E-commerce / Product catalog with payment gateway
- Admin dashboard to manage content
- Database integration (PostgreSQL / MySQL)
- APIs using Node.js
- User authentication & role management
- Cloud deployment (AWS / DigitalOcean / Hostinger)
- 3 months free maintenance support
Technology: Node.js / React / Next.js / Django / PostgreSQL
Special Offer: Free domain (.in) for first year on orders above 14999
Image URL: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=600&q=80"""
    },
    {
        "title": "Mobile App Development",
        "content": """Product Name: Mobile App Development
Category: Mobile Development
Price (INR): Starting from 24999
Turnaround: 21-45 working days
Product Details: Cross-platform mobile app development for Android and iOS. We build fast, beautiful, and scalable apps for businesses of all sizes.
Features:
- Android + iOS both (single codebase using Flutter/React Native)
- Custom UI/UX design
- Push notifications
- Backend API integration
- Payment gateway (Razorpay / PayU / Stripe)
- Admin panel to manage app content
- Google Play Store & Apple App Store submission
- Real-time features (chat, live tracking, etc.)
- 3 months post-launch support
Technology: Flutter / React Native / Firebase / Node.js
Special Offer: Free UI/UX wireframe design before development starts
Image URL: https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?auto=format&fit=crop&w=600&q=80"""
    },
    {
        "title": "AI Chatbot Development (Like VyapaarOS Bot)",
        "content": """Product Name: AI Chatbot Development
Category: AI & Automation
Price (INR): Starting from 9999 per month
Special Offer: 7-day free trial available
Turnaround: 3-5 working days setup
Product Details: We build intelligent AI-powered sales chatbots for your website — just like this bot! The bot automatically handles customer queries, captures leads, shares product info, and connects customers to WhatsApp — 24/7, even when you're asleep.
Features:
- Aapke business se related hi accurate replies diye jaate hain (Strict Domain Knowledge Guardrails)
- AI trained on your business data (products, services, FAQs, pricing)
- WhatsApp lead capture and instant handoff
- Multi-language support (Hindi, English, Hinglish)
- Embeds on ANY website with 1 line of code
- Branded with your colors, logo, bot name
- Real-time lead management dashboard
- Product catalog with image display
- Context-aware conversation memory
- Fast, secure & intelligent AI responses
- Monthly analytics report
Plans:
- Starter (1 bot, up to 500 chats/month): Rs. 9999/month
- Growth (1 bot, unlimited chats): Rs. 14999/month
- Agency (5 bots, white-label): Rs. 34999/month
Image URL: https://images.unsplash.com/photo-1531746790731-6c087fecd65a?auto=format&fit=crop&w=600&q=80"""
    },
    {
        "title": "SEO, AEO & GEO Optimization",
        "content": """Product Name: SEO, AEO & GEO Optimization
Category: Digital Marketing
Price (INR): Starting from 4999 per month
Special Offer: Free website audit report worth Rs. 1999 on signup
Turnaround: Results visible in 60-90 days
Product Details: Complete search visibility package covering traditional SEO (Google search), AEO (Answer Engine Optimization for AI tools like ChatGPT, Perplexity), and GEO (Generative Engine Optimization for AI overviews).
Services Included:
SEO (Search Engine Optimization):
- Keyword research & strategy
- On-page SEO (meta tags, headers, schema)
- Technical SEO (site speed, mobile-first, Core Web Vitals)
- Backlink building
- Monthly ranking report

AEO (Answer Engine Optimization):
- Optimize content for featured snippets
- FAQ schema markup
- Voice search optimization
- Structured data for AI assistants (Alexa, Siri, Google Assistant)

GEO (Generative Engine Optimization):
- Optimize business to appear in ChatGPT / Gemini / Perplexity answers
- Brand entity building
- E-E-A-T signals improvement
- AI citation strategy

Monthly Deliverables:
- Keyword ranking report
- Traffic analytics (Google Analytics + Search Console)
- Content suggestions
- Competitor analysis
Image URL: https://images.unsplash.com/photo-1562577309-4932fdd64cd1?auto=format&fit=crop&w=600&q=80"""
    },
    {
        "title": "Google Business Profile Ranking & Management",
        "content": """Product Name: Google Business Profile Ranking
Category: Local SEO & Google Ranking
Price (INR): Starting from 2999 per month
Special Offer: Free Google Business Profile setup (worth Rs. 999) for new clients
Turnaround: Visible improvement in 30-60 days
Product Details: Get your business on TOP of Google Maps and local search results. We optimize, manage, and rank your Google Business Profile so more local customers find you.
Services Included:
- Google Business Profile (GBP) setup & verification
- Category & attribute optimization
- Photo & video optimization (high-quality uploads)
- Post scheduling (weekly Google Posts)
- Review management & reply strategy
- Q&A section optimization
- Local citation building (Justdial, Sulekha, IndiaMART listing)
- NAP consistency check across web
- Competitor analysis
- Monthly performance report (calls, directions, views)
Results We Deliver:
- Appear in Google Map Pack (top 3 local results)
- Increase in calls & direction requests
- More walk-in customers
- Better brand trust via reviews
Image URL: https://images.unsplash.com/photo-1611162617474-5b21e879e113?auto=format&fit=crop&w=600&q=80"""
    },
]

# ─── Seed into DB + Vector Store ──────────────────────────────────────────────
print(f"Adding {len(SERVICES)} services...\n")

for i, svc in enumerate(SERVICES, 1):
    doc, created = KnowledgeDocument.objects.update_or_create(
        client=biz,
        page_title=svc["title"],
        defaults={
            "content_text": svc["content"],
            "content_type": "product_catalog",
            "is_active": True,
        }
    )
    VectorRAGEngine.add_or_update_document(biz, doc)
    status = "Created" if created else "Updated"
    print(f"  [{i}/{len(SERVICES)}] {status}: {svc['title']}")

print(f"\nDone! {len(SERVICES)} services seeded & indexed for {biz.name}")
print(f"Open dashboard to verify: http://127.0.0.1:8000/dashboard/")
