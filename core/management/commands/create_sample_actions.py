from django.core.management.base import BaseCommand  # Import BaseCommand
from django.utils import timezone  # Import timezone utilities
from datetime import timedelta  # Import timedelta for date calculations
from core.models import CustomUser, Action  # Import our models

class Command(BaseCommand):  # Define command class
    help = 'Create sample actions for testing the actions system'  # Command help text

    def handle(self, *args, **options):  # Main command handler
        # Get or create a test user if no users exist
        if not CustomUser.objects.exists():  # If no users exist
            self.stdout.write(self.style.WARNING('No users found. Creating a test user...'))  # Warning message
            user = CustomUser.objects.create_user(  # Create test user
                email='test@example.com',  # Test email
                password='testpass123',  # Test password
                first_name='Test',  # Test first name
                last_name='User'  # Test last name
            )
            self.stdout.write(self.style.SUCCESS(f'Created test user: {user.email}'))  # Success message
        else:  # If users exist
            user = CustomUser.objects.first()  # Get first user
            self.stdout.write(self.style.SUCCESS(f'Using existing user: {user.email}'))  # Success message

        # Sample actions data
        sample_actions = [  # List of sample actions
            {
                'title': 'Complete Profile Information',  # Action title
                'description': 'Please update your profile with your full name, phone number, and address.',  # Action description
                'instructions': 'Go to your profile page and fill in any missing information. This helps us provide better support.',  # Action instructions
                'priority': 'medium',  # Action priority
                'status': 'pending',  # Action status
                'due_date': timezone.now() + timedelta(days=7),  # Due in 7 days
            },
            {
                'title': 'Upload Proof of Payment',  # Action title
                'description': 'Upload the receipt or screenshot of your recent payment for verification.',  # Action description
                'instructions': 'Take a clear photo or screenshot of your payment receipt and upload it through the POP upload page.',  # Action instructions
                'priority': 'high',  # Action priority
                'status': 'pending',  # Action status
                'due_date': timezone.now() + timedelta(days=3),  # Due in 3 days
            },
            {
                'title': 'Review Support Ticket',  # Action title
                'description': 'Please review and respond to the latest message in your support ticket #123.',  # Action description
                'instructions': 'Check your support tickets and provide any additional information requested by our support team.',  # Action instructions
                'priority': 'urgent',  # Action priority
                'status': 'in_progress',  # Action status
                'due_date': timezone.now() + timedelta(days=1),  # Due in 1 day
            },
            {
                'title': 'Update Contact Information',  # Action title
                'description': 'Verify and update your contact information including email and phone number.',  # Action description
                'instructions': 'Ensure your contact details are current so we can reach you if needed.',  # Action instructions
                'priority': 'low',  # Action priority
                'status': 'completed',  # Action status
                'completion_notes': 'Updated email address and added mobile phone number.',  # Completion notes
                'completed_at': timezone.now() - timedelta(days=2),  # Completed 2 days ago
            },
            {
                'title': 'Read Terms of Service',  # Action title
                'description': 'Please read and acknowledge our updated terms of service.',  # Action description
                'instructions': 'Review the terms of service document and confirm that you understand and agree to the terms.',  # Action instructions
                'priority': 'medium',  # Action priority
                'status': 'confirmed',  # Action status
                'completion_notes': 'Read and agreed to the terms of service.',  # Completion notes
                'completed_at': timezone.now() - timedelta(days=5),  # Completed 5 days ago
            },
            {
                'title': 'Setup Two-Factor Authentication',  # Action title
                'description': 'Enable two-factor authentication for enhanced account security.',  # Action description
                'instructions': 'Go to your security settings and follow the instructions to set up 2FA using an authenticator app.',  # Action instructions
                'priority': 'high',  # Action priority
                'status': 'pending',  # Action status
                'due_date': timezone.now() + timedelta(days=14),  # Due in 14 days
            },
            {
                'title': 'Complete Survey',  # Action title
                'description': 'Help us improve our service by completing a short customer satisfaction survey.',  # Action description
                'instructions': 'Click the survey link and answer a few questions about your experience with our service.',  # Action instructions
                'priority': 'low',  # Action priority
                'status': 'cancelled',  # Action status
                'admin_notes': 'Survey period has ended.',  # Admin notes
            },
        ]

        # Create actions
        created_count = 0  # Counter for created actions
        for action_data in sample_actions:  # Loop through sample actions
            # Check if action already exists (to avoid duplicates)
            if not Action.objects.filter(user=user, title=action_data['title']).exists():  # If action doesn't exist
                action = Action.objects.create(  # Create new action
                    user=user,  # Assign to user
                    title=action_data['title'],  # Set title
                    description=action_data['description'],  # Set description
                    instructions=action_data.get('instructions', ''),  # Set instructions (optional)
                    priority=action_data['priority'],  # Set priority
                    status=action_data['status'],  # Set status
                    due_date=action_data.get('due_date'),  # Set due date (optional)
                    completion_notes=action_data.get('completion_notes', ''),  # Set completion notes (optional)
                    completed_at=action_data.get('completed_at'),  # Set completed date (optional)
                    admin_notes=action_data.get('admin_notes', ''),  # Set admin notes (optional)
                )
                created_count += 1  # Increment counter
                self.stdout.write(f'Created action: {action.title}')  # Success message
            else:  # If action already exists
                self.stdout.write(f'Action already exists: {action_data["title"]}')  # Info message

        # Summary
        total_actions = Action.objects.filter(user=user).count()  # Get total actions for user
        self.stdout.write(  # Summary message
            self.style.SUCCESS(
                f'Successfully created {created_count} new actions. '
                f'Total actions for {user.email}: {total_actions}'
            )
        )

        # Show action statistics
        pending_count = Action.objects.filter(user=user, status='pending').count()  # Count pending actions
        in_progress_count = Action.objects.filter(user=user, status='in_progress').count()  # Count in-progress actions
        completed_count = Action.objects.filter(user=user, status='completed').count()  # Count completed actions
        confirmed_count = Action.objects.filter(user=user, status='confirmed').count()  # Count confirmed actions
        cancelled_count = Action.objects.filter(user=user, status='cancelled').count()  # Count cancelled actions

        self.stdout.write('\nAction Statistics:')  # Statistics header
        self.stdout.write(f'  Pending: {pending_count}')  # Pending count
        self.stdout.write(f'  In Progress: {in_progress_count}')  # In-progress count
        self.stdout.write(f'  Completed: {completed_count}')  # Completed count
        self.stdout.write(f'  Confirmed: {confirmed_count}')  # Confirmed count
        self.stdout.write(f'  Cancelled: {cancelled_count}')  # Cancelled count 