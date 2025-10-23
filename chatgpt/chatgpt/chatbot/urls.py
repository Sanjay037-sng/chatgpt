from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('chat/', views.chat, name='chat'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/history/', views.chat_history, name='chat_history'),
    path('api/conversations/', views.conversations_list, name='conversations_list'),
    path('api/conversations/<int:conversation_id>/', views.get_conversation, name='get_conversation'),
    path('api/conversations/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('api/clear/', views.clear_chat, name='clear_chat'),
    path('api/documents/upload/', views.upload_document, name='upload_document'),
    path('api/documents/', views.get_documents, name='get_documents'),
    path('api/documents/<int:document_id>/', views.get_document, name='get_document'),
    path('api/documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
]
