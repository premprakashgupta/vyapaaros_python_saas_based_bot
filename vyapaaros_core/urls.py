"""
URL configuration for vyapaaros_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from agent_engine.home_views import (
    HomeDashboardView, 
    demo_storefront_view,
    cyber_cafe_storefront_view,
    clothing_storefront_view,
    business_login_view,
    business_register_view,
    business_logout_view,
    business_dashboard_view,
    lead_detail_api,
    lead_delete_view,
    lead_bulk_delete_view,
    product_create_view,
    product_detail_view,
    product_update_view,
    product_delete_view,
    update_business_settings_view,
    upload_knowledge_view,
    delete_knowledge_view,
    clear_all_knowledge_view,
    custom_404_view
)

urlpatterns = [
    path('', HomeDashboardView.as_view(), name='home_dashboard'),
    path('demo/', demo_storefront_view, name='demo_storefront'),
    path('cyber/', cyber_cafe_storefront_view, name='cyber_demo'),
    path('clothing/', clothing_storefront_view, name='clothing_demo'),
    path('clothes/', clothing_storefront_view, name='clothes_alias'),
    path('login/', business_login_view, name='business_login'),
    path('register/', business_register_view, name='business_register'),
    path('logout/', business_logout_view, name='business_logout'),
    path('dashboard/', business_dashboard_view, name='business_dashboard'),
    path('dashboard/lead/<uuid:lead_id>/', lead_detail_api, name='lead_detail_api'),
    path('dashboard/lead/delete/<uuid:lead_id>/', lead_delete_view, name='lead_delete'),
    path('dashboard/lead/bulk-delete/', lead_bulk_delete_view, name='lead_bulk_delete'),
    path('dashboard/product/create/', product_create_view, name='product_create'),
    path('dashboard/product/<uuid:doc_id>/', product_detail_view, name='product_detail'),
    path('dashboard/product/update/<uuid:doc_id>/', product_update_view, name='product_update'),
    path('dashboard/product/delete/<uuid:doc_id>/', product_delete_view, name='product_delete'),
    path('settings/update/', update_business_settings_view, name='update_business_settings'),
    path('knowledge/upload/', upload_knowledge_view, name='upload_knowledge'),
    path('knowledge/delete/<uuid:doc_id>/', delete_knowledge_view, name='delete_knowledge'),
    path('knowledge/clear-all/', clear_all_knowledge_view, name='clear_all_knowledge'),
    path('404/', custom_404_view, name='preview_404'),
    path('admin/', admin.site.urls),
    path('api/v1/widget/', include('agent_engine.urls')),
]

handler404 = 'agent_engine.home_views.custom_404_view'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS else settings.BASE_DIR / 'static')



