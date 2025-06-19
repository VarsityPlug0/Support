from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver

# Custom user model (following SafeCrypto pattern)
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Email field for unique user identification
    phone = models.CharField(max_length=15, blank=True)  # Phone number field (optional)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)  # User profile picture
    is_admin = models.BooleanField(default=False)  # Admin flag for special privileges
    last_ip = models.GenericIPAddressField(null=True, blank=True)  # Track user's last IP address
    
    USERNAME_FIELD = 'email'  # Use email as the primary login field
    REQUIRED_FIELDS = ['username']  # Username is still required for Django admin

    def __str__(self):
        return self.email  # String representation returns email

# Support ticket model for customer issues
class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),      # Ticket is waiting for review
        ('in_progress', 'In Progress'),  # Ticket is being worked on
        ('fixed', 'Fixed'),          # Issue has been resolved
        ('confirmed', 'Confirmed'),  # User confirmed the fix
        ('rejected', 'Rejected'),    # Ticket was rejected
        ('waiting_for_documents', 'Waiting for Documents'),  # Waiting for user to upload documents
        ('ready_for_admin', 'Ready for Admin Review'),  # All documents collected, ready for admin
        ('waiting_for_admin', 'Waiting for Admin Review'),  # User confirmed issue, waiting for admin
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),              # Low priority issues
        ('medium', 'Medium'),        # Medium priority issues
        ('high', 'High'),            # High priority issues
        ('urgent', 'Urgent'),        # Urgent issues requiring immediate attention
    ]
    
    INTENT_CHOICES = [
        ('billing', 'Billing/Payment'),  # Payment-related issues
        ('technical', 'Technical Support'),  # Technical problems
        ('account', 'Account Issues'),  # Account-related problems
        ('general', 'General Inquiry'),  # General questions
        ('complaint', 'Complaint'),  # User complaints
        ('feature_request', 'Feature Request'),  # Feature requests
        ('deposit_confirmation', 'Deposit Confirmation'),  # Deposit confirmation request
        ('withdrawal_processing', 'Withdrawal Processing'),  # Withdrawal processing request
        ('investment_verification', 'Investment Verification'),  # Investment verification
        ('tier_upgrade', 'Tier Upgrade'),  # Tier upgrade request
        ('referral_verification', 'Referral Verification'),  # Referral verification
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # User who created the ticket
    title = models.CharField(max_length=255)  # Ticket title/summary
    description = models.TextField()  # Detailed description of the issue
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')  # Current status
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')  # Priority level
    intent_category = models.CharField(max_length=25, choices=INTENT_CHOICES, default='general')  # AI-detected intent
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')  # Admin assigned to handle
    created_at = models.DateTimeField(auto_now_add=True)  # When ticket was created
    updated_at = models.DateTimeField(auto_now=True)  # When ticket was last updated
    admin_notes = models.TextField(blank=True)  # Internal notes from admin
    ai_summary = models.TextField(blank=True)  # AI-generated summary of the issue
    requires_pop = models.BooleanField(default=False)  # Whether POP is required for this ticket
    user_satisfaction = models.IntegerField(null=True, blank=True)  # User satisfaction rating (1-5)
    resolution_time = models.DurationField(null=True, blank=True)  # Time taken to resolve
    
    # New fields for intelligent workflow
    admin_report = models.ForeignKey('AdminReport', on_delete=models.SET_NULL, null=True, blank=True)  # Associated admin report
    required_documents = models.JSONField(default=list)  # List of required document types
    collected_documents = models.ManyToManyField('ProofOfPayment', blank=True)  # Collected documents
    ai_recommendation = models.TextField(blank=True)  # AI recommendation for admin action
    next_admin_action = models.CharField(max_length=100, blank=True)  # What admin should do next

    def __str__(self):
        return f"{self.user.email} - {self.title}"  # String representation

    class Meta:
        ordering = ['-created_at']  # Order by newest first

# Chat message model for AI conversations
class ChatMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')  # Associated ticket
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # User who sent the message
    message = models.TextField()  # The actual message content
    is_ai_response = models.BooleanField(default=False)  # Flag to identify AI responses
    created_at = models.DateTimeField(auto_now_add=True)  # When message was sent

    def __str__(self):
        return f"{self.ticket.title} - {self.user.email}"  # String representation

    class Meta:
        ordering = ['created_at']  # Order by oldest first for chat flow

# Proof of Payment model (following SafeCrypto deposit pattern)
class ProofOfPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),      # POP is waiting for review
        ('approved', 'Approved'),    # POP has been approved
        ('rejected', 'Rejected'),    # POP has been rejected
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # User who uploaded the POP
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, null=True, blank=True)  # Associated ticket (optional)
    email = models.EmailField()  # Email associated with the payment
    reference_number = models.CharField(max_length=100, blank=True)  # Payment reference number
    file = models.FileField(upload_to='pop_uploads/')  # Uploaded file
    file_name = models.CharField(max_length=255)  # Original filename
    file_size = models.IntegerField()  # File size in bytes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Current status
    admin_notes = models.TextField(blank=True)  # Admin notes about the POP
    created_at = models.DateTimeField(auto_now_add=True)  # When POP was uploaded
    updated_at = models.DateTimeField(auto_now=True)  # When POP was last updated

    def __str__(self):
        return f"{self.user.email} - {self.file_name}"  # String representation

    class Meta:
        ordering = ['-created_at']  # Order by newest first

