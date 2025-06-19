# Smart Assistant Chat Application
**Purpose:**  
A web-based smart assistant that interacts with users via chat, understands and categorizes their issues, summarizes them, and forwards relevant information (including uploaded documents) to the admin team for resolution.

---

## Core Functionality

1. **Conversational Interface:**  
   - Users interact with the assistant through a real-time chat interface
   - The assistant uses NLP to understand user queries, requests, and issues
   - Chat interface supports both user and AI messages with distinct styling
   - Messages include timestamps and sender information

2. **Issue Categorization & Summarization:**  
   - Automatic categorization of support tickets into:
     - Billing/Payment issues
     - Technical Support
     - Account Issues
     - General Inquiries
     - Complaints
     - Feature Requests
   - AI-generated summaries for quick admin review
   - Priority levels: Urgent, High, Medium, Low
   - Status tracking: Pending, In Progress, Fixed, Confirmed, Rejected

3. **Document Management:**  
   - Support for Proof of Payment (POP) uploads
   - Document status tracking (Pending, Approved, Rejected)
   - Secure file storage in media/pop_uploads/
   - File validation and type restrictions

4. **Admin Dashboard:**  
   - Real-time statistics and metrics
   - Quick filters for ticket management
   - Chat-style ticket display
   - Document review interface
   - Management area reports
   - Priority-based color coding

5. **User Management:**  
   - Custom user model with email authentication
   - Profile management
   - Action tracking system
   - Role-based access control (Admin/User)

---

## Key Features

### Natural Language Processing (NLP)
- Intent recognition for ticket categorization
- Automatic summarization of user issues
- Sentiment analysis for priority assignment
- Context-aware responses

### Real-Time Chat Interface
- WhatsApp/ChatGPT inspired design
- Message bubbles with sender avatars
- Timestamp display
- File upload integration
- Status indicators

### Document Processing
- Supported file types: PDF, Images
- Automatic file naming and organization
- Secure storage and access control
- Admin review workflow

### Admin Features
- Dashboard with real-time metrics:
  - Urgent tickets count
  - New tickets
  - In-progress tickets
  - Resolved tickets
  - Document statistics
- Quick filters:
  - Status
  - Priority
  - Category
  - Search functionality
- Management area reports
- Document review tools

### Security Features
- CSRF protection
- Secure file uploads
- Role-based permissions
- Session management
- Audit logging

---

## System Architecture

### Frontend Components
1. **Chat Interface** (`core/templates/core/chat_simple.html`):
   - Real-time message display
   - File upload widget
   - Status indicators
   - Responsive design

2. **Admin Dashboard** (`core/templates/core/admin/dashboard.html`):
   - Statistics cards
   - Ticket management
   - Document review
   - Management reports

### Backend Components
1. **Models** (`core/models.py`):
   - CustomUser
   - SupportTicket
   - Action
   - Document

2. **Views** (`core/views.py`):
   - Chat handling
   - File uploads
   - Admin functions
   - API endpoints

3. **Forms** (`core/forms.py`):
   - User registration
   - Document upload
   - Ticket creation

### Database Schema
- Users table (email, role, profile info)
- Tickets table (title, description, category, priority, status)
- Documents table (file path, status, metadata)
- Actions table (user tasks and notifications)

---

## Developer Guidelines

### Setting Up Development Environment
1. Clone repository
2. Install requirements: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Create superuser: `python manage.py createsuperuser`
5. Load sample data: `python manage.py create_sample_actions`

### Code Style
- Follow PEP 8 guidelines
- Use Django's coding style
- Document all functions and classes
- Include type hints where possible

### Testing
- Write unit tests for models and views
- Test file upload functionality
- Verify NLP integration
- Check security measures

### Security Best Practices
- Validate all file uploads
- Implement CSRF protection
- Use secure session handling
- Sanitize user input
- Regular security audits

---

## Support Team Guidelines

### Ticket Management
1. Monitor dashboard for new tickets
2. Review AI-generated summaries
3. Check attached documents
4. Assign priorities
5. Update ticket status

### Document Review Process
1. Access document review section
2. Verify file contents
3. Check for completeness
4. Approve or reject with notes
5. Update user via chat

### Priority Levels
- **Urgent**: Immediate attention required (red)
- **High**: Address within 24 hours (yellow)
- **Medium**: Handle within 48 hours (blue)
- **Low**: Process within 1 week (green)

### Status Updates
1. Pending: New ticket
2. In Progress: Under review
3. Fixed: Solution provided
4. Confirmed: User verified
5. Rejected: Invalid ticket

---

## Maintenance and Updates

### Regular Tasks
- Monitor system performance
- Review error logs
- Update NLP models
- Clean up old files
- Backup database

### Troubleshooting
1. Check error logs
2. Verify file permissions
3. Test database connections
4. Monitor API responses
5. Review security alerts

---

For technical support or questions, contact the development team at dev@example.com 