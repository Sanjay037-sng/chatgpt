import json
import uuid
import google.generativeai as genai
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.db import models
from django.core.files.storage import default_storage
from .models import ChatRecord, Conversation, Document
from .document_processor import DocumentProcessor


def home(request):
    """Redirect to login page by default"""
    return redirect('login')


@login_required
def chat(request):
    """Render the main chat page - only for authenticated users"""
    return render(request, 'chat.html')


def login_view(request):
    """Handle user login"""
    # If user is already logged in, redirect to chat
    if request.user.is_authenticated:
        return redirect('chat')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('chat')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'login.html')


def signup_view(request):
    """Handle user registration"""
    # If user is already logged in, redirect to chat
    if request.user.is_authenticated:
        return redirect('chat')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            messages.error(request, 'Please fill in all fields.')
        elif len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                messages.success(request, 'Account created successfully! Please log in.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'signup.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """Handle chat API requests with contextual conversation"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', None)
        
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        
        # Configure Gemini API
        if not settings.GEMINI_API_KEY:
            return JsonResponse({'error': 'Gemini API key not configured'}, status=500)
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            except Conversation.DoesNotExist:
                return JsonResponse({'error': 'Conversation not found'}, status=404)
        else:
            # Create new conversation
            title = user_message[:50] + ('...' if len(user_message) > 50 else '')
            conversation = Conversation.create_new_conversation(
                user=request.user,
                title=title,
                first_user_message=user_message,
                first_bot_response="",  # Will be filled after AI response
                context_summary=None
            )
        
        # Get conversation context for AI
        context_text = ""
        messages = conversation.get_messages()
        if len(messages) > 1:  # More than just the current message
            context_text = "Previous conversation context:\n"
            for msg in messages[:-1]:  # Exclude the current message
                context_text += f"User: {msg['user_message']}\n"
                context_text += f"Assistant: {msg['bot_response']}\n\n"
        
        # Check if user wants to analyze uploaded documents
        document_context = ""
        if any(keyword in user_message.lower() for keyword in ['document', 'file', 'pdf', 'docx', 'summarize', 'analyze', 'extract']):
            # Get user's recent documents
            recent_docs = Document.objects.filter(user=request.user).order_by('-last_accessed')[:3]
            if recent_docs:
                document_context = "\n\nAvailable Documents:\n"
                for doc in recent_docs:
                    document_context += f"- {doc.title} ({doc.file_type}, {doc.get_file_size_mb()}MB)\n"
                    document_context += f"Content preview: {doc.extracted_text[:1000]}...\n\n"
        
        # Create the full prompt with context
        full_prompt = f"{context_text}{document_context}Current user message: {user_message}"
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Generate response with context
        response = model.generate_content(full_prompt)
        bot_response = response.text if response.text else "I'm sorry, I couldn't generate a response."
        
        # Generate context summary for long conversations
        context_summary = None
        if len(messages) > 5:  # Generate summary for conversations with more than 5 exchanges
            summary_prompt = f"Please provide a brief summary of this conversation context: {context_text}"
            try:
                summary_response = model.generate_content(summary_prompt)
                context_summary = summary_response.text if summary_response.text else None
            except:
                context_summary = None
        
        # Update conversation with the new message exchange
        if conversation_id:
            # Add to existing conversation
            conversation.add_message(user_message, bot_response, context_summary)
        else:
            # Update the new conversation with the bot response
            conversation_data = conversation.full_conversation
            conversation_data[0]['bot_response'] = bot_response
            conversation_data[0]['context_summary'] = context_summary
            conversation.full_conversation = conversation_data
            conversation.save()
        
        return JsonResponse({
            'response': bot_response,
            'conversation_id': conversation.id,
            'status': 'success'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def chat_history(request):
    """Get chat history for a specific session"""
    try:
        session_id = request.GET.get('session_id', '')
        
        if not session_id:
            return JsonResponse({'messages': [], 'session_id': ''})
        
        messages = ChatRecord.objects.filter(session_id=session_id).order_by('timestamp')
        
        chat_data = []
        for msg in messages:
            chat_data.append({
                'id': msg.id,
                'user_message': msg.user_message,
                'bot_response': msg.bot_response,
                'context_summary': msg.context_summary,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return JsonResponse({
            'messages': chat_data,
            'session_id': session_id,
            'total_messages': len(chat_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def conversations_list(request):
    """Get list of all conversations for the user"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        
        # Get all conversations for the current user
        conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
        
        print(f"Found {len(conversations)} conversations for user {request.user.username}")
        
        conversation_list = []
        for conv in conversations:
            conversation_list.append({
                'id': conv.id,
                'title': conv.title,
                'last_updated': conv.updated_at.isoformat(),
                'message_count': conv.get_message_count(),
                'created_at': conv.created_at.isoformat()
            })
            print(f"Added conversation: {conv.title}")
        
        print(f"Returning {len(conversation_list)} conversations")
        
        return JsonResponse({
            'conversations': conversation_list,
            'total': len(conversation_list)
        })
        
    except Exception as e:
        print(f"Error in conversations_list: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_conversation(request, conversation_id):
    """Get a specific conversation by ID"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        return JsonResponse({
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'messages': conversation.get_messages(),
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat(),
                'message_count': conversation.get_message_count()
            },
            'status': 'success'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_conversation(request, conversation_id):
    """Delete a specific conversation"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            conversation.delete()
            
            return JsonResponse({
                'message': f'Deleted conversation "{conversation.title}"',
                'status': 'success'
            })
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def clear_chat(request):
    """Clear all chat records for a specific session"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', '')
        
        if not session_id:
            return JsonResponse({'error': 'Session ID is required'}, status=400)
        
        # Clear all messages for the session
        deleted_count = ChatRecord.clear_session(session_id)
        
        return JsonResponse({
            'message': f'Cleared {deleted_count[0]} chat records for session {session_id}',
            'deleted_count': deleted_count[0],
            'status': 'success'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def upload_document(request):
    """Handle document upload and text extraction"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Check file size (limit to 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'File size too large. Maximum 10MB allowed.'}, status=400)
        
        # Check if file type is supported
        if not DocumentProcessor.is_file_type_supported(uploaded_file.name):
            return JsonResponse({
                'error': f'Unsupported file type. Supported types: {", ".join(DocumentProcessor.get_supported_file_types())}'
            }, status=400)
        
        # Extract text from document
        extracted_text, file_type = DocumentProcessor.extract_text_from_file(uploaded_file)
        
        if file_type == 'error':
            return JsonResponse({'error': f'Error processing file: {extracted_text}'}, status=400)
        
        # Create document record
        document = Document.objects.create(
            user=request.user,
            title=uploaded_file.name,
            file=uploaded_file,
            file_type=file_type,
            extracted_text=extracted_text,
            file_size=uploaded_file.size
        )
        
        return JsonResponse({
            'document_id': document.id,
            'title': document.title,
            'file_type': file_type,
            'file_size_mb': document.get_file_size_mb(),
            'extracted_text_preview': extracted_text[:500] + ('...' if len(extracted_text) > 500 else ''),
            'status': 'success'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_documents(request):
    """Get list of user's uploaded documents"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        
        documents = Document.objects.filter(user=request.user).order_by('-upload_date')
        
        document_list = []
        for doc in documents:
            document_list.append({
                'id': doc.id,
                'title': doc.title,
                'file_type': doc.file_type,
                'file_size_mb': doc.get_file_size_mb(),
                'upload_date': doc.upload_date.isoformat(),
                'last_accessed': doc.last_accessed.isoformat(),
                'extracted_text_preview': doc.extracted_text[:200] + ('...' if len(doc.extracted_text) > 200 else '')
            })
        
        return JsonResponse({
            'documents': document_list,
            'total': len(document_list)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_document(request, document_id):
    """Get specific document content"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)
        
        # Update last accessed time
        document.save()
        
        return JsonResponse({
            'document': {
                'id': document.id,
                'title': document.title,
                'file_type': document.file_type,
                'file_size_mb': document.get_file_size_mb(),
                'extracted_text': document.extracted_text,
                'upload_date': document.upload_date.isoformat(),
                'last_accessed': document.last_accessed.isoformat()
            },
            'status': 'success'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_document(request, document_id):
    """Delete a specific document"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        
        try:
            document = Document.objects.get(id=document_id, user=request.user)
            document.delete()
            
            return JsonResponse({
                'message': f'Deleted document "{document.title}"',
                'status': 'success'
            })
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
