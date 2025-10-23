from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
import uuid
import json
import os


class Conversation(models.Model):
    """Model to store complete chat conversations"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200, help_text="Title of the conversation")
    full_conversation = models.JSONField(help_text="Complete conversation history as JSON")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
    
    def __str__(self):
        return f"{self.title} - {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def add_message(self, user_message, bot_response, context_summary=None):
        """Add a new message exchange to the conversation"""
        from django.utils import timezone
        
        conversation_data = self.full_conversation or []
        
        message_exchange = {
            'user_message': user_message,
            'bot_response': bot_response,
            'context_summary': context_summary,
            'timestamp': timezone.now().isoformat()
        }
        
        conversation_data.append(message_exchange)
        self.full_conversation = conversation_data
        self.save()
    
    def get_messages(self):
        """Get all messages in the conversation"""
        return self.full_conversation or []
    
    def get_message_count(self):
        """Get the number of message exchanges in the conversation"""
        return len(self.full_conversation or [])
    
    @classmethod
    def create_new_conversation(cls, user, title, first_user_message, first_bot_response, context_summary=None):
        """Create a new conversation with the first message exchange"""
        from django.utils import timezone
        
        conversation_data = [{
            'user_message': first_user_message,
            'bot_response': first_bot_response,
            'context_summary': context_summary,
            'timestamp': timezone.now().isoformat()
        }]
        
        return cls.objects.create(
            user=user,
            title=title,
            full_conversation=conversation_data
        )


class ChatRecord(models.Model):
    """Model to store structured chat conversations with labeled sections"""
    id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=100, help_text="Unique identifier for conversation session")
    user_message = models.TextField(help_text="User's input message")
    bot_response = models.TextField(help_text="AI model's response")
    context_summary = models.TextField(
        blank=True, 
        null=True, 
        help_text="Optional summary of conversation context"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = "Chat Record"
        verbose_name_plural = "Chat Records"
    
    def __str__(self):
        return f"Chat {self.id} - Session {self.session_id[:8]}... - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def get_session_messages(cls, session_id, limit=15):
        """Get the latest messages for a session, limited to specified count"""
        return cls.objects.filter(session_id=session_id).order_by('-timestamp')[:limit]
    
    @classmethod
    def clear_session(cls, session_id):
        """Clear all messages for a specific session"""
        return cls.objects.filter(session_id=session_id).delete()
    
    @classmethod
    def get_session_summary(cls, session_id):
        """Get a summary of the conversation for a session"""
        messages = cls.objects.filter(session_id=session_id).order_by('timestamp')
        if not messages.exists():
            return None
        
        # Create a simple summary of the conversation
        total_messages = messages.count()
        first_message = messages.first()
        last_message = messages.last()
        
        summary = f"Conversation with {total_messages} exchanges from {first_message.timestamp.strftime('%H:%M')} to {last_message.timestamp.strftime('%H:%M')}"
        return summary


class Document(models.Model):
    """Model to store uploaded documents and their extracted content"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255, help_text="Document title")
    file = models.FileField(upload_to='documents/', help_text="Uploaded file")
    file_type = models.CharField(max_length=50, help_text="File type (pdf, docx, txt, etc.)")
    extracted_text = models.TextField(help_text="Extracted text content from the document")
    file_size = models.IntegerField(help_text="File size in bytes")
    upload_date = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = "Document"
        verbose_name_plural = "Documents"
    
    def __str__(self):
        return f"{self.title} - {self.user.username} - {self.upload_date.strftime('%Y-%m-%d %H:%M')}"
    
    def get_file_extension(self):
        """Get file extension from filename"""
        return os.path.splitext(self.file.name)[1].lower()
    
    def get_file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    def is_pdf(self):
        """Check if file is PDF"""
        return self.get_file_extension() == '.pdf'
    
    def is_docx(self):
        """Check if file is DOCX"""
        return self.get_file_extension() in ['.docx', '.doc']
    
    def is_excel(self):
        """Check if file is Excel"""
        return self.get_file_extension() in ['.xlsx', '.xls']
    
    def is_text(self):
        """Check if file is text"""
        return self.get_file_extension() in ['.txt', '.md']
    
    def is_image(self):
        """Check if file is image"""
        return self.get_file_extension() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    
    def delete(self, *args, **kwargs):
        """Override delete to also remove the file from storage"""
        if self.file:
            if default_storage.exists(self.file.name):
                default_storage.delete(self.file.name)
        super().delete(*args, **kwargs)
