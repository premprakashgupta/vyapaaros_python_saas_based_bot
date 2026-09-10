"""
seed_demo_clients.py
--------------------
Seeds complete real-world demo businesses along with their FULL dataset:
1. Vastra Fashion Collection -> Imports ALL 300+ Products from sample_vastra_300_clothing_catalog.csv
2. Digital Point Cyber Cafe -> Imports ALL Rate Cards from sample_cyber_cafe_rate_card.csv
3. Luxe Interiors & Living -> Imports Home Decor & Furniture Products
"""

import os
import sys
import csv
import django

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vyapaaros_core.settings")
django.setup()

from django.contrib.auth.models import User
from agent_engine.models import BusinessClient, ClientAPIKey, KnowledgeDocument
from agent_engine.vector_service import VectorRAGEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DOCS_DIR = os.path.join(BASE_DIR, "sample_docs")

def seed_vastra_300_catalog(client):
    csv_path = os.path.join(SAMPLE_DOCS_DIR, "sample_vastra_300_clothing_catalog.csv")
    if not os.path.exists(csv_path):
        print(f"⚠️ Warning: {csv_path} not found!")
        return 0

    count = 0
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("product_name") or row.get("title") or f"Product {row.get('sku', '')}"
            category = row.get("category", "Clothing")
            fabric = row.get("fabric", "")
            color = row.get("color", "")
            size = row.get("size", "")
            price = row.get("price_inr", "")
            offer = row.get("special_offer", "")
            details = row.get("product_details", "")
            
            content = f"Product Name: {title}\nCategory: {category}\nPrice (INR): {price}\n"
            if offer:
                content += f"Special Offer: {offer}\n"
            if fabric:
                content += f"Fabric: {fabric}\n"
            if color:
                content += f"Color: {color}\n"
            if size:
                content += f"Available Sizes: {size}\n"
            if details:
                content += f"Product Details: {details}\n"
            
            # Add Unsplash ethnic clothing image
            content += "Image URL: https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=600&q=80\n"

            doc, _ = KnowledgeDocument.objects.update_or_create(
                client=client,
                page_title=title,
                defaults={
                    "content_text": content.strip(),
                    "content_type": "product_catalog",
                    "is_active": True,
                }
            )
            VectorRAGEngine.add_or_update_document(client, doc)
            count += 1
            if count % 50 == 0:
                print(f"   Indexed {count}/300 products into AI Vector Store...")

    return count

def seed_cyber_cafe_catalog(client):
    csv_path = os.path.join(SAMPLE_DOCS_DIR, "sample_cyber_cafe_rate_card.csv")
    if not os.path.exists(csv_path):
        # Fallback to predefined services
        services = [
            ("Private High-Speed Gaming & Work PC Cabin", "Category: Cyber Cafe Services\nPrice (INR): 40 per hour\nSpecial Offer: 3-hour gaming pass at Rs. 100\nProduct Details: Air-conditioned private cabin with 300 Mbps internet."),
            ("Govt Job Application & Admit Card Service", "Category: CSC Services\nPrice (INR): 80 per application\nProduct Details: Error-free online form submission for SSC, UPSC, Railway, Police exams with scanning."),
            ("Aadhaar, PAN & Voter ID Card Services", "Category: CSC Services\nPrice (INR): Starting from 50\nProduct Details: New PAN card, Voter ID application, and instant waterproof PVC Smart Card print.")
        ]
        for t, c in services:
            doc, _ = KnowledgeDocument.objects.update_or_create(client=client, page_title=t, defaults={"content_text": c, "content_type": "product_catalog", "is_active": True})
            VectorRAGEngine.add_or_update_document(client, doc)
        return len(services)

    count = 0
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("Service Name") or row.get("service_name") or row.get("title") or "Cyber Service"
            category = row.get("Category", "Cyber & CSC Services")
            rate = row.get("Rate (INR)", "") or row.get("price", "")
            tat = row.get("Turnaround Time", "") or row.get("turnaround", "")
            desc = row.get("Description", "") or row.get("details", "")

            content = f"Product Name: {title}\nCategory: {category}\nPrice (INR): {rate}\n"
            if tat:
                content += f"Turnaround: {tat}\n"
            if desc:
                content += f"Product Details: {desc}\n"

            doc, _ = KnowledgeDocument.objects.update_or_create(
                client=client,
                page_title=title,
                defaults={
                    "content_text": content.strip(),
                    "content_type": "product_catalog",
                    "is_active": True,
                }
            )
            VectorRAGEngine.add_or_update_document(client, doc)
            count += 1
    return count

