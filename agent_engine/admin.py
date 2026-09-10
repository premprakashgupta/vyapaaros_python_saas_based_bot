import re
from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.contrib import messages
from .models import BusinessClient, ClientAPIKey, KnowledgeDocument, ChatLead


class BusinessClientAdminForm(forms.ModelForm):
    custom_username = forms.CharField(
        label="Client Login Username",
        required=False,
        help_text="Login username for client dashboard. If left blank, it will be auto-generated from store name."
    )
    custom_password = forms.CharField(
        label="Set Client Password",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. client123 (Leave blank to keep existing password)"}),
        help_text="Enter a new password for this business client. Default is 'client123' if creating a new user."
    )

    class Meta:
        model = BusinessClient
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['custom_username'].initial = self.instance.user.username


class ClientAPIKeyInline(admin.TabularInline):
    model = ClientAPIKey
    extra = 1
    fields = ("key_with_copy", "allowed_domains", "is_active", "created_at")
    readonly_fields = ("key_with_copy", "created_at")

    def key_with_copy(self, obj):
        if not obj or not obj.key:
            return "Will be generated on save"
        return mark_safe(f'''
            <div style="display: flex; align-items: center; gap: 8px;">
                <code style="background: #f1f5f9; color: #0f172a; padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 13px;">{obj.key}</code>
                <button type="button" onclick="navigator.clipboard.writeText('{obj.key}'); this.innerText='Copied!'; setTimeout(() => this.innerText='Copy', 2000);" 
                        style="background: #f2541b; color: #fff; border: none; padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600;">
                    Copy
                </button>
            </div>
        ''')
    key_with_copy.short_description = "API Key"


class KnowledgeDocumentInline(admin.TabularInline):
    model = KnowledgeDocument
    extra = 0
    fields = ("page_title", "content_type", "source_url", "is_active")
    readonly_fields = ("created_at",)


