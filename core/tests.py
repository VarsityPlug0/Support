from django.test import TestCase, Client  # Import Django test classes
from django.urls import reverse  # Import reverse for URL generation
from django.contrib.auth import get_user_model  # Import user model
from .models import SupportTicket, ChatMessage, ProofOfPayment, Notification, AdminActivityLog  # Import our models

User = get_user_model()  # Get the custom user model

class CustomUserModelTest(TestCase):
    """Test cases for CustomUser model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(  # Create a test user
            email='test@example.com',  # Set email
            username='testuser',  # Set username
            password='testpass123'  # Set password
        )
    
    def test_user_creation(self):
        """Test that user can be created"""
        self.assertEqual(self.user.email, 'test@example.com')  # Check email
        self.assertEqual(self.user.username, 'testuser')  # Check username
        self.assertTrue(self.user.check_password('testpass123'))  # Check password
    
    def test_user_string_representation(self):
        """Test user string representation"""
        self.assertEqual(str(self.user), 'test@example.com')  # Check string representation

class SupportTicketModelTest(TestCase):
    """Test cases for SupportTicket model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(  # Create a test user
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.ticket = SupportTicket.objects.create(  # Create a test ticket
            user=self.user,  # Set user
            title='Test Ticket',  # Set title
            description='Test description',  # Set description
            priority='medium'  # Set priority
        )
    
    def test_ticket_creation(self):
        """Test that ticket can be created"""
        self.assertEqual(self.ticket.title, 'Test Ticket')  # Check title
        self.assertEqual(self.ticket.user, self.user)  # Check user
        self.assertEqual(self.ticket.status, 'pending')  # Check default status
        self.assertEqual(self.ticket.priority, 'medium')  # Check priority
    
    def test_ticket_string_representation(self):
        """Test ticket string representation"""
        expected = f"{self.user.email} - Test Ticket"  # Expected string
        self.assertEqual(str(self.ticket), expected)  # Check string representation

class ChatMessageModelTest(TestCase):
    """Test cases for ChatMessage model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(  # Create a test user
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.ticket = SupportTicket.objects.create(  # Create a test ticket
            user=self.user,
            title='Test Ticket',
            description='Test description'
        )
        self.message = ChatMessage.objects.create(  # Create a test message
            ticket=self.ticket,  # Set ticket
            user=self.user,  # Set user
            message='Test message',  # Set message
            is_ai_response=False  # Set as user message
        )
    
    def test_message_creation(self):
        """Test that message can be created"""
        self.assertEqual(self.message.message, 'Test message')  # Check message
        self.assertEqual(self.message.ticket, self.ticket)  # Check ticket
        self.assertEqual(self.message.user, self.user)  # Check user
        self.assertFalse(self.message.is_ai_response)  # Check AI response flag

class ViewsTest(TestCase):
    """Test cases for views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()  # Create test client
        self.user = User.objects.create_user(  # Create a test user
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_home_view(self):
        """Test home view"""
        response = self.client.get(reverse('home'))  # Get home page
        self.assertEqual(response.status_code, 200)  # Check status code
        self.assertTemplateUsed(response, 'core/home.html')  # Check template used
    
    def test_register_view_get(self):
        """Test register view GET request"""
        response = self.client.get(reverse('register'))  # Get register page
        self.assertEqual(response.status_code, 200)  # Check status code
        self.assertTemplateUsed(response, 'core/register.html')  # Check template used
    
    def test_login_view_get(self):
        """Test login view GET request"""
        response = self.client.get(reverse('login'))  # Get login page
        self.assertEqual(response.status_code, 200)  # Check status code
        self.assertTemplateUsed(response, 'core/login.html')  # Check template used
    
    def test_dashboard_view_authenticated(self):
        """Test dashboard view for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')  # Login user
        response = self.client.get(reverse('dashboard'))  # Get dashboard
        self.assertEqual(response.status_code, 200)  # Check status code
        self.assertTemplateUsed(response, 'core/dashboard.html')  # Check template used
    
    def test_dashboard_view_unauthenticated(self):
        """Test dashboard view for unauthenticated user"""
        response = self.client.get(reverse('dashboard'))  # Get dashboard without login
        self.assertEqual(response.status_code, 302)  # Should redirect to login
    
    def test_chat_view_authenticated(self):
        """Test chat view for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')  # Login user
        response = self.client.get(reverse('chat'))  # Get chat page
        self.assertEqual(response.status_code, 200)  # Check status code
        self.assertTemplateUsed(response, 'core/chat.html')  # Check template used
    
    def test_upload_pop_view_authenticated(self):
        """Test upload POP view for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')  # Login user
        response = self.client.get(reverse('upload_pop'))  # Get upload POP page
        self.assertEqual(response.status_code, 200)  # Check status code
        self.assertTemplateUsed(response, 'core/upload_pop.html')  # Check template used
    
    def test_tickets_view_authenticated(self):
        """Test tickets view for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')  # Login user
        response = self.client.get(reverse('tickets'))  # Get tickets page
        self.assertEqual(response.status_code, 200)  # Check status code
        self.assertTemplateUsed(response, 'core/tickets.html')  # Check template used

class AdminViewsTest(TestCase):
    """Test cases for admin views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()  # Create test client
        self.admin_user = User.objects.create_user(  # Create admin user
            email='admin@example.com',
            username='admin',
            password='adminpass123',
            is_staff=True,  # Make staff
            is_admin=True  # Make admin
        )
    
    def test_admin_dashboard_view_authenticated(self):
        """Test admin dashboard view for authenticated admin"""
        self.client.login(email='admin@example.com', password='adminpass123')  # Login admin
        response = self.client.get(reverse('admin_dashboard'))  # Get admin dashboard
        self.assertEqual(response.status_code, 200)  # Check status code
        self.assertTemplateUsed(response, 'core/admin_dashboard.html')  # Check template used
    
    def test_admin_dashboard_view_unauthenticated(self):
        """Test admin dashboard view for unauthenticated user"""
        response = self.client.get(reverse('admin_dashboard'))  # Get admin dashboard without login
        self.assertEqual(response.status_code, 302)  # Should redirect to login
    
    def test_admin_pops_view_authenticated(self):
        """Test admin POPs view for authenticated admin"""
        self.client.login(email='admin@example.com', password='adminpass123')  # Login admin
        response = self.client.get(reverse('admin_pops'))  # Get admin POPs page
        self.assertEqual(response.status_code, 200)  # Check status code
        self.assertTemplateUsed(response, 'core/admin_pops.html')  # Check template used
    
    def test_admin_tickets_view_authenticated(self):
        """Test admin tickets view for authenticated admin"""
        self.client.login(email='admin@example.com', password='adminpass123')  # Login admin
        response = self.client.get(reverse('admin_tickets'))  # Get admin tickets page
        self.assertEqual(response.status_code, 200)  # Check status code
        self.assertTemplateUsed(response, 'core/admin_tickets.html')  # Check template used 