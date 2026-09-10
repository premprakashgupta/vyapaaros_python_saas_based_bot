import uuid
from urllib.parse import urlparse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import ClientAPIKey, BusinessClient
from .ai_service import process_chat_message

def is_domain_allowed(api_key_obj: ClientAPIKey, request) -> bool:
    """
    Validates request Origin/Referer header against client's Whitelisted Allowed Domains.
    Prevents unauthorized third-parties from stealing the public API key.
    """
    allowed_raw = (api_key_obj.allowed_domains or '*').strip()
    if allowed_raw == '*':
        return True

    origin = request.headers.get('Origin') or request.headers.get('Referer') or ''
    if not origin:
        return True

    parsed = urlparse(origin)
    req_host = (parsed.netloc or parsed.path).split(':')[0].lower()
    allowed_list = [d.strip().lower() for d in allowed_raw.split(',') if d.strip()]

    for allowed in allowed_list:
        clean_allowed = allowed.split(':')[0]
        if clean_allowed == '*' or clean_allowed == req_host:
            return True
        if clean_allowed.startswith('*.') and req_host.endswith(clean_allowed[2:]):
            return True
        # Local development matching
        if req_host in ('127.0.0.1', 'localhost') and any(loc in clean_allowed for loc in ('127.0.0.1', 'localhost')):
            return True

    return False

class WidgetConfigView(APIView):
    """
    Returns initial widget styling, greeting, and suggestions for a verified API key.
    Enforces Domain Whitelisting and Client Status verification.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        api_key_str = request.GET.get('key') or request.headers.get('X-Api-Key')
        if not api_key_str:
            return Response({"error": "Missing 'key' query parameter or 'X-Api-Key' header."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            api_key_obj = ClientAPIKey.objects.select_related('client').get(key=api_key_str, is_active=True)
        except ClientAPIKey.DoesNotExist:
            return Response({"error": "Invalid or inactive API Key."}, status=status.HTTP_403_FORBIDDEN)
            
        client = api_key_obj.client
        if not client.is_active:
            return Response({"error": "Client account is inactive."}, status=status.HTTP_403_FORBIDDEN)
            
        # Security: Domain Whitelisting Verification
        if not is_domain_allowed(api_key_obj, request):
            return Response({"error": f"Unauthorized Origin: This API Key is locked to {api_key_obj.allowed_domains}"}, status=status.HTTP_403_FORBIDDEN)
            
        # Extract default quick suggestions
        suggestions = [
            "What services do you offer?",
            "What are your prices & packages?",
            "How can I contact your team?"
        ]
        
        # Check if client has custom docs for quick prompts
        docs = client.knowledge_docs.filter(is_active=True)[:3]
        if docs.exists():
            suggestions = [f"Tell me about {d.page_title}" for d in docs]

        data = {
            "client_name": client.name,
            "bot_name": client.bot_name,
            "brand_color": client.brand_color or "#F2541B",
            "welcome_message": client.welcome_message,
            "owner_whatsapp": client.owner_whatsapp,
            "suggestions": suggestions,
            "session_id": str(uuid.uuid4())
        }
        return Response(data, status=status.HTTP_200_OK)


class WidgetChatView(APIView):
    """
    Handles user chat interactions, RAG knowledge retrieval, LLM response, and lead capture.
    Enforces Domain Whitelisting, active client status, and payload validation.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = request.data
        api_key_str = data.get('api_key') or request.headers.get('X-Api-Key')
        session_id = data.get('session_id')
        message = data.get('message', '').strip()
        history = data.get('history', [])
        
        if not api_key_str:
            return Response({"error": "API Key is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            api_key_obj = ClientAPIKey.objects.select_related('client').get(key=api_key_str, is_active=True)
        except ClientAPIKey.DoesNotExist:
            return Response({"error": "Invalid or inactive API Key."}, status=status.HTTP_403_FORBIDDEN)

        # Security: Domain Whitelisting Verification
        if not is_domain_allowed(api_key_obj, request):
            return Response({"error": f"Unauthorized Origin: This API Key is locked to {api_key_obj.allowed_domains}"}, status=status.HTTP_403_FORBIDDEN)

        if not session_id:
            return Response({"error": "session_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not message:
            return Response({"error": "Message cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
            
        result = process_chat_message(
            client=api_key_obj.client,
            session_id=session_id,
            message=message,
            history=history
        )

        if not result.get("success"):
            # Bug Fix #9: Server-side errors should be 500, not 400
            return Response({"error": result.get("error")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(result, status=status.HTTP_200_OK)