# Admin activity log (following SafeCrypto pattern)
class AdminActivityLog(models.Model):
    admin_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Admin who performed the action
    action = models.CharField(max_length=100)  # Description of the action
    target_model = models.CharField(max_length=100)  # Which model was affected
    target_id = models.IntegerField(null=True, blank=True)  # ID of the affected object
    details = models.TextField()  # Detailed description of what happened
    timestamp = models.DateTimeField(auto_now_add=True)  # When the action occurred

    class Meta:
        ordering = ['-timestamp']  # Order by newest first
        verbose_name = 'Admin Activity Log'  # Human-readable name
        verbose_name_plural = 'Admin Activity Logs'  # Plural form

    def __str__(self):
        return f"{self.admin_user.email} - {self.action}"  # String representation

# Notification model for user alerts
class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # User to notify
    title = models.CharField(max_length=255)  # Notification title
    message = models.TextField()  # Notification message
    is_read = models.BooleanField(default=False)  # Whether user has read it
    created_at = models.DateTimeField(auto_now_add=True)  # When notification was created

    class Meta:
        ordering = ['-created_at']  # Order by newest first

    def __str__(self):
        return f"{self.user.email} - {self.title}"  # String representation

# Action model for user tasks
class Action(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),      # Action is waiting to be completed
        ('in_progress', 'In Progress'),  # User is working on the action
        ('completed', 'Completed'),  # Action has been completed
        ('confirmed', 'Confirmed'),  # Admin has confirmed completion
        ('cancelled', 'Cancelled'),  # Action was cancelled
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),              # Low priority actions
        ('medium', 'Medium'),        # Medium priority actions
        ('high', 'High'),            # High priority actions
        ('urgent', 'Urgent'),        # Urgent actions requiring immediate attention
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # User assigned to the action
    title = models.CharField(max_length=255)  # Action title/summary
    description = models.TextField()  # Detailed description of what needs to be done
    instructions = models.TextField()  # Step-by-step instructions for the user
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Current status
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')  # Priority level
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_actions')  # Admin who assigned the action
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, null=True, blank=True, related_name='actions')  # Associated ticket (optional)
    due_date = models.DateTimeField(null=True, blank=True)  # When action should be completed
    completed_at = models.DateTimeField(null=True, blank=True)  # When action was completed
    completion_notes = models.TextField(blank=True)  # User's notes about completion
    admin_notes = models.TextField(blank=True)  # Admin notes about the action
    created_at = models.DateTimeField(auto_now_add=True)  # When action was created
    updated_at = models.DateTimeField(auto_now=True)  # When action was last updated

    def __str__(self):
        return f"{self.user.email} - {self.title}"  # String representation

    class Meta:
        ordering = ['-priority', '-created_at']  # Order by priority first, then by newest first

    def is_overdue(self):
        """Check if the action is overdue"""
        if self.due_date and self.status not in ['completed', 'confirmed', 'cancelled']:
            return timezone.now() > self.due_date
        return False

    def get_priority_color(self):
        """Get Bootstrap color class for priority"""
        colors = {
            'low': 'success',
            'medium': 'warning', 
            'high': 'danger',
            'urgent': 'danger'
        }
        return colors.get(self.priority, 'secondary')

    def get_status_color(self):
        """Get Bootstrap color class for status"""
        colors = {
            'pending': 'secondary',
            'in_progress': 'primary',
            'completed': 'success',
            'confirmed': 'success',
            'cancelled': 'danger'
        }
        return colors.get(self.status, 'secondary')

