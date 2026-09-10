import uuid
import secrets
from django.db import models

from django.contrib.auth.models import User

class BusinessClient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="business_profile", help_text="Business owner login user")
    name = models.CharField(max_length=255, help_text="Business / Store Name")
    website_url = models.URLField(max_length=500, blank=True, null=True, help_text="Main Website URL")
    owner_whatsapp = models.CharField(max_length=20, help_text="Owner WhatsApp number (e.g. 919876543210)")
    brand_color = models.CharField(max_length=10, default="#0d9488", help_text="Theme Hex color")
    bot_name = models.CharField(max_length=100, default="AI Sales Assistant", help_text="Name displayed in widget")
    welcome_message = models.TextField(default="Hello! How can I help you today? Ask me about our services, pricing, or catalog.")
    system_prompt = models.TextField(blank=True, null=True, help_text="Custom instructions for AI behavior")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.bot_name})"

class ClientAPIKey(models.Model):
    client = models.ForeignKey(BusinessClient, on_delete=models.CASCADE, related_name="api_keys")
    key = models.CharField(max_length=64, unique=True, editable=False)
    allowed_domains = models.CharField(max_length=500, default="*", help_text="Allowed domains")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = f"vyapaar_live_{secrets.token_hex(16)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client.name} - {self.key[:16]}..."

class KnowledgeDocument(models.Model):
    CONTENT_TYPES = (
        ("website_page", "Website Page"),
        ("product_catalog", "Product / Service Item"),
        ("custom_faq", "Custom FAQ"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(BusinessClient, on_delete=models.CASCADE, related_name="knowledge_docs")
    source_url = models.URLField(max_length=500, blank=True, null=True)
    page_title = models.CharField(max_length=255, default="Untitled Page")
    content_text = models.TextField(help_text="Clean extracted textual knowledge for RAG context")
    content_type = models.CharField(max_length=30, choices=CONTENT_TYPES, default="website_page")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.client.name}] {self.page_title}"

class ChatLead(models.Model):
    LEAD_STATUS = (
        ("New", "New / Uncontacted"),
        ("Contacted", "Contacted"),
        ("Converted", "Converted / Client Won"),
        ("Spam", "Spam / Invalid"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(BusinessClient, on_delete=models.CASCADE, related_name="leads")
    session_id = models.CharField(max_length=100, help_text="Unique browser session ID")
    visitor_name = models.CharField(max_length=150, blank=True, null=True)
    visitor_phone = models.CharField(max_length=30, blank=True, null=True, help_text="Captured WhatsApp / Phone")
    visitor_email = models.EmailField(blank=True, null=True)
    transcript = models.JSONField(default=list, help_text="List of chat message history")
    lead_summary = models.TextField(blank=True, null=True, help_text="Auto-generated summary")
    status = models.CharField(max_length=20, choices=LEAD_STATUS, default="New")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Lead: {self.visitor_name or 'Anonymous'} - {self.client.name}"
