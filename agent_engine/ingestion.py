import re
import requests
from urllib.parse import urljoin, urlparse
import trafilatura
from bs4 import BeautifulSoup
from pypdf import PdfReader
import pandas as pd
from .models import BusinessClient, KnowledgeDocument

class IngestionEngine:
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Remove extra whitespaces, tabs, newlines
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @classmethod
    def scrape_webpage(cls, client: BusinessClient, url: str) -> KnowledgeDocument | None:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 VyapaarOSBot/1.0'
            }
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code != 200:
                return None

            html_content = resp.text
            # Extract clean main text using trafilatura
            extracted_text = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )

            # Get Page Title
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string.strip() if soup.title and soup.title.string else url

            if not extracted_text or len(extracted_text.split()) < 30:
                # Fallback to BeautifulSoup if trafilatura extracted too little
                for tag in soup(['script', 'style', 'nav', 'footer', 'noscript', 'svg']):
                    tag.decompose()
                extracted_text = soup.get_text(separator='\n')

            clean_content = cls.clean_text(extracted_text)
            if len(clean_content.split()) < 20:
                return None

            doc, _ = KnowledgeDocument.objects.update_or_create(
                client=client,
                source_url=url,
                defaults={
                    'page_title': title[:250],
                    'content_text': clean_content,
                    'content_type': 'website_page',
                    'is_active': True
                }
            )
            return doc
        except Exception as e:
            print(f"[Scraper Error] {url}: {e}")
            return None

    @classmethod
    def crawl_website(cls, client: BusinessClient, max_pages: int = 15) -> list[KnowledgeDocument]:
        if not client.website_url:
            return []
        
        base_url = client.website_url.strip()
        parsed_base = urlparse(base_url)
        domain = parsed_base.netloc

        visited = set()
        queue = [base_url]
        saved_docs = []

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) VyapaarOSBot/1.0'}

        while queue and len(visited) < max_pages:
            curr_url = queue.pop(0)
            if curr_url in visited:
                continue
            visited.add(curr_url)

            # Bug Fix #28: Fetch the page once and reuse for both scraping and link discovery.
            try:
                resp = requests.get(curr_url, headers=headers, timeout=12)
            except Exception:
                continue

            if resp.status_code != 200:
                continue

            # Scrape text content from the already-fetched response
            html_content = resp.text
            soup = BeautifulSoup(html_content, 'html.parser')
            page_title = soup.title.string.strip() if soup.title and soup.title.string else curr_url

            import trafilatura
            extracted_text = trafilatura.extract(html_content, include_comments=False, include_tables=True, no_fallback=False)
            if not extracted_text or len(extracted_text.split()) < 30:
                for tag in soup(['script', 'style', 'nav', 'footer', 'noscript', 'svg']):
                    tag.decompose()
                extracted_text = soup.get_text(separator='\n')

            clean_content = cls.clean_text(extracted_text)
            if len(clean_content.split()) >= 20:
                from .models import KnowledgeDocument
                doc, _ = KnowledgeDocument.objects.update_or_create(
                    client=client,
                    source_url=curr_url,
                    defaults={
                        'page_title': page_title[:250],
                        'content_text': clean_content,
                        'content_type': 'website_page',
                        'is_active': True
                    }
                )
                saved_docs.append(doc)

            # Discover internal links from the same response
            for a_tag in soup.find_all('a', href=True):
                link = urljoin(curr_url, a_tag['href'])
                parsed_link = urlparse(link)
                if parsed_link.netloc == domain and parsed_link.scheme in ['http', 'https']:
                    clean_link = link.split('#')[0].split('?')[0]
                    if clean_link not in visited and clean_link not in queue:
                        if not any(clean_link.lower().endswith(ext) for ext in ['.jpg', '.png', '.pdf', '.zip', '.mp4']):
                            queue.append(clean_link)

        return saved_docs

    @classmethod
    def ingest_pdf(cls, client: BusinessClient, file_obj, title: str = "Uploaded Brochure / Rate Card") -> KnowledgeDocument | None:
        try:
            reader = PdfReader(file_obj)
            extracted_pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_pages.append(f"--- Page {i+1} ---\n{text}")

            full_text = cls.clean_text("\n\n".join(extracted_pages))
            if not full_text:
                return None

            # If same PDF title exists for this client, update it (Overwrite); otherwise append new
            doc, _ = KnowledgeDocument.objects.update_or_create(
                client=client,
                page_title=title,
                defaults={
                    'content_text': full_text,
                    'content_type': 'product_catalog',
                    'is_active': True
                }
            )
            # Bug Fix #14: Vector indexing is handled by the caller (home_views.py)
            # to prevent double-indexing. Do NOT call VectorRAGEngine here.
            return doc
        except Exception as e:
            print(f"[PDF Ingest Error]: {e}")
            return None

    @classmethod
    def resolve_product_image(cls, row_dict: dict, client: BusinessClient) -> str | None:
        """Resolves explicit image URL or assigns high-quality relevant category image"""
        for k in ['image_url', 'image', 'photo', 'img', 'picture']:
            if k in row_dict and row_dict[k]:
                return str(row_dict[k]).strip()
                
        text_full = " ".join(str(v) for v in row_dict.values()).lower()
        
        # 1. Sarees
        if 'saree' in text_full or 'sari' in text_full or 'katan' in text_full or 'kanjivaram' in text_full:
            if 'pink' in text_full: return "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=600&q=80"
            if 'maroon' in text_full or 'red' in text_full: return "https://images.unsplash.com/photo-1610030469668-965529f79b6d?auto=format&fit=crop&w=600&q=80"
            if 'green' in text_full or 'teal' in text_full: return "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?auto=format&fit=crop&w=600&q=80"
            return "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=600&q=80"

        # 2. Lehengas & Chaniya Choli
        if 'lehenga' in text_full or 'chaniya' in text_full or 'ghagra' in text_full:
            if 'mirror' in text_full or 'navratri' in text_full: return "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=600&q=80"
            if 'pink' in text_full: return "https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=600&q=80"
            if 'teal' in text_full or 'green' in text_full: return "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80"
            return "https://images.unsplash.com/photo-1583391733975-dd7183e87854?auto=format&fit=crop&w=600&q=80"

        # 3. Kurtis & Suits
        if 'kurti' in text_full or 'anarkali' in text_full or 'suit' in text_full:
            if 'anarkali' in text_full or 'cotton' in text_full: return "https://images.unsplash.com/photo-1596783074918-c84cb06531ca?auto=format&fit=crop&w=600&q=80"
            if 'silk' in text_full or 'chanderi' in text_full: return "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=600&q=80"
            return "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=600&q=80"

        # 4. Mens Sherwani & Bandhgala
        if 'sherwani' in text_full or 'bandhgala' in text_full or 'coat' in text_full:
            if 'sherwani' in text_full: return "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?auto=format&fit=crop&w=600&q=80"
            return "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=600&q=80"

        # 5. Cyber Cafe & CSC Services
        if 'passport' in text_full or 'pan' in text_full or 'aadhaar' in text_full or 'form' in text_full:
            return "https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&w=600&q=80"
        if 'ticket' in text_full or 'railway' in text_full or 'flight' in text_full:
            return "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80"
        if 'print' in text_full or 'xerox' in text_full or 'lamination' in text_full:
            return "https://images.unsplash.com/photo-1512418490979-92798cec1380?auto=format&fit=crop&w=600&q=80"

        # 6. Luxury Interiors
        if 'kitchen' in text_full: return "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=600&q=80"
        if 'bedroom' in text_full or 'wardrobe' in text_full: return "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=600&q=80"
        if 'living' in text_full or 'marble' in text_full or 'interior' in text_full: return "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=600&q=80"

        return None

    @classmethod
    def ingest_csv_excel(cls, client: BusinessClient, file_obj, filename: str) -> list[KnowledgeDocument]:
        docs = []
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file_obj)
            else:
                df = pd.read_excel(file_obj)

            # Convert rows into meaningful structured text items
            for idx, row in df.iterrows():
                row_dict = row.dropna().to_dict()
                if not row_dict:
                    continue
                
                title = str(
                    row_dict.get('product_name') or 
                    row_dict.get('service_name') or 
                    row_dict.get('name') or 
                    row_dict.get('title') or 
                    row_dict.get('product') or 
                    f"Item #{idx+1}"
                )
                
                # Resolve image URL
                img_url = cls.resolve_product_image(row_dict, client)
                
                # Clean column headers
                text_lines = []
                for k, v in row_dict.items():
                    clean_k = k.replace('_', ' ').title()
                    if 'Inr' in clean_k:
                        clean_k = clean_k.replace('Inr', '(INR)')
                    text_lines.append(f"{clean_k}: {v}")
                    
                if img_url and not any('image' in l.lower() for l in text_lines):
                    text_lines.append(f"Image URL: {img_url}")

                content_text = "\n".join(text_lines)

                doc = KnowledgeDocument.objects.create(
                    client=client,
                    page_title=title[:250],
                    content_text=content_text,
                    content_type='product_catalog',
                    is_active=True
                )
                # Bug Fix #14: Vector indexing handled by caller to avoid double-indexing
                docs.append(doc)
        except Exception as e:
            print(f"[CSV/Excel Ingest Error]: {e}")
        return docs