def seed_luxe_catalog(client):
    products = [
        {
            "title": "Nordic Velvet Accent Armchair",
            "content": """Product Name: Nordic Velvet Accent Armchair
Category: Living Room Furniture
Price (INR): 18499
Special Offer: 15% instant discount + Free Home Delivery
Product Details: Premium high-density foam Scandinavian accent chair upholstered in stain-resistant royal velvet. Solid teak wood frame with brushed gold metal tips on legs.
Fabric: Velvet (Stain Resistant)
Available Colors: Royal Blue, Emerald Green, Mustard Yellow, Charcoal Grey
Image URL: https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=600&q=80"""
        },
        {
            "title": "Minimalist Artisan Oak Coffee Table",
            "content": """Product Name: Minimalist Artisan Oak Coffee Table
Category: Tables & Desks
Price (INR): 12999
Special Offer: Free assembly on delivery
Product Details: Handcrafted Japanese minimalist low coffee table made from certified solid European white oak. Matte water-resistant eco finish.
Material: Solid White Oak Wood
Image URL: https://images.unsplash.com/photo-1533090161767-e6ffed986c88?auto=format&fit=crop&w=600&q=80"""
        },
        {
            "title": "Abstract Geometric Wool Area Rug (6x9 ft)",
            "content": """Product Name: Abstract Geometric Wool Area Rug
Category: Rugs & Carpets
Price (INR): 8499
Product Details: Hand-tufted 100% New Zealand wool area rug with modern abstract terracotta and neutral arch pattern. Plush 15mm pile height.
Material: 100% New Zealand Wool
Size: 6 ft x 9 ft
Image URL: https://images.unsplash.com/photo-1600121848594-d8644e57abab?auto=format&fit=crop&w=600&q=80"""
        }
    ]
    for p in products:
        doc, _ = KnowledgeDocument.objects.update_or_create(
            client=client,
            page_title=p["title"],
            defaults={"content_text": p["content"], "content_type": "product_catalog", "is_active": True}
        )
        VectorRAGEngine.add_or_update_document(client, doc)
    return len(products)

def run_seed():
    print("🚀 Starting FULL Demo Clients + 300+ Products Seeding...\n")

    # 1. VASTRA FASHION (300+ Products)
    v_user, _ = User.objects.get_or_create(username="vastracollection", defaults={"email": "sales@vastrafashion.in"})
    v_user.set_password("client123")
    v_user.save()
    v_client, _ = BusinessClient.objects.update_or_create(
        user=v_user,
        defaults={
            "name": "Vastra Fashion Collection",
            "website_url": "https://vastracollection.shop",
            "owner_whatsapp": "919955804730",
            "bot_name": "Vastra Stylist",
            "brand_color": "#E11D48",
            "welcome_message": "Namaste! Welcome to Vastra Fashion ✨ Looking for Sarees, Kurtis, Lehengas or customized ethnic wear?",
            "is_active": True
        }
    )
    if not v_client.api_keys.exists():
        ClientAPIKey.objects.create(client=v_client, is_active=True, allowed_domains="*")
    print(f"👗 [1/3] Seeding Vastra Fashion Collection (300 Products CSV)...")
    v_count = seed_vastra_300_catalog(v_client)
    print(f"   ✅ Done! {v_count} clothing products indexed in ChromaDB.")

    # 2. DIGITAL POINT CYBER CAFE
    d_user, _ = User.objects.get_or_create(username="digitalpoint", defaults={"email": "contact@digitalpointcafe.in"})
    d_user.set_password("client123")
    d_user.save()
    d_client, _ = BusinessClient.objects.update_or_create(
        user=d_user,
        defaults={
            "name": "Digital Point Cyber Cafe & CSC",
            "website_url": "https://digitalpoint.in",
            "owner_whatsapp": "919955804730",
            "bot_name": "SpeedNet Assistant",
            "brand_color": "#0284C7",
            "welcome_message": "Namaste! Digital Point Cyber Cafe mein aapka swagat hai. CSC, Forms, Print, ya High-Speed PC Cabins ke baare me poochiye!",
            "is_active": True
        }
    )
    if not d_client.api_keys.exists():
        ClientAPIKey.objects.create(client=d_client, is_active=True, allowed_domains="*")
    print(f"\n💻 [2/3] Seeding Digital Point Cyber Cafe Rate Cards...")
    d_count = seed_cyber_cafe_catalog(d_client)
    print(f"   ✅ Done! {d_count} cyber services indexed in ChromaDB.")

    # 3. LUXE INTERIORS
    l_user, _ = User.objects.get_or_create(username="luxestore", defaults={"email": "contact@luxeinteriors.demo"})
    l_user.set_password("client123")
    l_user.save()
    l_client, _ = BusinessClient.objects.update_or_create(
        user=l_user,
        defaults={
            "name": "Luxe Interiors & Living",
            "website_url": "https://luxeinteriors.demo",
            "owner_whatsapp": "919955804730",
            "bot_name": "Luxe Decor Advisor",
            "brand_color": "#4F46E5",
            "welcome_message": "Namaste! Welcome to Luxe Interiors ✨ How can I help you transform your living spaces today?",
            "is_active": True
        }
    )
    if not l_client.api_keys.exists():
        ClientAPIKey.objects.create(client=l_client, is_active=True, allowed_domains="*")
    print(f"\n🛋️ [3/3] Seeding Luxe Interiors Furniture Catalog...")
    l_count = seed_luxe_catalog(l_client)
    print(f"   ✅ Done! {l_count} furniture products indexed in ChromaDB.")

    print("\n" + "=" * 60)
    print("🎉 ALL 3 DEMO CLIENTS + FULL 300+ DATASETS INDEXED!")
    print("=" * 60)
    print("1. Vastra Collection:    User: 'vastracollection' | Pass: 'client123' | 300+ Sarees, Kurtis & Lehengas")
    print("2. Digital Point Cafe:   User: 'digitalpoint'     | Pass: 'client123' | Cyber & Govt CSC Rates")
    print("3. Luxe Interiors:       User: 'luxestore'        | Pass: 'client123' | Home Decor & Furniture")
    print("\nLogin at: /login/ or check live storefronts!")

if __name__ == "__main__":
    run_seed()
