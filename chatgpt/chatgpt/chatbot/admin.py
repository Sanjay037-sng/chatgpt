from django.contrib import admin
from .models import ChatRecord, Conversation, Document


@admin.register(ChatRecord)
class ChatRecordAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session_id_short', 'timestamp', 'user_message_preview', 
        'bot_response_preview', 'has_summary'
    ]
    list_filter = ['timestamp', 'session_id']
    search_fields = ['user_message', 'bot_response', 'session_id', 'context_summary']
    readonly_fields = ['timestamp', 'id']
    list_per_page = 25
    
    fieldsets = (
        ('Session Information', {
            'fields': ('id', 'session_id', 'timestamp')
        }),
        ('Conversation', {
            'fields': ('user_message', 'bot_response'),
            'classes': ('wide',)
        }),
        ('Context & Summary', {
            'fields': ('context_summary',),
            'classes': ('collapse',)
        }),
    )
    
    def session_id_short(self, obj):
        return f"{obj.session_id[:12]}..." if len(obj.session_id) > 12 else obj.session_id
    session_id_short.short_description = 'Session ID'
    session_id_short.admin_order_field = 'session_id'
    
    def user_message_preview(self, obj):
        return obj.user_message[:60] + '...' if len(obj.user_message) > 60 else obj.user_message
    user_message_preview.short_description = 'User Message'
    
    def bot_response_preview(self, obj):
        return obj.bot_response[:60] + '...' if len(obj.bot_response) > 60 else obj.bot_response
    bot_response_preview.short_description = 'Bot Response'
    
    def has_summary(self, obj):
        return bool(obj.context_summary)
    has_summary.boolean = True
    has_summary.short_description = 'Has Summary'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'user', 'created_at', 'updated_at', 'message_count'
    ]
    list_filter = ['created_at', 'updated_at', 'user']
    search_fields = ['title', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'id']
    list_per_page = 25
    
    fieldsets = (
        ('Conversation Information', {
            'fields': ('id', 'user', 'title', 'created_at', 'updated_at')
        }),
        ('Messages', {
            'fields': ('full_conversation',),
            'classes': ('wide',)
        }),
    )
    
    def message_count(self, obj):
        return obj.get_message_count()
    message_count.short_description = 'Message Count'
    message_count.admin_order_field = 'full_conversation'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'user', 'file_type', 'file_size_mb', 'upload_date', 'last_accessed'
    ]
    list_filter = ['file_type', 'upload_date', 'last_accessed', 'user']
    search_fields = ['title', 'user__username', 'extracted_text']
    readonly_fields = ['upload_date', 'last_accessed', 'id', 'file_size']
    list_per_page = 25
    
    fieldsets = (
        ('Document Information', {
            'fields': ('id', 'user', 'title', 'file', 'file_type', 'file_size', 'upload_date', 'last_accessed')
        }),
        ('Content', {
            'fields': ('extracted_text',),
            'classes': ('wide',)
        }),
    )
    
    def file_size_mb(self, obj):
        return f"{obj.get_file_size_mb()} MB"
    file_size_mb.short_description = 'File Size'
    file_size_mb.admin_order_field = 'file_size'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