@admin.register(BusinessClient)
class BusinessClientAdmin(admin.ModelAdmin):
    form = BusinessClientAdminForm
    list_display = ("name", "user_link", "bot_name", "owner_whatsapp", "api_key_display", "is_active", "created_at")
    search_fields = ("name", "bot_name", "owner_whatsapp", "website_url", "user__username")
    list_filter = ("is_active", "created_at")
    inlines = [ClientAPIKeyInline, KnowledgeDocumentInline]
    readonly_fields = ("credentials_box", "embed_code_box", "created_at", "updated_at")

    fieldsets = (
        ("🏢 Business Profile", {
            "fields": ("name", "website_url", "owner_whatsapp", "is_active")
        }),
        ("🔑 Client Login Credentials (Dashboard Access)", {
            "description": "Credentials used by the business client to log in at <code>/login/</code> and manage their AI bot & leads.",
            "fields": ("credentials_box", "custom_username", "custom_password", "user")
        }),
        ("🤖 AI Assistant Configuration", {
            "fields": ("bot_name", "brand_color", "welcome_message", "system_prompt")
        }),
        ("🚀 1-Line Embed Code & API Key", {
            "fields": ("embed_code_box",)
        }),
        ("🕒 Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )

    def user_link(self, obj):
        if obj.user:
            return mark_safe(f'<strong>{obj.user.username}</strong>')
        return mark_safe('<span style="color: #ef4444;">No User Linked</span>')
    user_link.short_description = "Client Login User"

    def api_key_display(self, obj):
        key_obj = obj.api_keys.first()
        if key_obj:
            return mark_safe(f'''
                <div style="display: flex; align-items: center; gap: 6px;">
                    <code style="font-size: 11.5px; background: #e2e8f0; padding: 2px 6px; border-radius: 4px;">{key_obj.key[:16]}...</code>
                    <button type="button" onclick="navigator.clipboard.writeText('{key_obj.key}'); this.innerText='✓'; setTimeout(() => this.innerText='📋', 1500);" 
                            style="border: 1px solid #cbd5e1; background: #fff; border-radius: 4px; padding: 2px 6px; cursor: pointer; font-size: 11px;" title="Copy API Key">
                        📋
                    </button>
                </div>
            ''')
        return "-"
    api_key_display.short_description = "API Key"

    def credentials_box(self, obj):
        if not obj or not obj.pk:
            return "Credentials will be displayed after saving the client."
        
        username = obj.user.username if obj.user else "Not created yet"
        return mark_safe(f'''
            <div style="background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 14px 18px; max-width: 600px;">
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 12px; text-transform: uppercase; color: #64748b; font-weight: 700;">Client Login Username:</span>
                    <strong style="font-size: 15px; color: #0f172a; margin-left: 8px;">{username}</strong>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 12px; text-transform: uppercase; color: #64748b; font-weight: 700;">Client Login Portal:</span>
                    <a href="/login/" target="_blank" style="margin-left: 8px; color: #2563eb; font-weight: 700; text-decoration: underline;">
                        http://127.0.0.1:8000/login/ ↗
                    </a>
                </div>
                <div style="font-size: 12px; color: #475569; background: #e0f2fe; padding: 8px 12px; border-radius: 6px; border: 1px solid #bae6fd;">
                    💡 <strong>Password:</strong> Enter a new password below anytime to set or reset this client's password.
                </div>
            </div>
        ''')
    credentials_box.short_description = "Active Credentials"

    def embed_code_box(self, obj):
        if not obj or not obj.pk:
            return "API Key and Embed Code will be generated after saving."

        key_obj = obj.api_keys.first()
        if not key_obj:
            # Bug Fix #24: Never create records inside a readonly display method.
            # The key will be created in save_model(). Show a prompt instead.
            return mark_safe(
                '<span style="color:#ef4444; font-weight:600;">'
                '⚠️ No API Key found. Click <strong>Save</strong> to auto-generate one.</span>'
            )
            
        key_str = key_obj.key
        script_snippet = f'&lt;script src="http://127.0.0.1:8000/static/widget.js" data-api-key="{key_str}" async&gt;&lt;/script&gt;'
        raw_script = f'<script src="http://127.0.0.1:8000/static/widget.js" data-api-key="{key_str}" async></script>'

        return mark_safe(f'''
            <div style="background: #0f172a; color: #f8fafc; border-radius: 10px; padding: 18px; max-width: 700px; font-family: monospace;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
                    <div>
                        <span style="color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">API Key:</span>
                        <span style="color: #38bdf8; font-weight: 700; font-size: 13.5px; margin-left: 6px;">{key_str}</span>
                    </div>
                    <button type="button" onclick="navigator.clipboard.writeText('{key_str}'); this.innerText='Copied Key!'; setTimeout(() => this.innerText='Copy Key', 2000);"
                            style="background: #f2541b; color: #fff; border: none; padding: 5px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 700;">
                        Copy Key
                    </button>
                </div>

                <div style="margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                        <span style="color: #94a3b8; font-size: 11px; text-transform: uppercase;">1-Line HTML Embed Script:</span>
                        <button type="button" onclick="navigator.clipboard.writeText(`{raw_script}`); this.innerText='Copied Script!'; setTimeout(() => this.innerText='Copy Embed Script', 2000);"
                                style="background: #22c55e; color: #fff; border: none; padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 11.5px; font-weight: 700;">
                            Copy Embed Script
                        </button>
                    </div>
                    <pre style="background: #1e293b; padding: 10px; border-radius: 6px; color: #a5f3fc; font-size: 12px; overflow-x: auto; margin: 0;">{script_snippet}</pre>
                </div>
            </div>
        ''')
    embed_code_box.short_description = "Live Widget Embed"

    def save_model(self, request, obj, form, change):
        custom_username = form.cleaned_data.get('custom_username')
        custom_password = form.cleaned_data.get('custom_password')
        pwd_set_msg = None

        if not obj.user:
            # Generate or use custom username
            if custom_username:
                username = custom_username.strip()
            else:
                base_username = re.sub(r'[^a-zA-Z0-9]', '', obj.name.lower())[:20] or f"client_{obj.id.hex[:6]}"
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
            
            pwd = custom_password.strip() if custom_password else "client123"
            new_user = User.objects.create_user(
                username=username,
                email=f"{username}@vyapaaros.local",
                password=pwd
            )
            obj.user = new_user
            pwd_set_msg = pwd
        else:
            # Existing user
            user_obj = obj.user
            if custom_username and custom_username.strip() != user_obj.username:
                user_obj.username = custom_username.strip()
                user_obj.save()
            if custom_password and custom_password.strip():
                user_obj.set_password(custom_password.strip())
                user_obj.save()
                pwd_set_msg = custom_password.strip()

        super().save_model(request, obj, form, change)

        # Ensure active API key
        if not obj.api_keys.exists():
            ClientAPIKey.objects.create(client=obj)

        if not change:
            messages.success(
                request,
                f"✅ New Client Created! Login Credentials -> Username: '{obj.user.username}' | Password: '{pwd_set_msg or 'client123'}' | Login URL: /login/"
            )
        elif pwd_set_msg:
            messages.success(
                request,
                f"✅ Password updated for '{obj.user.username}'! New Password: '{pwd_set_msg}'"
            )


@admin.register(ClientAPIKey)
class ClientAPIKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "client", "allowed_domains", "is_active", "created_at")
    search_fields = ("key", "client__name", "allowed_domains")
    list_filter = ("is_active", "created_at")
    readonly_fields = ("key_display_box", "created_at")
    fields = ("key_display_box", "client", "allowed_domains", "is_active", "created_at")

    def key_display_box(self, obj):
        if not obj or not obj.key:
            return "-"
        return mark_safe(f'''
            <div style="display: flex; align-items: center; gap: 8px;">
                <code style="font-size: 14px; font-weight: 700; background: #0f172a; color: #38bdf8; padding: 6px 12px; border-radius: 6px;">{obj.key}</code>
                <button type="button" onclick="navigator.clipboard.writeText('{obj.key}'); this.innerText='Copied!'; setTimeout(() => this.innerText='Copy Key', 2000);"
                        style="background: #f2541b; color: #fff; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 700; font-size: 12px;">
                    Copy Key
                </button>
            </div>
        ''')
    key_display_box.short_description = "API Key"


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("page_title", "client", "content_type", "source_url", "is_active", "updated_at")
    search_fields = ("page_title", "content_text", "client__name", "source_url")
    list_filter = ("content_type", "is_active", "client")
    list_per_page = 25


@admin.register(ChatLead)
class ChatLeadAdmin(admin.ModelAdmin):
    list_display = ("visitor_name", "visitor_phone", "client", "status", "created_at")
    search_fields = ("visitor_name", "visitor_phone", "visitor_email", "client__name", "lead_summary")
    list_filter = ("status", "client", "created_at")
    readonly_fields = ("created_at", "updated_at", "transcript")
