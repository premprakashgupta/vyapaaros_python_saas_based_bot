from django.urls import path
from .views import WidgetConfigView, WidgetChatView

urlpatterns = [
    path('config/', WidgetConfigView.as_view(), name='widget_config'),
    path('chat/', WidgetChatView.as_view(), name='widget_chat'),
]
