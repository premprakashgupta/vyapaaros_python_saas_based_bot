import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
import os
from django.conf import settings

from .models import BusinessClient, ClientAPIKey, KnowledgeDocument, ChatLead
from .forms import BusinessRegistrationForm, BusinessSettingsForm, ManualFAQForm
from .ingestion import IngestionEngine

class HomeDashboardView(TemplateView):
    template_name = 'home_dashboard.html'

def demo_storefront_view(request):
    # Bug Fix #20: Handle missing demo files gracefully
    demo_path = os.path.join(settings.BASE_DIR, 'test_client_website', 'index.html')
    try:
        with open(demo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse('<h2>Demo page not found.</h2>', status=404)

def cyber_cafe_storefront_view(request):
    cafe_path = os.path.join(settings.BASE_DIR, 'test_client_website', 'cyber_cafe.html')
    try:
        with open(cafe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse('<h2>Demo page not found.</h2>', status=404)

def clothing_storefront_view(request):
    cloth_path = os.path.join(settings.BASE_DIR, 'test_client_website', 'clothing_store.html')
    try:
        with open(cloth_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse('<h2>Demo page not found.</h2>', status=404)

def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def business_login_view(request):
    if request.user.is_authenticated:
        return redirect('business_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('business_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            
    return render(request, 'business_portal/login.html')

def business_register_view(request):
    if request.user.is_authenticated:
        return redirect('business_dashboard')

    if request.method == 'POST':
        form = BusinessRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Create User (uniqueness already validated in form.clean_username())
            user = User.objects.create_user(username=username, email=email, password=password)

            # Create Business Client
            business = form.save(commit=False)
            business.user = user
            business.save()

            # Create default API Key
            ClientAPIKey.objects.create(client=business)

            login(request, user)
            messages.success(request, f'Welcome to VyapaarOS, {business.name}!')
            return redirect('business_dashboard')
    else:
        form = BusinessRegistrationForm()

    return render(request, 'business_portal/register.html', {'form': form})

def business_logout_view(request):
    logout(request)
    return redirect('business_login')

def get_user_business(user, request=None):
    """Safely retrieves the business profile for any logged-in user.

    - Superusers/staff: can switch between any business via ?business_id=,
      or default to their own profile (created via get_or_create to prevent
      race conditions — Bug Fix #7).
    - Regular users: returns their linked BusinessClient, or None.
      Callers must handle the None case (Bug Fix #6: no more phantom records).
    """
    if user.is_superuser or user.is_staff:
        selected_id = None
        if request:
            selected_id = request.GET.get('business_id') or request.session.get('admin_active_business_id')
            if request.GET.get('business_id'):
                request.session['admin_active_business_id'] = str(request.GET.get('business_id'))

        if selected_id:
            biz = BusinessClient.objects.filter(id=selected_id).first()
            if biz:
                return biz

        # Bug Fix #7: Use get_or_create to prevent race condition on simultaneous requests
        admin_biz, created = BusinessClient.objects.get_or_create(
            user=user,
            defaults={
                'name': 'VyapaarOS HQ',
                'brand_color': '#F2541B',
                'bot_name': 'VyapaarOS Executive',
                'welcome_message': 'Hello! Welcome to VyapaarOS HQ. How can I assist your business today?',
                'owner_whatsapp': '919955804730',
            }
        )
        if created:
            ClientAPIKey.objects.create(client=admin_biz)
        return admin_biz

    # Bug Fix #6: Regular users — return profile only if it exists.
    # Do NOT auto-create phantom businesses. Callers handle None.
    try:
        if hasattr(user, 'business_profile') and user.business_profile:
            return user.business_profile
    except Exception:
        pass

    return BusinessClient.objects.filter(user=user).first()

def parse_product_attributes(doc: KnowledgeDocument) -> dict:
    """Helper to extract price, image, fabric, and category for structured dashboard tables"""
    attrs = {
        'id': str(doc.id),
        'title': doc.page_title,
        'category': 'General',
        'price': 'N/A',
        'fabric': '',
        'details': '',
        'image_url': '',
        'content_type': doc.content_type,
        'raw_content': doc.content_text,
        'created_at': doc.created_at,
        'updated_at': doc.updated_at
    }
    details_lines = []
    for line in doc.content_text.split('\n'):
        line_clean = line.strip()
        if not line_clean or ':' not in line_clean:
            if line_clean:
                details_lines.append(line_clean)
            continue
        k, v = line_clean.split(':', 1)
        k_lower = k.strip().lower()
        v_clean = v.strip()
        if k_lower in ('price (inr)', 'price', 'charges (inr)', 'charges', 'fee', 'rate'):
            attrs['price'] = v_clean
        elif k_lower in ('category', 'type', 'service type'):
            attrs['category'] = v_clean
        elif k_lower in ('fabric', 'material'):
            attrs['fabric'] = v_clean
        elif k_lower in ('image url', 'image', 'photo', 'thumbnail'):
            attrs['image_url'] = v_clean
        elif k_lower in ('product details', 'details', 'description', 'about', 'specs'):
            attrs['details'] = v_clean
        else:
            details_lines.append(f"{k}: {v_clean}")
            
    if not attrs['details'] and details_lines:
        attrs['details'] = "\n".join(details_lines)
        
    if not attrs['image_url']:
        attrs['image_url'] = 'https://images.unsplash.com/photo-1583391733975-dd7183e87854?auto=format&fit=crop&w=600&q=80'
    return attrs

@login_required(login_url='business_login')
def product_detail_view(request, doc_id):
    business = get_user_business(request.user, request=request)
    if not business:
        messages.warning(request, 'Please complete your business registration first.')
        return redirect('business_register')
    doc = get_object_or_404(KnowledgeDocument, id=doc_id, client=business)
    product = parse_product_attributes(doc)
    # Bug Fix #8: get_or_create should use defaults= not a filter kwarg
    api_key_obj, _ = ClientAPIKey.objects.get_or_create(client=business, defaults={'is_active': True})
    
    # Calculate word count & token estimate
    word_count = len(doc.content_text.split())
    est_tokens = max(1, int(word_count * 1.3))
    
    context = {
        'business': business,
        'doc': doc,
        'product': product,
        'word_count': word_count,
        'est_tokens': est_tokens,
        'api_key': api_key_obj.key if api_key_obj else '',
    }
    return render(request, 'business_portal/product_detail.html', context)

@login_required(login_url='business_login')
def business_dashboard_view(request):
    business = get_user_business(request.user, request=request)
    if not business:
        messages.warning(request, 'Please complete your business registration first.')
        return redirect('business_register')
    # Bug Fix #8: use defaults= so is_active is only for creation, not lookup
    api_key_obj, _ = ClientAPIKey.objects.get_or_create(client=business, defaults={'is_active': True})
    raw_docs = business.knowledge_docs.all().order_by('-updated_at')
    leads = business.leads.all().order_by('-created_at')
    
    # Process structured product items
    products_list = [parse_product_attributes(d) for d in raw_docs]
    
    settings_form = BusinessSettingsForm(instance=business)
    faq_form = ManualFAQForm()
    
    all_businesses = BusinessClient.objects.all().order_by('name') if (request.user.is_superuser or request.user.is_staff) else None

    context = {
        'business': business,
        'api_key': api_key_obj.key,
        'knowledge_docs': raw_docs,
        'products_list': products_list,
        'leads': leads,
        'settings_form': settings_form,
        'faq_form': faq_form,
        'all_businesses': all_businesses,
    }
    return render(request, 'business_portal/dashboard.html', context)

@login_required(login_url='business_login')
def lead_detail_api(request, lead_id):
    business = get_user_business(request.user, request=request)
    lead = get_object_or_404(ChatLead, id=lead_id, client=business)
    return JsonResponse({
        'success': True,
        'id': str(lead.id),
        'session_id': lead.session_id,
        'visitor_name': lead.visitor_name or 'Website Visitor',
        'visitor_phone': lead.visitor_phone or '',
        'visitor_email': lead.visitor_email or '',
        'status': lead.status,
        'created_at': lead.created_at.strftime('%d %b %Y, %I:%M %p'),
        'transcript': lead.transcript or [],
        'whatsapp_url': f"https://wa.me/{lead.visitor_phone}?text=Hi%20{lead.visitor_name or 'there'},%20thank%20you%20for%20reaching%20out%20to%20{business.name}!" if lead.visitor_phone else None
    })

@login_required(login_url='business_login')
def lead_delete_view(request, lead_id):
    # Bug Fix #11: Only allow DELETE via POST to prevent CSRF/accidental deletion
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    business = get_user_business(request.user, request=request)
    if not business:
        return JsonResponse({'error': 'No business profile found.'}, status=403)
    lead = get_object_or_404(ChatLead, id=lead_id, client=business)
    lead.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'success': True, 'message': 'Lead deleted successfully'})
    messages.success(request, 'Lead deleted successfully!')
    return redirect('business_dashboard')

@login_required(login_url='business_login')
def lead_bulk_delete_view(request):
    business = get_user_business(request.user, request=request)
    if not business:
        return JsonResponse({'error': 'No business profile found.'}, status=403)
    if request.method == 'POST':
        lead_ids = request.POST.getlist('lead_ids[]') or request.POST.getlist('lead_ids')
        if not lead_ids and request.body:
            try:
                data = json.loads(request.body)
                lead_ids = data.get('lead_ids', [])
            except Exception:
                pass
        if lead_ids:
            deleted_count, _ = ChatLead.objects.filter(id__in=lead_ids, client=business).delete()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': True, 'deleted_count': deleted_count, 'message': f'{deleted_count} lead(s) deleted successfully.'})
            messages.success(request, f'{deleted_count} lead(s) deleted successfully!')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': 'No leads selected.'}, status=400)
            messages.warning(request, 'No leads selected for deletion.')
    return redirect('business_dashboard')

@login_required(login_url='business_login')
def product_create_view(request):
    business = get_user_business(request.user, request=request)
    if request.method == 'POST':
        from .vector_service import VectorRAGEngine
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', '').strip() or 'General'
        price = request.POST.get('price', '').strip() or '0'
        fabric = request.POST.get('fabric', '').strip()
        details = request.POST.get('details', '').strip()
        image_url = request.POST.get('image_url', '').strip() or 'https://images.unsplash.com/photo-1583391733975-dd7183e87854?auto=format&fit=crop&w=600&q=80'
        
        if not title:
            messages.error(request, 'Product title is required.')
            return redirect('business_dashboard')

        content_lines = [
            f"Product Name: {title}",
            f"Category: {category}",
            f"Price (INR): {price}",
        ]
        if fabric:
            content_lines.append(f"Fabric: {fabric}")
        if details:
            content_lines.append(f"Product Details: {details}")
        if image_url:
            content_lines.append(f"Image URL: {image_url}")
            
        doc = KnowledgeDocument.objects.create(
            client=business,
            page_title=title,
            content_text="\n".join(content_lines),
            content_type="product_catalog",
            is_active=True
        )
        
        # Instant Live Vector Indexing
        VectorRAGEngine.add_or_update_document(business, doc)
        messages.success(request, f'Product "{title}" added & AI Vector knowledge synced successfully!')
    return redirect('business_dashboard')

@login_required(login_url='business_login')
def product_update_view(request, doc_id):
    business = get_user_business(request.user, request=request)
    doc = get_object_or_404(KnowledgeDocument, id=doc_id, client=business)
    
    if request.method == 'POST':
        from .vector_service import VectorRAGEngine
        title = request.POST.get('title', '').strip() or doc.page_title
        category = request.POST.get('category', '').strip()
        price = request.POST.get('price', '').strip()
        fabric = request.POST.get('fabric', '').strip()
        details = request.POST.get('details', '').strip()
        image_url = request.POST.get('image_url', '').strip()

        content_lines = [
            f"Product Name: {title}",
        ]
        if category:
            content_lines.append(f"Category: {category}")
        if price:
            content_lines.append(f"Price (INR): {price}")
        if fabric:
            content_lines.append(f"Fabric: {fabric}")
        if details:
            content_lines.append(f"Product Details: {details}")
        if image_url:
            content_lines.append(f"Image URL: {image_url}")

        doc.page_title = title
        doc.content_text = "\n".join(content_lines)
        doc.save()

        # Instant Live Vector Re-indexing
        VectorRAGEngine.add_or_update_document(business, doc)
        messages.success(request, f'Product "{title}" updated & AI Vector knowledge synced!')
    return redirect('business_dashboard')

@login_required(login_url='business_login')
def product_delete_view(request, doc_id):
    # Bug Fix #13: Only allow deletion via POST
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('business_dashboard')
    business = get_user_business(request.user, request=request)
    if not business:
        messages.warning(request, 'No business profile found.')
        return redirect('business_register')
    doc = get_object_or_404(KnowledgeDocument, id=doc_id, client=business)
    doc_title = doc.page_title

    from .vector_service import VectorRAGEngine
    # Delete from ChromaDB Vector Store
    VectorRAGEngine.delete_document(business, str(doc.id))
    # Delete from Database
    doc.delete()

    messages.success(request, f'Product "{doc_title}" deleted and removed from AI knowledge!')
    return redirect('business_dashboard')

@login_required(login_url='business_login')
def update_business_settings_view(request):
    business = get_user_business(request.user, request=request)
    if request.method == 'POST':
        form = BusinessSettingsForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bot & Business settings updated successfully!')
        else:
            messages.error(request, 'Error updating settings.')
    return redirect('business_dashboard')

@login_required(login_url='business_login')
def upload_knowledge_view(request):
    business = get_user_business(request.user, request=request)
    if request.method == 'POST':
        from .vector_service import VectorRAGEngine
        action_type = request.POST.get('action_type')
        catalog_file = request.FILES.get('catalog_file') or request.FILES.get('pdf_file') or request.FILES.get('excel_file')
        
        if catalog_file:
            fname = catalog_file.name.lower()
            if fname.endswith('.pdf'):
                doc = IngestionEngine.ingest_pdf(business, catalog_file, title=catalog_file.name)
                if doc:
                    VectorRAGEngine.add_or_update_document(business, doc)
                    messages.success(request, f'PDF "{catalog_file.name}" ingested and synced to Vector DB!')
                else:
                    messages.error(request, 'Could not extract text from PDF.')
            elif fname.endswith(('.xlsx', '.xls', '.csv')):
                docs = IngestionEngine.ingest_csv_excel(business, catalog_file, catalog_file.name)
                if docs:
                    for d in docs:
                        VectorRAGEngine.add_or_update_document(business, d)
                    messages.success(request, f'Imported {len(docs)} items from "{catalog_file.name}" and synced to Vector DB!')
                else:
                    messages.error(request, 'Could not parse Excel/CSV file.')
        elif action_type == 'crawl_web':
            url = request.POST.get('website_url', '').strip()
            if url:
                business.website_url = url
                business.save()
                docs = IngestionEngine.crawl_website(business, max_pages=10)
                if docs:
                    for d in docs:
                        VectorRAGEngine.add_or_update_document(business, d)
                    messages.success(request, f'Crawled and indexed {len(docs)} pages from {url}!')
                else:
                    messages.warning(request, 'Could not extract clean text from this URL.')
        elif action_type == 'add_faq':
            faq_form = ManualFAQForm(request.POST)
            if faq_form.is_valid():
                faq = faq_form.save(commit=False)
                faq.client = business
                faq.content_type = 'custom_faq'
                faq.save()
                VectorRAGEngine.add_or_update_document(business, faq)
                messages.success(request, f'Custom FAQ "{faq.page_title}" added & indexed!')
    return redirect('business_dashboard')

@login_required(login_url='business_login')
def delete_knowledge_view(request, doc_id):
    business = get_user_business(request.user, request=request)
    doc = get_object_or_404(KnowledgeDocument, id=doc_id, client=business)
    from .vector_service import VectorRAGEngine
    VectorRAGEngine.delete_document(business, str(doc.id))
    doc.delete()
    messages.success(request, f'Knowledge item deleted and removed from Vector DB.')
    return redirect('business_dashboard')

@login_required(login_url='business_login')
def clear_all_knowledge_view(request):
    # Bug Fix #12: Only allow via POST to prevent accidental data wipe via GET
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('business_dashboard')
    business = get_user_business(request.user, request=request)
    if not business:
        messages.warning(request, 'No business profile found.')
        return redirect('business_register')
    count = business.knowledge_docs.count()
    from .vector_service import VectorRAGEngine
    VectorRAGEngine.clear_client_collection(business)
    business.knowledge_docs.all().delete()
    messages.success(request, f'Cleared all {count} knowledge items and reset Vector DB collection.')
    return redirect('business_dashboard')
