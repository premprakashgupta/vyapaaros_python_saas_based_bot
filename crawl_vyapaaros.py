"""
crawl_vyapaaros.py
------------------
Run with the project venv:
    venv\Scripts\python.exe crawl_vyapaaros.py

Uses the project's own IngestionEngine + VectorRAGEngine to crawl
vyapaaros.in and save everything to the superadmin's business.
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vyapaaros_core.settings")
django.setup()

from django.contrib.auth.models import User
from agent_engine.models import BusinessClient, ClientAPIKey
from agent_engine.ingestion import IngestionEngine
from agent_engine.vector_service import VectorRAGEngine

TARGET_URL = "https://vyapaaros.in"
MAX_PAGES  = 20

# ─── 1. Find (or create) the superadmin's BusinessClient ─────────────────────
su = User.objects.filter(is_superuser=True).order_by("date_joined").first()
if not su:
    print("No superuser found. Create one with: manage.py createsuperuser")
    exit(1)

print(f"Superuser: {su.username}")

biz, created = BusinessClient.objects.get_or_create(
    user=su,
    defaults={
        "name":            "VyapaarOS HQ",
        "brand_color":     "#F2541B",
        "bot_name":        "VyapaarOS Executive",
        "welcome_message": "Hello! Welcome to VyapaarOS. How can I assist your business today?",
        "owner_whatsapp":  "919955804730",
        "website_url":     TARGET_URL,
    }
)

if created:
    print(f"Created new BusinessClient: {biz.name}")
    ClientAPIKey.objects.get_or_create(client=biz)
else:
    print(f"Found BusinessClient: {biz.name}  (id={biz.id})")
    if biz.website_url != TARGET_URL:
        biz.website_url = TARGET_URL
        biz.save(update_fields=["website_url"])
        print(f"Updated website_url to {TARGET_URL}")

# ─── 2. Crawl vyapaaros.in ───────────────────────────────────────────────────
print(f"\nCrawling {TARGET_URL} (max {MAX_PAGES} pages) ...")

docs = IngestionEngine.crawl_website(biz, max_pages=MAX_PAGES)

# ─── 3. Index into ChromaDB ──────────────────────────────────────────────────
print(f"\nIndexing {len(docs)} pages into Vector DB ...")
for i, doc in enumerate(docs, 1):
    VectorRAGEngine.add_or_update_document(biz, doc)
    print(f"  [{i}/{len(docs)}] {doc.page_title[:80]}")

# ─── 4. Done ─────────────────────────────────────────────────────────────────
print(f"\nDone! {len(docs)} pages crawled and indexed for business: {biz.name}")