# Admin Report model for compiled reports sent to admin
class AdminReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('deposit_confirmation', 'Deposit Confirmation'),
        ('withdrawal_processing', 'Withdrawal Processing'),
        ('investment_verification', 'Investment Verification'),
        ('payment_verification', 'Payment Verification'),
        ('account_verification', 'Account Verification'),
        ('tier_upgrade', 'Tier Upgrade Request'),
        ('referral_verification', 'Referral Verification'),
        ('general_support', 'General Support'),
        ('user_confirmed_issue', 'User Confirmed Issue'),
    ]
    
    ADMIN_MANAGEMENT_AREAS = [
        ('deposits', 'Deposits'),
        ('investment_tiers', 'Investment Tiers'),
        ('investments', 'Investments'),
        ('users', 'Users'),
        ('wallets', 'Wallets'),
        ('withdrawals', 'Withdrawals'),
        ('referrals', 'Referrals'),
        ('daily_specials', 'Daily Specials'),
        ('vouchers', 'Vouchers'),
        ('ip_addresses', 'IP Addresses'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('requires_more_info', 'Requires More Information'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic information
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    admin_management_area = models.CharField(max_length=50, choices=ADMIN_MANAGEMENT_AREAS, blank=True)  # Which admin area should handle this
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # User and ticket association
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, null=True, blank=True)
    
    # Required documents and information
    required_documents = models.JSONField(default=list)  # List of required document types
    collected_documents = models.ManyToManyField(ProofOfPayment, blank=True)
    additional_info_required = models.JSONField(default=list)  # List of additional info needed
    
    # AI analysis and recommendations
    ai_analysis = models.TextField(blank=True)  # AI analysis of the situation
    ai_recommendation = models.TextField(blank=True)  # AI recommendation for admin action
    risk_assessment = models.CharField(max_length=20, default='low')  # Low, Medium, High
    
    # Admin handling
    assigned_admin = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    admin_notes = models.TextField(blank=True)
    admin_action_taken = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.report_type} - {self.user.email} - {self.status}"
    
    def get_required_documents_text(self):
        """Get human-readable list of required documents"""
        document_map = {
            'proof_of_payment': 'Proof of Payment',
            'bank_statement': 'Bank Statement',
            'id_document': 'ID Document',
            'selfie': 'Selfie with ID',
            'investment_confirmation': 'Investment Confirmation',
            'withdrawal_request': 'Withdrawal Request Form',
            'referral_proof': 'Referral Proof',
            'account_statement': 'Account Statement',
        }
        return [document_map.get(doc, doc) for doc in self.required_documents]
    
    def get_missing_documents(self):
        """Get list of documents that are still required"""
        collected_types = [pop.file_name for pop in self.collected_documents.all()]
        missing = []
        for required in self.required_documents:
            if not any(required in collected for collected in collected_types):
                missing.append(required)
        return missing
    
    def is_ready_for_admin_review(self):
        """Check if all required documents are collected"""
        return len(self.get_missing_documents()) == 0 