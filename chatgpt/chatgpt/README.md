# ChatGPT Clone with Django and Gemini AI

A modern, responsive ChatGPT-like web application built with Django backend and Google's Gemini AI integration.

## Features

- 🤖 **AI Chat Interface**: Powered by Google's Gemini 2.0 Flash model
- 💬 **Real-time Messaging**: Asynchronous chat with typing indicators
- 📱 **Responsive Design**: Beautiful UI that works on desktop and mobile
- 💾 **Chat History**: Persistent chat sessions stored in SQLite database
- 🔒 **Secure**: CSRF protection and environment variable configuration
- ⚡ **Fast**: Optimized for quick responses and smooth user experience

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Google Gemini API key

## Installation & Setup

### 1. Clone or Download the Project

```bash
# If using git
git clone <repository-url>
cd chatgpt

# Or simply download and extract the files
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

1. Copy the example environment file:
   ```bash
   copy env.example .env
   ```

2. Edit the `.env` file and add your configuration:
   ```
   SECRET_KEY=your-django-secret-key-here
   DEBUG=True
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

### 5. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key and add it to your `.env` file

### 6. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional, for admin access)
python manage.py createsuperuser
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

### 8. Access the Application

Open your browser and go to: `http://localhost:8000`

## Usage

1. **Start Chatting**: Type your message in the input field and press Enter or click Send
2. **View History**: Your chat history is automatically saved and loaded when you refresh the page
3. **Admin Panel**: Access `http://localhost:8000/admin/` to view chat history and manage data

## Project Structure

```
chatgpt/
├── chatgpt_project/          # Django project settings
│   ├── __init__.py
│   ├── settings.py          # Main settings file
│   ├── urls.py              # URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── chatbot/                  # Main chat application
│   ├── __init__.py
│   ├── models.py            # Database models
│   ├── views.py             # API views
│   ├── urls.py              # App URL patterns
│   └── admin.py             # Admin configuration
├── templates/                # HTML templates
│   └── chat.html            # Main chat interface
├── static/                   # Static files
│   └── js/
│       └── chat.js          # Frontend JavaScript
├── requirements.txt          # Python dependencies
├── env.example              # Environment variables example
├── manage.py                # Django management script
└── README.md                # This file
```

## API Endpoints

- `GET /` - Main chat interface
- `POST /api/chat/` - Send message to AI
- `GET /api/history/` - Get chat history for current session

## Configuration Options

### Environment Variables

- `SECRET_KEY`: Django secret key for security
- `DEBUG`: Enable/disable debug mode (True/False)
- `GEMINI_API_KEY`: Your Google Gemini API key

### Django Settings

The application is configured with:
- SQLite database for development
- CORS enabled for local development
- Session-based chat history
- Static files serving

## Troubleshooting

### Common Issues

1. **"Gemini API key not configured" error**
   - Make sure you've added your API key to the `.env` file
   - Restart the Django server after adding the key

2. **CORS errors in browser console**
   - Ensure you're accessing the app via `localhost:8000` or `127.0.0.1:8000`
   - Check that `django-cors-headers` is installed

3. **Static files not loading**
   - Run `python manage.py collectstatic` if needed
   - Check that `STATICFILES_DIRS` is properly configured

4. **Database errors**
   - Run `python manage.py makemigrations` and `python manage.py migrate`
   - Check that the database file has proper permissions

### Getting Help

If you encounter issues:
1. Check the Django console for error messages
2. Verify your API key is correct and active
3. Ensure all dependencies are installed correctly
4. Check the browser console for JavaScript errors

## Future Enhancements

- [ ] Streaming responses for real-time typing effect
- [ ] Voice input/output support
- [ ] User authentication and personal chat histories
- [ ] Multiple AI model support
- [ ] File upload capabilities
- [ ] Dark/light theme toggle

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
