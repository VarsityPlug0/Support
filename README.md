# 🔗 Safe Chain Assistant

A standalone Django-based AI-powered customer support system that follows the same architectural patterns as SafeCrypto. This application provides intelligent customer support with AI chat, ticket management, and file upload capabilities.

## 🚀 Features

### Core Features
- **AI-Powered Chat**: Real-time chat with OpenAI GPT integration
- **Ticket Management**: Create and track support tickets
- **File Upload**: Upload proof of payment and other documents
- **User Authentication**: Email-based registration and login
- **Admin Dashboard**: Comprehensive admin interface for managing tickets and POPs
- **Activity Logging**: Track all admin activities
- **Responsive Design**: Modern, mobile-friendly UI with dark theme

### Technical Features
- **Django 5.0**: Latest Django framework
- **Custom User Model**: Email-based authentication
- **Bootstrap 5**: Modern UI components
- **OpenAI Integration**: GPT-3.5-turbo for AI responses
- **File Handling**: Secure file upload and storage
- **Database**: SQLite for development, PostgreSQL ready for production

## 🏗️ Project Structure

```
ai-support-app/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── Procfile                 # Heroku deployment config
├── start.sh                 # Development startup script
├── build.sh                 # Production build script
├── README.md                # Project documentation
├── ai_support/              # Main Django project
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── core/                    # Main application
│   ├── __init__.py
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── urls.py              # URL patterns
│   ├── forms.py             # Form classes
│   ├── admin.py             # Django admin configuration
│   ├── tests.py             # Test cases
│   ├── static/              # Static files
│   │   └── css/
│   │       └── main.css     # Custom styles
│   └── templates/           # HTML templates
│       └── core/
│           ├── home.html    # Home page
│           ├── login.html   # Login page
│           ├── register.html # Registration page
│           ├── dashboard.html # User dashboard
│           ├── chat.html    # AI chat interface
│           ├── upload_pop.html # File upload page
│           ├── tickets.html # Ticket management
│           ├── admin_dashboard.html # Admin dashboard
│           ├── admin_pops.html # POP management
│           └── admin_tickets.html # Ticket management
├── templates/               # Global templates
│   └── base.html           # Base template
├── media/                  # User uploads
│   ├── pop_uploads/        # Proof of payment files
│   └── profile_pictures/   # User profile pictures
└── staticfiles/            # Collected static files
```

## 🗄️ Database Models

### CustomUser
- Email-based authentication
- Profile picture support
- Admin privileges
- IP tracking

### SupportTicket
- User association
- Status tracking (pending, in_progress, fixed, confirmed, rejected)
- Priority levels (low, medium, high, urgent)
- Admin assignment and notes

### ChatMessage
- Ticket association
- AI response tracking
- Message history

### ProofOfPayment
- File upload support
- Status management (pending, approved, rejected)
- Admin review system

### AdminActivityLog
- Activity tracking
- Admin action logging
- Audit trail

### Notification
- User notifications
- Read status tracking

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-support-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   OPENAI_API_KEY=your-openai-api-key
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main site: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

### Using the Start Script
```bash
chmod +x start.sh
./start.sh
```

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `OPENAI_API_KEY`: OpenAI API key for AI chat
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

### File Upload Settings
- Maximum file size: 10MB
- Allowed formats: JPG, PNG, PDF
- Upload directory: `media/pop_uploads/`

### AI Chat Configuration
- Model: GPT-3.5-turbo
- Max tokens: 500
- Context: Ticket history and recent messages

## 🎨 UI/UX Features

### Design System
- **Dark Theme**: Modern dark interface
- **Bootstrap 5**: Responsive components
- **Custom CSS**: Enhanced styling
- **Icons**: Bootstrap Icons integration
- **Animations**: Smooth transitions and hover effects

### Responsive Design
- Mobile-first approach
- Tablet and desktop optimized
- Touch-friendly interface

### Accessibility
- ARIA labels
- Keyboard navigation
- Focus indicators
- Screen reader support

## 🔒 Security Features

### Authentication
- Email-based login
- Password validation
- Session management
- CSRF protection

### File Upload Security
- File type validation
- Size limits
- Secure file storage
- Virus scanning ready

### Admin Security
- Staff member required decorators
- Activity logging
- IP tracking
- Audit trails

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

### Test Coverage
- Model tests
- View tests
- Form tests
- Admin tests

## 📦 Deployment

### Heroku Deployment
1. Create Heroku app
2. Set environment variables
3. Deploy using Git:
   ```bash
   git push heroku main
   ```

### Production Settings
- Set `DEBUG=False`
- Configure production database
- Set up static file serving
- Configure HTTPS

### Environment Variables for Production
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
OPENAI_API_KEY=your-openai-api-key
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=your-database-url
```

## 🔧 Customization

### Adding New Models
1. Define model in `core/models.py`
2. Create and run migrations
3. Add to admin interface
4. Create views and templates

### Customizing AI Responses
Modify the `get_ai_response()` function in `core/views.py` to customize AI behavior.

### Styling Changes
Edit `core/static/css/main.css` for custom styles.

## 📊 Monitoring and Analytics

### Admin Dashboard
- System statistics
- Recent activities
- User management
- File management

### Activity Logging
- Admin actions tracked
- User activity monitoring
- System health indicators

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔄 Updates and Maintenance

### Regular Maintenance
- Update dependencies
- Security patches
- Performance optimizations
- Feature enhancements

### Version History
- v1.0.0: Initial release
- v1.1.0: Enhanced AI chat
- v1.2.0: File upload improvements

---

**Built with ❤️ using Django and OpenAI** 