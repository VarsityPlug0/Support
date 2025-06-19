from django.contrib import admin  # Import Django admin
from django.contrib.auth.admin import UserAdmin  # Import UserAdmin for custom user model
from .models import CustomUser, SupportTicket, ChatMessage, ProofOfPayment, AdminActivityLog, Notification, Action  # Import our models
from django.utils.html import format_html

# Custom admin for CustomUser model
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser model"""
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_admin', 'is_staff', 'date_joined')  # Fields to display in list
    list_filter = ('is_admin', 'is_staff', 'is_active', 'date_joined')  # Filters for the list
    search_fields = ('email', 'username', 'first_name', 'last_name')  # Searchable fields
    ordering = ('-date_joined',)  # Default ordering
    
    fieldsets = UserAdmin.fieldsets + (  # Add custom fields to existing fieldsets
        ('Additional Info', {'fields': ('phone', 'profile_picture', 'is_admin', 'last_ip')}),  # Custom fields section
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (  # Add custom fields to add form
        ('Additional Info', {'fields': ('phone', 'is_admin')}),  # Custom fields for new users
    )

# Admin for SupportTicket model
class SupportTicketAdmin(admin.ModelAdmin):
    """Admin configuration for SupportTicket model"""
    list_display = ('title', 'user', 'status', 'priority', 'assigned_to', 'created_at')  # Fields to display
    list_filter = ('status', 'priority', 'created_at')  # Filters
    search_fields = ('title', 'description', 'user__email')  # Searchable fields
    readonly_fields = ('created_at', 'updated_at')  # Read-only fields
    ordering = ('-created_at',)  # Default ordering
    
    fieldsets = (
        ('Basic Information', {'fields': ('user', 'title', 'description')}),  # Basic info section
        ('Status & Priority', {'fields': ('status', 'priority', 'assigned_to')}),  # Status section
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),  # Timestamps section (collapsible)
        ('Admin Notes', {'fields': ('admin_notes',)}),  # Admin notes section
    )

# Admin for ChatMessage model
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin configuration for ChatMessage model"""
    # Enhanced list display with more useful information
    list_display = (
        'get_ticket_info',  # Custom method to show ticket info
        'get_user_info',    # Custom method to show user info
        'get_message_preview',  # Custom method to show message preview
        'get_ai_status',    # Custom method to show AI status with icon
        'get_created_time', # Custom method to show formatted time
        'get_ticket_status', # Custom method to show ticket status
        'is_ai_response'    # Direct field for inline editing
    )
    
    # Enhanced filters for better organization
    list_filter = (
        'is_ai_response',  # Filter by AI vs user messages
        ('created_at', admin.DateFieldListFilter),  # Date filter
        ('ticket__status', admin.ChoicesFieldListFilter),  # Ticket status filter
        ('ticket__priority', admin.ChoicesFieldListFilter),  # Ticket priority filter
        ('ticket__intent_category', admin.ChoicesFieldListFilter),  # Intent category filter
        ('user__is_admin', admin.BooleanFieldListFilter),  # Filter by admin users
    )
    
    # Enhanced search fields
    search_fields = (
        'message',  # Search in message content
        'ticket__title',  # Search in ticket titles
        'ticket__description',  # Search in ticket descriptions
        'user__email',  # Search by user email
        'user__username',  # Search by username
        'user__first_name',  # Search by first name
        'user__last_name',  # Search by last name
    )
    
    # Read-only fields
    readonly_fields = ('created_at', 'get_ticket_link', 'get_user_link', 'get_message_length')
    
    # Default ordering
    ordering = ('-created_at',)
    
    # Items per page
    list_per_page = 25
    
    # Enable date hierarchy for better navigation
    date_hierarchy = 'created_at'
    
    # Enable list editable for quick editing
    list_editable = ('is_ai_response',)
    
    # Custom list display methods
    def get_ticket_info(self, obj):
        """Display ticket information in a compact format"""
        if obj.ticket:
            status_color = {
                'pending': 'warning',
                'in_progress': 'info', 
                'fixed': 'success',
                'confirmed': 'success',
                'rejected': 'danger'
            }.get(obj.ticket.status, 'secondary')
            
            priority_color = {
                'low': 'secondary',
                'medium': 'info',
                'high': 'warning',
                'urgent': 'danger'
            }.get(obj.ticket.priority, 'secondary')
            
            return format_html(
                '<div class="ticket-info"><strong>{}</strong><br>'
                '<span class="badge bg-{}">{}</span> • '
                '<span class="badge bg-{}">{}</span><br>'
                '<small>ID: {}</small></div>',
                obj.ticket.title[:50] + ('...' if len(obj.ticket.title) > 50 else ''),
                status_color,
                obj.ticket.get_status_display(),
                priority_color,
                obj.ticket.get_priority_display(),
                obj.ticket.id
            )
        return '-'
    get_ticket_info.short_description = 'Ticket Info'
    get_ticket_info.admin_order_field = 'ticket__title'
    
    def get_user_info(self, obj):
        """Display user information in a compact format"""
        if obj.user:
            admin_badge = ''
            if obj.user.is_admin:
                admin_badge = ' <span class="badge bg-danger">Admin</span>'
            
            return format_html(
                '<div class="user-info"><strong>{}</strong><br>'
                '<small class="text-muted">{}</small>{}</div>',
                obj.user.email,
                obj.user.get_full_name() or obj.user.username,
                admin_badge
            )
        return '-'
    get_user_info.short_description = 'User'
    get_user_info.admin_order_field = 'user__email'
    
    def get_message_preview(self, obj):
        """Display a preview of the message content"""
        preview = obj.message[:100] + ('...' if len(obj.message) > 100 else '')
        return format_html(
            '<div class="message-preview" title="{}">{}</div>',
            obj.message,
            preview
        )
    get_message_preview.short_description = 'Message Preview'
    
    def get_ai_status(self, obj):
        """Display AI status with appropriate icon and color"""
        if obj.is_ai_response:
            return format_html(
                '<span class="badge bg-success">🤖 AI Response</span>'
            )
        else:
            return format_html(
                '<span class="badge bg-primary">👤 User Message</span>'
            )
    get_ai_status.short_description = 'Type'
    get_ai_status.admin_order_field = 'is_ai_response'
    
    def get_created_time(self, obj):
        """Display formatted creation time"""
        return format_html(
            '<div class="time-display"><strong>{}</strong><br>'
            '<small class="text-muted">{}</small></div>',
            obj.created_at.strftime('%b %d, %Y'),
            obj.created_at.strftime('%I:%M %p')
        )
    get_created_time.short_description = 'Created'
    get_created_time.admin_order_field = 'created_at'
    
    def get_ticket_status(self, obj):
        """Display ticket status with color coding"""
        if obj.ticket:
            status_colors = {
                'pending': 'warning',
                'in_progress': 'info',
                'fixed': 'success', 
                'confirmed': 'success',
                'rejected': 'danger'
            }
            color = status_colors.get(obj.ticket.status, 'secondary')
            return format_html(
                '<span class="badge bg-{}">{}</span>',
                color,
                obj.ticket.get_status_display()
            )
        return '-'
    get_ticket_status.short_description = 'Ticket Status'
    get_ticket_status.admin_order_field = 'ticket__status'
    
    # Custom methods for readonly fields
    def get_ticket_link(self, obj):
        """Display ticket as a clickable link"""
        if obj.ticket:
            return format_html(
                '<a href="{}" target="_blank" class="btn btn-sm btn-outline-primary">{}</a>',
                f'/admin/core/supportticket/{obj.ticket.id}/change/',
                f'View Ticket #{obj.ticket.id}'
            )
        return '-'
    get_ticket_link.short_description = 'Ticket Link'
    
    def get_user_link(self, obj):
        """Display user as a clickable link"""
        if obj.user:
            return format_html(
                '<a href="{}" target="_blank" class="btn btn-sm btn-outline-info">{}</a>',
                f'/admin/core/customuser/{obj.user.id}/change/',
                f'View User: {obj.user.email}'
            )
        return '-'
    get_user_link.short_description = 'User Link'
    
    def get_message_length(self, obj):
        """Display message length with color coding"""
        length = len(obj.message)
        if length < 50:
            color = 'success'
        elif length < 200:
            color = 'warning'
        else:
            color = 'danger'
        
        return format_html(
            '<span class="badge bg-{}">{} characters</span>',
            color,
            length
        )
    get_message_length.short_description = 'Message Length'
    
    # Custom fieldsets for better organization
    fieldsets = (
        ('Message Information', {
            'fields': ('message', 'is_ai_response', 'created_at', 'get_message_length'),
            'classes': ('wide',)
        }),
        ('Related Information', {
            'fields': ('ticket', 'user', 'get_ticket_link', 'get_user_link'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom actions
    actions = ['mark_as_ai_response', 'mark_as_user_message', 'export_messages', 'delete_old_messages']
    
    def mark_as_ai_response(self, request, queryset):
        """Mark selected messages as AI responses"""
        updated = queryset.update(is_ai_response=True)
        self.message_user(request, f'{updated} messages marked as AI responses.')
    mark_as_ai_response.short_description = "Mark selected messages as AI responses"
    
    def mark_as_user_message(self, request, queryset):
        """Mark selected messages as user messages"""
        updated = queryset.update(is_ai_response=False)
        self.message_user(request, f'{updated} messages marked as user messages.')
    mark_as_user_message.short_description = "Mark selected messages as user messages"
    
    def export_messages(self, request, queryset):
        """Export selected messages (placeholder for future implementation)"""
        self.message_user(request, f'{queryset.count()} messages selected for export.')
    export_messages.short_description = "Export selected messages"
    
    def delete_old_messages(self, request, queryset):
        """Delete messages older than 30 days"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        old_messages = queryset.filter(created_at__lt=cutoff_date)
        count = old_messages.count()
        old_messages.delete()
        self.message_user(request, f'{count} old messages deleted.')
    delete_old_messages.short_description = "Delete messages older than 30 days"
    
    # Custom CSS for better styling
    class Media:
        css = {
            'all': ('admin/css/chat_message_admin.css',)
        }

# Admin for ProofOfPayment model
class ProofOfPaymentAdmin(admin.ModelAdmin):
    """Admin configuration for ProofOfPayment model"""
    list_display = ('user', 'file_name', 'status', 'created_at')  # Fields to display
    list_filter = ('status', 'created_at')  # Filters
    search_fields = ('user__email', 'file_name', 'reference_number')  # Searchable fields
    readonly_fields = ('file_size', 'created_at', 'updated_at')  # Read-only fields
    ordering = ('-created_at',)  # Default ordering
    
    fieldsets = (
        ('User Information', {'fields': ('user', 'email', 'reference_number')}),  # User info section
        ('File Information', {'fields': ('file', 'file_name', 'file_size')}),  # File info section
        ('Status', {'fields': ('status', 'admin_notes')}),  # Status section
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),  # Timestamps section (collapsible)
    )

# Admin for AdminActivityLog model
class AdminActivityLogAdmin(admin.ModelAdmin):
    """Admin configuration for AdminActivityLog model"""
    list_display = ('admin_user', 'action', 'target_model', 'timestamp')  # Fields to display
    list_filter = ('action', 'target_model', 'timestamp')  # Filters
    search_fields = ('admin_user__email', 'action', 'details')  # Searchable fields
    readonly_fields = ('timestamp',)  # Read-only fields
    ordering = ('-timestamp',)  # Default ordering

# Admin for Notification model
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model"""
    list_display = ('user', 'title', 'is_read', 'created_at')  # Fields to display
    list_filter = ('is_read', 'created_at')  # Filters
    search_fields = ('user__email', 'title', 'message')  # Searchable fields
    readonly_fields = ('created_at',)  # Read-only fields
    ordering = ('-created_at',)  # Default ordering

# Admin for Action model
class ActionAdmin(admin.ModelAdmin):
    """Admin configuration for Action model"""
    list_display = (
        'title', 
        'user', 
        'status', 
        'priority', 
        'assigned_by', 
        'due_date', 
        'is_overdue_display',
        'created_at'
    )  # Fields to display in list
    list_filter = (
        'status', 
        'priority', 
        'created_at', 
        'due_date',
        ('assigned_by', admin.RelatedOnlyFieldListFilter)
    )  # Filters for the list
    search_fields = (
        'title', 
        'description', 
        'instructions', 
        'user__email', 
        'assigned_by__email'
    )  # Searchable fields
    readonly_fields = ('created_at', 'updated_at', 'completed_at')  # Read-only fields
    ordering = ('-priority', '-created_at')  # Default ordering
    
    # Enable list editable for quick status updates
    list_editable = ('status', 'priority')
    
    # Custom actions
    actions = ['mark_as_completed', 'mark_as_confirmed', 'mark_as_cancelled', 'assign_high_priority']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'instructions')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'assigned_by', 'ticket')
        }),
        ('Timeline', {
            'fields': ('due_date', 'completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('completion_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue_display(self, obj):
        """Display overdue status with color coding"""
        if obj.is_overdue():
            return format_html(
                '<span class="badge bg-danger">Overdue</span>'
            )
        elif obj.due_date:
            return format_html(
                '<span class="badge bg-success">On Time</span>'
            )
        return '-'
    is_overdue_display.short_description = 'Due Status'
    
    # Custom admin actions
    def mark_as_completed(self, request, queryset):
        """Mark selected actions as completed"""
        from django.utils import timezone
        updated = queryset.update(
            status='completed',
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} action(s) marked as completed.')
    mark_as_completed.short_description = "Mark selected actions as completed"
    
    def mark_as_confirmed(self, request, queryset):
        """Mark selected actions as confirmed"""
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} action(s) marked as confirmed.')
    mark_as_confirmed.short_description = "Mark selected actions as confirmed"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected actions as cancelled"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} action(s) marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected actions as cancelled"
    
    def assign_high_priority(self, request, queryset):
        """Assign high priority to selected actions"""
        updated = queryset.update(priority='high')
        self.message_user(request, f'{updated} action(s) assigned high priority.')
    assign_high_priority.short_description = "Assign high priority to selected actions"
    
    class Media:
        css = {
            'all': ('admin/css/action_admin.css',)
        }

# Register models with admin
admin.site.register(CustomUser, CustomUserAdmin)  # Register CustomUser with custom admin
admin.site.register(SupportTicket, SupportTicketAdmin)  # Register SupportTicket with custom admin
admin.site.register(ChatMessage, ChatMessageAdmin)  # Register ChatMessage with custom admin
admin.site.register(ProofOfPayment, ProofOfPaymentAdmin)  # Register ProofOfPayment with custom admin
admin.site.register(AdminActivityLog, AdminActivityLogAdmin)  # Register AdminActivityLog with custom admin
admin.site.register(Notification, NotificationAdmin)  # Register Notification with custom admin
admin.site.register(Action, ActionAdmin)  # Register Action with custom admin 