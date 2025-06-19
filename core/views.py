import os
import json
from django.shortcuts import render, redirect, get_object_or_404  # Import Django shortcuts for common operations
from django.contrib.auth import authenticate, login, logout  # Import authentication functions
from django.contrib.auth.decorators import login_required  # Import decorator to require login
from django.contrib.admin.views.decorators import staff_member_required  # Import decorator for admin access
from django.contrib import messages  # Import Django's message framework
from django.http import JsonResponse  # Import for JSON responses
from django.utils import timezone  # Import for timezone handling
from django.core.files.storage import FileSystemStorage  # Import for file handling
from django.db.models import Count, Q, Avg  # Import database query helpers
from .models import CustomUser, SupportTicket, ChatMessage, ProofOfPayment, Notification, AdminActivityLog, Action, AdminReport  # Import our models
from .forms import SupportTicketForm, ProofOfPaymentForm  # Import our forms
from django.core.paginator import Paginator  # Import for pagination
from datetime import timedelta  # Import for timedelta
from django.contrib.auth.decorators import user_passes_test  # Import for user_passes_test decorator
import math
from .safechain_knowledge import SAFECHAIN_KNOWLEDGE, SAFECHAIN_FAQ  # Import knowledge base
import traceback  # Import traceback for detailed error info

# Home view (following SafeCrypto pattern)
def home_view(request):
    """Display the home page with statistics"""
    context = {
        'total_users': CustomUser.objects.count(),  # Count total registered users
        'total_tickets': SupportTicket.objects.count(),  # Count total support tickets
        'resolved_tickets': SupportTicket.objects.filter(status='confirmed').count(),  # Count resolved tickets
        'pending_tickets': SupportTicket.objects.filter(status='pending').count(),  # Count pending tickets
    }
    return render(request, 'core/home.html', context)  # Render the home template with context

# Registration view (following SafeCrypto pattern)
def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':  # If form is submitted
        full_name = request.POST.get('full_name')  # Get full name from form
        email = request.POST.get('email')  # Get email from form
        phone = request.POST.get('phone')  # Get phone from form
        password = request.POST.get('password')  # Get password from form
        confirm_password = request.POST.get('confirm_password')  # Get password confirmation

        if password != confirm_password:  # Check if passwords match
            messages.error(request, 'Passwords do not match.')  # Show error message
            return redirect('register')  # Redirect back to registration
        
        if CustomUser.objects.filter(email=email).exists():  # Check if email already exists
            messages.error(request, 'Email already registered.')  # Show error message
            return redirect('register')  # Redirect back to registration
            
        try:
            # Split full name into first and last name
            first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')
            # Create new user
            user = CustomUser.objects.create_user(
                username=email,  # Use email as username
                email=email,  # Set email
                password=password,  # Set password (will be hashed)
                phone=phone,  # Set phone number
                first_name=first_name,  # Set first name
                last_name=last_name  # Set last name
            )
            
            login(request, user)  # Log the user in automatically
            messages.success(request, 'Registration successful! Welcome to Safe Chain Assistant.')  # Show success message
            return redirect('home')  # Redirect to chat (home page)
        except Exception as e:  # Handle any errors
            messages.error(request, 'An error occurred during registration. Please try again.')  # Show error message
            return redirect('register')  # Redirect back to registration
            
    return render(request, 'core/register.html')  # Render registration template

# Login view (following SafeCrypto pattern)
def login_view(request):
    """Handle user login"""
    if request.method == 'POST':  # If form is submitted
        email = request.POST.get('email')  # Get email from form
        password = request.POST.get('password')  # Get password from form
        user = authenticate(request, username=email, password=password)  # Authenticate user
        if user is not None:  # If authentication successful
            login(request, user)  # Log the user in
            return redirect('home')  # Redirect to chat (home page)
        else:  # If authentication failed
            messages.error(request, 'Invalid email or password.')  # Show error message
    return render(request, 'core/login.html')  # Render login template

# Dashboard view
@login_required  # Require user to be logged in
def dashboard_view(request):
    """Display user dashboard with enhanced ticket overview"""
    # Get user's ticket statistics
    open_tickets = SupportTicket.objects.filter(user=request.user, status__in=['pending', 'in_progress'])  # Get open tickets
    resolved_tickets = SupportTicket.objects.filter(user=request.user, status__in=['fixed', 'confirmed'])  # Get resolved tickets
    recent_tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')[:5]  # Get 5 most recent tickets
    
    # Get user's POP statistics
    user_pops = ProofOfPayment.objects.filter(user=request.user)  # Get user's POPs
    pending_pops = user_pops.filter(status='pending')  # Get pending POPs
    approved_pops = user_pops.filter(status='approved')  # Get approved POPs
    
    # Get user's action statistics
    pending_actions = Action.objects.filter(user=request.user, status='pending').order_by('-priority', '-created_at')[:5]  # Get 5 most recent pending actions
    total_actions = Action.objects.filter(user=request.user).count()  # Get total actions count
    overdue_actions = Action.objects.filter(user=request.user, status__in=['pending', 'in_progress']).filter(due_date__lt=timezone.now()).count()  # Get overdue actions count
    
    # Calculate average satisfaction
    rated_tickets = SupportTicket.objects.filter(user=request.user, user_satisfaction__isnull=False)  # Get rated tickets
    avg_satisfaction = rated_tickets.aggregate(avg_rating=Avg('user_satisfaction'))['avg_rating']  # Calculate average
    
    context = {
        'open_tickets': open_tickets,  # Pass open tickets
        'resolved_tickets': resolved_tickets,  # Pass resolved tickets
        'recent_tickets': recent_tickets,  # Pass recent tickets
        'total_open': open_tickets.count(),  # Count of open tickets
        'total_resolved': resolved_tickets.count(),  # Count of resolved tickets
        'pending_pops': pending_pops,  # Pass pending POPs
        'approved_pops': approved_pops,  # Pass approved POPs
        'total_pops': user_pops.count(),  # Count of total POPs
        'avg_satisfaction': round(avg_satisfaction, 1) if avg_satisfaction else None,  # Average satisfaction
        'total_rated': rated_tickets.count(),  # Count of rated tickets
        'pending_actions': pending_actions,  # Pass pending actions
        'total_actions': total_actions,  # Pass total actions count
        'overdue_actions': overdue_actions,  # Pass overdue actions count
    }
    return render(request, 'core/dashboard.html', context)  # Render dashboard template

# Chat view
@login_required  # Require user to be logged in
def chat_view(request):
    """Handle chat interface with AI assistant and intelligent workflow"""
    if request.method == 'POST':  # If form is submitted
        try:
            message = request.POST.get('message', '').strip()  # Get message from form
            ticket_id = request.POST.get('ticket_id')  # Get ticket ID if continuing conversation
            uploaded_files = request.FILES.getlist('files')  # Get uploaded files
            
            if not message:  # If no message provided
                return JsonResponse({
                    'success': False,  # Success flag
                    'response': "Please enter a message.",  # Error message
                    'suggestions': ['How can I help you?']  # Default suggestions
                })
            
            # Get or create ticket
            if ticket_id:  # If continuing existing conversation
                ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)  # Get existing ticket
            else:  # If starting new conversation
                # --- Onboarding/General Info Detection (Visual/Step-based) ---
                onboarding_triggers = [
                    'how does this work', 'how do i start', 'how to invest', 'how do i invest', 'investments', 'how can i start', 'how to begin', 'how do i use', 'how do i get started', 'how do i join', 'how to join', 'how to get started', 'how to start', 'how do i deposit', 'how do i sign up', 'how do i register', 'how to register', 'how to sign up', 'how to deposit', 'how to begin investing', 'how to use cryptovault', 'cryptovault', 'how cryptovault works', 'how does cryptovault work', 'how does safec...' 
                ]
                general_info_triggers = [
                    'how does it work', 'how does this app work', 'how do i use this', 'how do i use the app', 'how do i get help', 'what is this', 'what can i do', 'what does this do', 'what is safec...', 'what is cryptovault', 'tell me about', 'explain', 'help', 'info', 'information', 'guide', 'instructions', 'tutorial', 'walkthrough', 'steps', 'process', 'overview', 'introduction', 'start here', 'beginner', 'getting started'
                ]
                investment_plan_triggers = [
                    'how much can i start with', 'minimum investment', 'how much to invest', 'investment plans', 'show me the plans', 'show me the table', 'what are the plans', 'investment tiers', 'how much do i need', 'plan options', 'investment options', 'how much can i invest', 'how much do i need to start', 'what is the minimum', 'how much for each plan', 'plan table', 'investment table', 'plans', 'tiers', 'investment levels', 'investment choices', 'investment packages', 'plan list', 'all plans', 'all tiers', 'investment chart', 'plan chart', 'investment breakdown', 'plan breakdown', 'how much is each plan', 'how much is each tier', 'how much to get started', 'how much to begin', 'how much to join', 'how much to participate', 'how much to open account', 'how much to open an account', 'how much to create account', 'how much to create an account', 'how much to register', 'how much to sign up', 'how much to deposit', 'how much to fund', 'how much to fund account', 'how much to fund wallet', 'how much to fund my account', 'how much to fund my wallet'
                ]
                msg_lower = message.lower()
                # If the message matches onboarding or general info triggers, respond with visual onboarding
                if any(trigger in msg_lower for trigger in onboarding_triggers + general_info_triggers):
                    # Use the new visual onboarding key for a step-by-step, image-inspired answer
                    onboarding_text = SAFECHAIN_KNOWLEDGE.get('cryptovault_visual_onboarding', SAFECHAIN_KNOWLEDGE.get('cryptovault_how_it_works'))
                    # Do NOT save ChatMessage if no ticket exists
                    return JsonResponse({
                        'success': True,
                        'response': onboarding_text,
                        'ticket_id': None,
                        'suggestions': ['Sign up', 'Choose a plan', 'Make a deposit', 'Ask more questions']
                    })
                # If the message matches investment plan triggers, respond with investment tiers
                if any(trigger in msg_lower for trigger in investment_plan_triggers):
                    tiers_text = SAFECHAIN_KNOWLEDGE.get('cryptovault_investment_tiers')
                    return JsonResponse({
                        'success': True,
                        'response': tiers_text,
                        'ticket_id': None,
                        'suggestions': ['See plan details', 'Ask about returns', 'Ask about deposits']
                    })
                # --- End Onboarding/General Info Detection ---
                # Analyze user intent
                intent_analysis = analyze_user_intent(message)  # Analyze what user wants
                priority = determine_priority(intent_analysis)  # Determine priority
                title = generate_ticket_title(message, intent_analysis)  # Generate ticket title
                
                # Create new ticket
                ticket = SupportTicket.objects.create(
                    user=request.user,  # Set user
                    title=title,  # Set title
                    description=message,  # Set description
                    priority=priority,  # Set priority
                    intent_category=intent_analysis.get('category', 'general')  # Set intent category
                )  # Create new support ticket
            
            # Save user message
            ChatMessage.objects.create(
                ticket=ticket,  # Associate with ticket
                user=request.user,  # Set user
                message=message,  # Set message
                is_ai_response=False  # Mark as user message
            )  # Create chat message
            
            # Handle file uploads if any
            uploaded_pop_files = []
            document_upload_message = ""
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    # Create ProofOfPayment object
                    pop = ProofOfPayment.objects.create(
                        user=request.user,  # Set user
                        email=request.user.email,  # Set email
                        file=uploaded_file,  # Set file
                        file_name=uploaded_file.name,  # Set filename
                        file_size=uploaded_file.size,  # Set file size
                        ticket=ticket  # Associate with ticket
                    )  # Create proof of payment
                    uploaded_pop_files.append(pop)  # Add to list
                    
                    # Associate with ticket's collected documents
                    ticket.collected_documents.add(pop)  # Add to collected documents
                    
                    # Notify admins about new document
                    notify_admins_new_pop(pop)  # Send notification to admins
                    
                    # Create document upload message
                    document_upload_message += f"📎 **Document Uploaded:** {uploaded_file.name} ({format_file_size(uploaded_file.size)})\n"
                
                # Add document upload confirmation to context
                document_upload_message += "\n✅ **Document received!** Your file has been uploaded and sent to our admin team for review.\n\n"
                
                # Save document upload message
                ChatMessage.objects.create(
                    ticket=ticket,  # Associate with ticket
                    user=request.user,  # Set user
                    message=document_upload_message,  # Set upload message
                    is_ai_response=True  # Mark as AI response
                )  # Create chat message
            
            # Check if this is a new request that needs admin workflow analysis
            if not ticket.admin_report and not ticket_id:
                # First, try to understand and draft the problem
                problem_analysis = understand_and_draft_problem(message, ticket, uploaded_files)
                
                if problem_analysis['is_asking_questions']:
                    # AI needs more information - ask clarifying questions
                    ai_response = problem_analysis['response']
                    
                    # Save AI response
                    ChatMessage.objects.create(
                        ticket=ticket,
                        user=request.user,
                        message=ai_response,
                        is_ai_response=True
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'response': ai_response,
                        'ticket_id': ticket.id,
                        'suggestions': ['Provide more details', 'Upload documents', 'Ask questions'],
                        'needs_more_info': True
                    })
                
                elif problem_analysis['needs_confirmation']:
                    # AI has drafted a summary and needs user confirmation
                    ai_response = problem_analysis['response']
                    
                    # Save AI response
                    ChatMessage.objects.create(
                        ticket=ticket,
                        user=request.user,
                        message=ai_response,
                        is_ai_response=True
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'response': ai_response,
                        'ticket_id': ticket.id,
                        'suggestions': ['✅ Yes, send to admin', '❌ No, let me correct it'],
                        'needs_confirmation': True
                    })
                
                else:
                    # Fall back to original workflow analysis
                    workflow_data = analyze_admin_workflow(message, ticket, uploaded_files)
                    
                    if workflow_data:
                        # Generate document request message
                        ai_response = generate_document_request_message(workflow_data)
                        
                        # Save AI response
                        ChatMessage.objects.create(
                            ticket=ticket,
                            user=request.user,
                            message=ai_response,
                            is_ai_response=True
                        )
                        
                        return JsonResponse({
                            'success': True,
                            'response': ai_response,
                            'ticket_id': ticket.id,
                            'suggestions': ['Upload documents', 'Provide additional information', 'Ask questions'],
                            'workflow_detected': True,
                            'required_documents': workflow_data['required_documents'],
                            'admin_action': workflow_data['admin_action']
                        })
            
            # Check if user is confirming a problem summary
            elif ticket.status == 'pending' and not ticket.admin_report:
                # Check if this might be a confirmation response
                confirmation_result = confirm_problem_with_user(message, ticket)
                
                if confirmation_result.get('admin_report_created'):
                    # User confirmed - admin report was created
                    ai_response = confirmation_result['response']
                    
                    # Save AI response
                    ChatMessage.objects.create(
                        ticket=ticket,
                        user=request.user,
                        message=ai_response,
                        is_ai_response=True
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'response': ai_response,
                        'ticket_id': ticket.id,
                        'suggestions': ['Check ticket status', 'Ask questions', 'Upload more documents'],
                        'admin_report_created': True,
                        'report_id': confirmation_result.get('ticket_id')
                    })
                
                elif confirmation_result.get('needs_correction') or confirmation_result.get('needs_clarification'):
                    # User wants to correct or needs clarification
                    ai_response = confirmation_result['response']
                    
                    # Save AI response
                    ChatMessage.objects.create(
                        ticket=ticket,
                        user=request.user,
                        message=ai_response,
                        is_ai_response=True
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'response': ai_response,
                        'ticket_id': ticket.id,
                        'suggestions': ['Provide corrections', 'Upload documents', 'Ask questions'],
                        'needs_correction': confirmation_result.get('needs_correction', False),
                        'needs_clarification': confirmation_result.get('needs_clarification', False)
                    })
            
            # Check if documents have been completed
            if ticket.admin_report and uploaded_files:
                if check_document_completion(ticket):
                    # Generate admin report summary
                    summary = generate_admin_report_summary(ticket)
                    
                    # Save AI response
                    ChatMessage.objects.create(
                        ticket=ticket,  # Associate with ticket
                        user=request.user,  # Set user
                        message=summary,  # Set summary message
                        is_ai_response=True  # Mark as AI response
                    )  # Create chat message
                    
                    return JsonResponse({
                        'success': True,  # Success flag
                        'response': summary,  # Summary message
                        'ticket_id': ticket.id,  # Ticket ID
                        'suggestions': ['Check status', 'Ask questions', 'Upload more documents'],
                        'report_ready': True,  # Flag that report is ready
                        'report_id': ticket.admin_report.id  # Report ID
                    })
            
            # Get enhanced AI response
            ai_response_data = get_enhanced_ai_response(message, ticket, uploaded_files)  # Get AI response
            ai_response = ai_response_data.get('response', 'I apologize, but I\'m having trouble processing your request.')  # Get response text
            
            # If documents were uploaded, enhance the response
            if uploaded_files and document_upload_message:
                # Combine document upload message with AI response
                enhanced_response = document_upload_message + "\n" + ai_response
            else:
                enhanced_response = ai_response
            
            # Save AI response
            ChatMessage.objects.create(
                ticket=ticket,  # Associate with ticket
                user=request.user,  # Set user
                message=enhanced_response,  # Set enhanced AI response
                is_ai_response=True  # Mark as AI response
            )  # Create chat message
            
            # Update ticket if needed
            if not ticket.ai_summary:  # If no AI summary yet
                ticket.ai_summary = ai_response_data.get('summary', '')  # Set AI summary
                ticket.save()  # Save changes
            
            # Return JSON response for AJAX
            return JsonResponse({
                'success': True,  # Success flag
                'response': enhanced_response,  # Enhanced AI response text
                'ticket_id': ticket.id,  # Ticket ID for continuing conversation
                'suggestions': ai_response_data.get('suggestions', []),  # Response suggestions
                'documents_uploaded': len(uploaded_files) if uploaded_files else 0,  # Number of documents uploaded
                'admin_notified': True if uploaded_files else False  # Whether admin was notified
            })
        except Exception as e:  # Handle any errors
            print(f"Error in chat view: {str(e)}")  # Print error for debugging
            print(f"Full traceback: {traceback.format_exc()}")  # Print full traceback
            return JsonResponse({
                'success': False,  # Success flag
                'response': "I apologize, but I'm having trouble processing your request right now. Please try again later.",
                'ticket_id': ticket.id if 'ticket' in locals() else None,  # Ticket ID if available
                'suggestions': ['Try again', 'Contact support directly']  # Default suggestions
            })
    
    # GET request - show chat interface
    return render(request, 'core/chat_simple.html', {})  # Render simplified chat template

# Upload POP view (following SafeCrypto deposit pattern)
@login_required  # Require user to be logged in
def upload_pop_view(request):
    """Handle proof of payment uploads"""
    if request.method == 'POST':  # If form is submitted
        form = ProofOfPaymentForm(request.POST, request.FILES)  # Create form with data and files
        if form.is_valid():  # If form is valid
            pop = form.save(commit=False)  # Create POP object but don't save yet
            pop.user = request.user  # Set user
            pop.file_name = request.FILES['file'].name  # Get original filename
            pop.file_size = request.FILES['file'].size  # Get file size
            pop.save()  # Save the POP
            
            # Notify admins
            notify_admins_new_pop(pop)  # Send notification to admins
            
            messages.success(request, 'Proof of payment uploaded successfully!')  # Show success message
            return redirect('dashboard')  # Redirect to dashboard
    else:  # If GET request
        form = ProofOfPaymentForm()  # Create empty form
    
    context = {
        'form': form,  # Pass form to template
    }
    return render(request, 'core/upload_pop.html', context)  # Render upload template

# Tickets view
@login_required  # Require user to be logged in
def tickets_view(request):
    """Display and manage user's support tickets with enhanced feedback"""
    # Get user's tickets with different statuses
    open_tickets = SupportTicket.objects.filter(user=request.user, status__in=['pending', 'in_progress']).order_by('-created_at')  # Get open tickets
    resolved_tickets = SupportTicket.objects.filter(user=request.user, status__in=['fixed', 'confirmed']).order_by('-created_at')  # Get resolved tickets
    all_tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')  # Get all tickets
    
    if request.method == 'POST':  # If form is submitted
        ticket_id = request.POST.get('ticket_id')  # Get ticket ID
        action = request.POST.get('action')  # Get action (confirm/reject/rate)
        satisfaction_rating = request.POST.get('satisfaction_rating')  # Get satisfaction rating
        ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)  # Get ticket
        
        if action == 'confirm':  # If user confirms resolution
            ticket.status = 'confirmed'  # Update status
            ticket.save()  # Save changes
            messages.success(request, 'Issue confirmed as resolved! Thank you for your feedback.')  # Show success message
            
            # Log admin activity
            AdminActivityLog.objects.create(
                admin_user=ticket.assigned_to or request.user,  # Set admin user
                action='Ticket Confirmed',  # Set action description
                target_model='SupportTicket',  # Set target model
                target_id=ticket.id,  # Set target ID
                details=f'User confirmed resolution for ticket: {ticket.title}'  # Set details
            )
            
        elif action == 'reject':  # If user rejects resolution
            ticket.status = 'rejected'  # Update status
            ticket.save()  # Save changes
            messages.success(request, 'Issue marked as not resolved. We\'ll continue working on it.')  # Show success message
            
            # Log admin activity
            AdminActivityLog.objects.create(
                admin_user=ticket.assigned_to or request.user,  # Set admin user
                action='Ticket Rejected',  # Set action description
                target_model='SupportTicket',  # Set target model
                target_id=ticket.id,  # Set target ID
                details=f'User rejected resolution for ticket: {ticket.title}'  # Set details
            )
            
        elif action == 'rate' and satisfaction_rating:  # If user is rating satisfaction
            try:
                rating = int(satisfaction_rating)  # Convert to integer
                if 1 <= rating <= 5:  # If rating is valid
                    ticket.user_satisfaction = rating  # Set satisfaction rating
                    ticket.save()  # Save changes
                    messages.success(request, 'Thank you for your feedback!')  # Show success message
                else:  # If rating is invalid
                    messages.error(request, 'Please provide a rating between 1 and 5.')  # Show error message
            except ValueError:  # If rating is not a number
                messages.error(request, 'Please provide a valid rating.')  # Show error message
    
    context = {
        'open_tickets': open_tickets,  # Pass open tickets to template
        'resolved_tickets': resolved_tickets,  # Pass resolved tickets to template
        'all_tickets': all_tickets,  # Pass all tickets to template
        'total_open': open_tickets.count(),  # Count of open tickets
        'total_resolved': resolved_tickets.count(),  # Count of resolved tickets
    }
    return render(request, 'core/tickets.html', context)  # Render tickets template

# Admin dashboard (following SafeCrypto admin pattern)
@staff_member_required  # Require staff/admin access
def admin_dashboard_view(request):
    """Display admin dashboard with comprehensive system statistics"""
    # Get comprehensive statistics
    total_users = CustomUser.objects.count()  # Count all users
    total_tickets = SupportTicket.objects.count()  # Count all tickets
    pending_tickets = SupportTicket.objects.filter(status='pending').count()  # Count pending tickets
    resolved_tickets = SupportTicket.objects.filter(status__in=['fixed', 'confirmed']).count()  # Count resolved tickets
    total_pops = ProofOfPayment.objects.count()  # Count all POPs
    pending_pops = ProofOfPayment.objects.filter(status='pending').count()  # Count pending POPs
    approved_pops = ProofOfPayment.objects.filter(status='approved').count()  # Count approved POPs
    
    # Get recent activities
    recent_activities = AdminActivityLog.objects.all().order_by('-timestamp')[:10]  # Get 10 most recent admin activities
    
    # Get recent tickets
    recent_tickets = SupportTicket.objects.all().order_by('-created_at')[:5]  # Get 5 most recent tickets
    
    # Get recent POPs
    recent_pops = ProofOfPayment.objects.all().order_by('-created_at')[:5]  # Get 5 most recent POPs
    
    # Get user statistics
    new_users_today = CustomUser.objects.filter(date_joined__date=timezone.now().date()).count()  # Count new users today
    new_users_week = CustomUser.objects.filter(date_joined__gte=timezone.now() - timezone.timedelta(days=7)).count()  # Count new users this week
    
    # Get ticket statistics by status
    ticket_status_stats = SupportTicket.objects.values('status').annotate(count=Count('id'))  # Get ticket counts by status
    
    context = {
        'total_users': total_users,  # Total users count
        'total_tickets': total_tickets,  # Total tickets count
        'pending_tickets': pending_tickets,  # Pending tickets count
        'resolved_tickets': resolved_tickets,  # Resolved tickets count
        'total_pops': total_pops,  # Total POPs count
        'pending_pops': pending_pops,  # Pending POPs count
        'approved_pops': approved_pops,  # Approved POPs count
        'recent_activities': recent_activities,  # Recent activities list
        'recent_tickets': recent_tickets,  # Recent tickets list
        'recent_pops': recent_pops,  # Recent POPs list
        'new_users_today': new_users_today,  # New users today
        'new_users_week': new_users_week,  # New users this week
        'ticket_status_stats': ticket_status_stats,  # Ticket status statistics
    }
    return render(request, 'core/admin_dashboard.html', context)  # Render admin dashboard template

# Admin users view
@staff_member_required  # Require staff/admin access
def admin_users_view(request):
    """Manage users and their accounts"""
    users = CustomUser.objects.all().order_by('-date_joined')  # Get all users
    
    if request.method == 'POST':  # If form is submitted
        user_id = request.POST.get('user_id')  # Get user ID
        action = request.POST.get('action')  # Get action (activate/deactivate/make_admin)
        
        user = get_object_or_404(CustomUser, id=user_id)  # Get user
        
        if action == 'activate':  # If activating user
            user.is_active = True  # Set user as active
            user.save()  # Save changes
            messages.success(request, f'User {user.email} activated successfully!')  # Show success message
        elif action == 'deactivate':  # If deactivating user
            user.is_active = False  # Set user as inactive
            user.save()  # Save changes
            messages.success(request, f'User {user.email} deactivated successfully!')  # Show success message
        elif action == 'make_admin':  # If making user admin
            user.is_admin = True  # Set user as admin
            user.save()  # Save changes
            messages.success(request, f'User {user.email} is now an admin!')  # Show success message
        elif action == 'remove_admin':  # If removing admin status
            user.is_admin = False  # Remove admin status
            user.save()  # Save changes
            messages.success(request, f'Admin status removed from {user.email}!')  # Show success message
        
        # Log admin activity
        AdminActivityLog.objects.create(
            admin_user=request.user,  # Set admin user
            action=f'User {action.title()}',  # Set action description
            target_model='CustomUser',  # Set target model
            target_id=user.id,  # Set target ID
            details=f'User {action} for {user.email}'  # Set details
        )
    
    context = {
        'users': users,  # Pass users to template
    }
    return render(request, 'core/admin_users.html', context)  # Render admin users template

# Admin POPs view
@staff_member_required  # Require staff/admin access
def admin_pops_view(request):
    """Manage proof of payment uploads with enhanced functionality"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')  # Get status filter
    date_filter = request.GET.get('date', '')  # Get date filter
    
    pops = ProofOfPayment.objects.all()  # Start with all POPs
    
    # Apply filters
    if status_filter:  # If status filter is applied
        pops = pops.filter(status=status_filter)  # Filter by status
    
    if date_filter:  # If date filter is applied
        if date_filter == 'today':  # If filtering for today
            pops = pops.filter(created_at__date=timezone.now().date())  # Filter for today
        elif date_filter == 'week':  # If filtering for this week
            pops = pops.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))  # Filter for this week
        elif date_filter == 'month':  # If filtering for this month
            pops = pops.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))  # Filter for this month
    
    pops = pops.order_by('-created_at')  # Order by creation date (newest first)
    
    if request.method == 'POST':  # If form is submitted
        pop_id = request.POST.get('pop_id')  # Get POP ID
        action = request.POST.get('action')  # Get action (approve/reject)
        admin_notes = request.POST.get('admin_notes', '')  # Get admin notes
        
        pop = get_object_or_404(ProofOfPayment, id=pop_id)  # Get POP
        
        if action == 'approve':  # If approving
            pop.status = 'approved'  # Update status
        elif action == 'reject':  # If rejecting
            pop.status = 'rejected'  # Update status
        
        pop.admin_notes = admin_notes  # Set admin notes
        pop.save()  # Save changes
        
        # Log admin activity
        AdminActivityLog.objects.create(
            admin_user=request.user,  # Set admin user
            action=f'POP {action.title()}',  # Set action description
            target_model='ProofOfPayment',  # Set target model
            target_id=pop.id,  # Set target ID
            details=f'POP {action} for {pop.user.email}'  # Set details
        )
        
        messages.success(request, f'POP {action} successfully!')  # Show success message
    
    context = {
        'pops': pops,  # Pass POPs to template
        'status_filter': status_filter,  # Pass status filter
        'date_filter': date_filter,  # Pass date filter
    }
    return render(request, 'core/admin_pops.html', context)  # Render admin POPs template

# Admin tickets view
@staff_member_required  # Require staff/admin access
def admin_tickets_view(request):
    """Manage support tickets with enhanced functionality"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')  # Get status filter
    priority_filter = request.GET.get('priority', '')  # Get priority filter
    date_filter = request.GET.get('date', '')  # Get date filter
    
    tickets = SupportTicket.objects.all()  # Start with all tickets
    
    # Apply filters
    if status_filter:  # If status filter is applied
        tickets = tickets.filter(status=status_filter)  # Filter by status
    
    if priority_filter:  # If priority filter is applied
        tickets = tickets.filter(priority=priority_filter)  # Filter by priority
    
    if date_filter:  # If date filter is applied
        if date_filter == 'today':  # If filtering for today
            tickets = tickets.filter(created_at__date=timezone.now().date())  # Filter for today
        elif date_filter == 'week':  # If filtering for this week
            tickets = tickets.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))  # Filter for this week
        elif date_filter == 'month':  # If filtering for this month
            tickets = tickets.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))  # Filter for this month
    
    tickets = tickets.order_by('-created_at')  # Order by creation date (newest first)
    
    if request.method == 'POST':  # If form is submitted
        ticket_id = request.POST.get('ticket_id')  # Get ticket ID
        status = request.POST.get('status')  # Get new status
        priority = request.POST.get('priority')  # Get new priority
        admin_notes = request.POST.get('admin_notes', '')  # Get admin notes
        
        ticket = get_object_or_404(SupportTicket, id=ticket_id)  # Get ticket
        ticket.status = status  # Update status
        ticket.priority = priority  # Update priority
        ticket.admin_notes = admin_notes  # Set admin notes
        ticket.assigned_to = request.user  # Assign to current admin
        ticket.save()  # Save changes
        
        # Log admin activity
        AdminActivityLog.objects.create(
            admin_user=request.user,  # Set admin user
            action=f'Ticket Update',  # Set action description
            target_model='SupportTicket',  # Set target model
            target_id=ticket.id,  # Set target ID
            details=f'Ticket status: {status}, priority: {priority}'  # Set details
        )
        
        messages.success(request, 'Ticket updated successfully!')  # Show success message
    
    context = {
        'tickets': tickets,  # Pass tickets to template
        'status_filter': status_filter,  # Pass status filter
        'priority_filter': priority_filter,  # Pass priority filter
        'date_filter': date_filter,  # Pass date filter
    }
    return render(request, 'core/admin_tickets.html', context)  # Render admin tickets template

# Enhanced AI helper functions
def analyze_user_intent(message):
    """Analyze user message to determine intent and requirements"""
    try:
        # Import configuration and OpenAI client
        from ai_support.settings import OPENAI_API_KEY
        from openai import OpenAI
        
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Call OpenAI API for intent analysis
        response = client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better analysis
            messages=[
                {"role": "system", "content": """You are an AI assistant that analyzes customer support messages. 
                Analyze the user's message and return a JSON response with:
                - category: billing, technical, account, general, complaint, or feature_request
                - requires_pop: true if payment-related, false otherwise
                - priority: low, medium, high, or urgent
                - summary: brief summary of the issue
                - emotion: frustrated, calm, urgent, or neutral
                - keywords: list of important keywords from the message"""},
                {"role": "user", "content": message}
            ],
            max_tokens=300  # Limit response length
        )
        
        # Parse the response
        analysis_text = response.choices[0].message.content  # Get response text
        analysis = json.loads(analysis_text)  # Parse JSON response
        
        return analysis  # Return analysis
    except Exception as e:  # Handle any errors
        print(f"Error in analyze_user_intent: {str(e)}")  # Print error for debugging
        # Return default analysis
        return {
            'category': 'general',  # Default category
            'requires_pop': False,  # Default POP requirement
            'priority': 'medium',  # Default priority
            'summary': 'User inquiry',  # Default summary
            'emotion': 'neutral',  # Default emotion
            'keywords': []  # Default keywords
        }

def determine_priority(intent_analysis):
    """Determine ticket priority based on intent analysis"""
    emotion = intent_analysis.get('emotion', 'neutral')  # Get emotion
    category = intent_analysis.get('category', 'general')  # Get category
    
    # High priority for urgent emotions or billing issues
    if emotion == 'urgent' or category == 'billing':  # If urgent or billing
        return 'high'  # Set high priority
    elif emotion == 'frustrated' or category == 'complaint':  # If frustrated or complaint
        return 'medium'  # Set medium priority
    else:  # For other cases
        return 'low'  # Set low priority

def generate_ticket_title(message, intent_analysis):
    """Generate a smart ticket title based on user message and intent"""
    category = intent_analysis.get('category', 'general')  # Get category
    keywords = intent_analysis.get('keywords', [])  # Get keywords
    
    # Create title based on category
    if category == 'billing':  # If billing issue
        return f"Payment Issue - {keywords[0] if keywords else 'Inquiry'}"  # Payment-related title
    elif category == 'technical':  # If technical issue
        return f"Technical Support - {keywords[0] if keywords else 'Problem'}"  # Technical title
    elif category == 'complaint':  # If complaint
        return f"Customer Complaint - {keywords[0] if keywords else 'Issue'}"  # Complaint title
    else:  # For other categories
        return f"{category.title()} Inquiry - {timezone.now().strftime('%Y-%m-%d %H:%M')}"  # General title

def get_enhanced_ai_response(message, ticket, uploaded_files=None):
    """Get enhanced AI response with intent detection and calm responses"""
    try:
        # Import configuration and knowledge base
        from ai_support.settings import OPENAI_API_KEY
        from openai import OpenAI  # Import OpenAI client
        from .safechain_knowledge import SAFECHAIN_KNOWLEDGE, SAFECHAIN_FAQ, SAFECHAIN_SUPPORT_CATEGORIES  # Import knowledge base
        
        # Create a completely isolated environment for OpenAI client
        import os
        import copy
        
        # Save original environment
        original_env = copy.deepcopy(os.environ)
        
        # Clear all proxy-related environment variables
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']
        for var in proxy_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Also clear any other potential interfering variables
        interfering_vars = ['REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE', 'SSL_CERT_FILE']
        for var in interfering_vars:
            if var in os.environ:
                del os.environ[var]
        
        try:
            # Create OpenAI client in clean environment
            client = OpenAI(api_key=OPENAI_API_KEY)
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
        
        # Build context from ticket history
        context = f"User has a {ticket.intent_category} ticket: {ticket.title}. "  # Add ticket info
        context += f"Priority: {ticket.priority}. "  # Add priority info
        context += f"Requires POP: {ticket.requires_pop}. "  # Add POP requirement
        
        # Add file upload context if files were uploaded
        if uploaded_files:  # If files were uploaded
            file_names = [f.name for f in uploaded_files]  # Get file names from file objects
            context += f"User uploaded files: {', '.join(file_names)}. "  # Add file info
            context += "These appear to be proof of payment documents. "  # Add file context
        
        # Add recent chat history
        recent_messages = ChatMessage.objects.filter(ticket=ticket).order_by('-created_at')[:5]  # Get 5 most recent messages
        chat_history = ""  # Initialize chat history string
        for msg in reversed(recent_messages):  # Loop through messages (oldest first)
            role = "assistant" if msg.is_ai_response else "user"  # Determine message role
            chat_history += f"{role}: {msg.message}\n"  # Add message to history
        
        # Create comprehensive system prompt with SafeChain AI knowledge
        investment_tiers_text = "\n".join([f"- {tier['name']}: {tier['investment']} investment, {tier['duration']} duration, {tier['return']} return - {tier['description']}" for tier in SAFECHAIN_KNOWLEDGE['investment_tiers']])
        how_it_works_text = "\n".join([f"- {step['icon']} {step['step']}: {step['description']}" for step in SAFECHAIN_KNOWLEDGE['how_it_works']])
        support_categories_text = "\n".join([f"- {category}: {description}" for category, description in SAFECHAIN_SUPPORT_CATEGORIES.items()])
        faq_text = "\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in SAFECHAIN_FAQ.values()])
        
        # Add investment rules text
        investment_rules_text = "\n".join([f"- {rule}: {description}" for rule, description in SAFECHAIN_KNOWLEDGE['investment_rules'].items()])
        
        system_prompt = f"""You are a professional, empathetic customer support assistant for SafeChain AI, an AI-powered crypto investment platform.

COMPANY INFORMATION:
- Company: {SAFECHAIN_KNOWLEDGE['company_info']['name']}
- Tagline: {SAFECHAIN_KNOWLEDGE['company_info']['tagline']}
- Description: {SAFECHAIN_KNOWLEDGE['company_info']['description']}
- Website: {SAFECHAIN_KNOWLEDGE['company_info']['website']}
- Contact: {SAFECHAIN_KNOWLEDGE['company_info']['email']}
- Status: {SAFECHAIN_KNOWLEDGE['company_info']['status']}

PLATFORM STATISTICS:
- {SAFECHAIN_KNOWLEDGE['statistics']['investors_joined']} Investors Joined
- {SAFECHAIN_KNOWLEDGE['statistics']['total_payouts']} Total Payouts
- {SAFECHAIN_KNOWLEDGE['statistics']['ai_strategies']} AI Strategies Running

INVESTMENT TIERS:
{investment_tiers_text}

IMPORTANT INVESTMENT RULES:
{investment_rules_text}

INVESTMENT CALCULATOR:
- Users can calculate expected returns by entering investment amount and selecting a tier
- Calculator shows expected returns, duration, and return date
- Example: R500 investment in Big Jumbo tier = R100 return in 1 day

REFERRAL PROGRAM:
- {SAFECHAIN_KNOWLEDGE['referral_program']['description']}
- Referral Link: {SAFECHAIN_KNOWLEDGE['referral_program']['referral_link']}

HOW IT WORKS:
{how_it_works_text}

FEATURES:
- {', '.join(SAFECHAIN_KNOWLEDGE['features'])}

SUPPORT CATEGORIES:
{support_categories_text}

COMMON QUESTIONS & ANSWERS:
{faq_text}

Your role is to:
1. Stay calm and professional, especially with frustrated users
2. Provide accurate information about SafeChain AI services
3. Help users understand investment tiers, returns, and duration
4. Assist with referral program questions
5. Guide users to the correct registration link
6. Acknowledge when users upload proof of payment (POP) files
7. Ask for proof of payment (POP) if the issue is payment-related and no files were uploaded
8. Suggest relevant next steps based on SafeChain AI processes
9. Reassure users that their issue is being taken seriously
10. Provide clear information about minimum investments (R50) and expected returns
11. Help users understand the investment calculator and calculate potential returns
12. Explain investment amounts required for each tier
13. IMPORTANT: Always inform users they CANNOT reinvest in the same tier - they must keep growing to higher tiers
14. Explain the tier progression system when users ask about reinvestment
15. Clarify that users can invest ANY amount they want, as long as they don't reinvest in the same tier
16. Explain that tier amounts shown are examples - users are free to invest any amount in higher tiers

**SPECIAL HANDLING FOR WITHDRAWAL REQUESTS:**
If a user mentions withdrawal issues, problems, or requests, immediately ask for:
- Proof of Payment (POP) from their original investment
- Email address associated with their account

**WITHDRAWAL PROCESS:**
1. User must provide proof of their original payment
2. User must provide their email address
3. Admin team will verify and process the withdrawal
4. Processing time is typically 24-48 hours after verification

If the user seems frustrated, acknowledge their feelings and assure them you're here to help.
If payment-related and no POP was uploaded, ask for POP and email for verification.
If files were uploaded, acknowledge them and explain next steps.
Always provide clear next steps and set expectations.
Use the SafeChain AI knowledge to provide accurate, helpful responses."""
        
        # Build user message with file context
        user_message = message  # Start with original message
        if uploaded_files:  # If files were uploaded
            user_message += f"\n\n[User uploaded {len(uploaded_files)} file(s): "  # Add file info
            file_info = []  # Initialize file info list
            for file in uploaded_files:  # Loop through files
                file_info.append(f"{file.name} ({format_file_size(file.size)})")  # Add file info from file objects
            user_message += ", ".join(file_info) + "]"  # Add file list
        
        # Call OpenAI API using new client syntax
        response = client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better responses
            messages=[
                {"role": "system", "content": system_prompt},  # System prompt with SafeChain knowledge
                {"role": "user", "content": f"{context}\n\nChat history:\n{chat_history}\n\nUser: {user_message}"}  # User message with context
            ],
            max_tokens=800  # Increased token limit for more detailed responses
        )
        
        ai_response = response.choices[0].message.content  # Get AI response
        
        # Generate response suggestions
        suggestions = generate_response_suggestions(ticket, message, uploaded_files)  # Generate suggestions
        
        # Determine if ticket needs updating
        update_ticket = False  # Default to no update
        intent_category = ticket.intent_category  # Default intent
        priority = ticket.priority  # Default priority
        requires_pop = ticket.requires_pop  # Default POP requirement
        
        # Update if payment-related keywords detected or files uploaded
        payment_keywords = ['payment', 'billing', 'charge', 'refund', 'money', 'transaction', 'deposit', 'withdrawal', 'investment']  # Payment keywords
        if any(keyword in message.lower() for keyword in payment_keywords) or uploaded_files:  # If payment keywords found or files uploaded
            requires_pop = True  # Set POP requirement
            update_ticket = True  # Mark for update
        
        return {
            'response': ai_response,  # AI response text
            'suggestions': suggestions,  # Response suggestions
            'update_ticket': update_ticket,  # Whether to update ticket
            'intent_category': intent_category,  # Intent category
            'priority': priority,  # Priority level
            'requires_pop': requires_pop,  # POP requirement
        }
    except Exception as e:  # Handle any errors
        print(f"OpenAI API Error: {str(e)}")  # Print error for debugging
        return {
            'response': "I apologize, but I'm having trouble processing your request right now. Please try again later.",
            'suggestions': ['Try again', 'Contact support directly'],
            'update_ticket': False,
            'intent_category': ticket.intent_category,
            'priority': ticket.priority,
            'requires_pop': ticket.requires_pop,
        }

def format_file_size(bytes):
    """Format file size in human readable format"""
    if bytes == 0:  # If 0 bytes
        return '0 Bytes'  # Return 0 Bytes
    k = 1024  # Kilobyte constant
    sizes = ['Bytes', 'KB', 'MB', 'GB']  # Size units
    i = int(math.log(bytes) / math.log(k))  # Calculate unit index
    return f"{bytes / k**i:.1f} {sizes[i]}"  # Return formatted size

def generate_response_suggestions(ticket, message, uploaded_files=None):
    """Generate helpful response suggestions based on ticket context and SafeChain AI knowledge"""
    suggestions = []  # Initialize suggestions list
    
    # Add suggestions based on ticket category
    if ticket.intent_category == 'billing':  # If billing issue
        if uploaded_files:  # If files were uploaded
            suggestions.extend([
                'Thank you for uploading the proof of payment',
                'I can see your payment documents',
                'Your payment verification is being processed'
            ])
        else:  # If no files uploaded
            suggestions.extend([
                'Upload proof of payment',
                'Provide transaction details',
                'Check payment status'
            ])
    elif ticket.intent_category == 'technical':  # If technical issue
        suggestions.extend([
            'Try refreshing the page',
            'Clear browser cache',
            'Check internet connection'
        ])
    elif ticket.intent_category == 'complaint':  # If complaint
        suggestions.extend([
            'I understand your frustration',
            'Let me help resolve this',
            'Your feedback is important to us'
        ])
    
    # Add SafeChain AI-specific suggestions based on message content
    message_lower = message.lower()  # Convert to lowercase for easier matching
    
    # Withdrawal-specific suggestions
    if any(word in message_lower for word in ['withdrawal', 'withdraw', 'payout', 'get money', 'cash out', 'return']):
        suggestions.extend([
            'Upload proof of payment',
            'Provide your email address',
            'Processing time is 24-48 hours after verification'
        ])
    
    # Investment-related suggestions
    if any(word in message_lower for word in ['investment', 'tier', 'return', 'duration']):
        suggestions.extend([
            f'Minimum investment starts at {SAFECHAIN_KNOWLEDGE["support_info"]["minimum_investment"]}',
            'You can invest any amount you want, as long as you don\'t reinvest in the same tier',
            'Tier amounts shown are examples - you\'re free to invest any amount in higher tiers',
            'Returns vary by tier from R100 to R10,000',
            'Use the investment calculator to see your potential returns'
        ])
    
    # Reinvestment-specific suggestions
    if any(word in message_lower for word in ['reinvest', 'same tier', 'again', 'repeat', 'another']):
        suggestions.extend([
            'You cannot reinvest in the same tier - must progress to higher tiers',
            'Tier progression: Big Jumbo → Big Fish → Silver → Momentum → Booster Pack → Tier Breaker → Power Ladder → 10K Sprint',
            'Each new investment must be in a higher tier than your current active investment',
            'This ensures continuous growth and prevents staying in the same tier'
        ])
    
    # Referral program suggestions
    if any(word in message_lower for word in ['referral', 'refer', 'earn', 'bonus']):
        suggestions.extend([
            SAFECHAIN_KNOWLEDGE['referral_program']['description'],
            f'Use referral link: {SAFECHAIN_KNOWLEDGE["referral_program"]["referral_link"]}',
            'Top referrers earn R25,000+'
        ])
    
    # Registration suggestions
    if any(word in message_lower for word in ['register', 'sign up', 'join', 'account']):
        suggestions.extend([
            f'Register at {SAFECHAIN_KNOWLEDGE["company_info"]["website"]}',
            'Use referral link for bonus',
            'Quick and easy registration process'
        ])
    
    # AI trading suggestions
    if any(word in message_lower for word in ['ai', 'trading', 'automated', 'crypto']):
        suggestions.extend([
            'AI analyzes market data for low-risk tokens',
            'Trades are executed automatically',
            'Advanced encryption secures all transactions'
        ])
    
    # Security suggestions
    if any(word in message_lower for word in ['secure', 'safe', 'protection', 'risk']):
        suggestions.extend([
            'All trades secured with advanced encryption',
            'Low-risk crypto token selection',
            'Automated trading reduces human error'
        ])
    
    # File-specific suggestions
    if uploaded_files:  # If files were uploaded
        suggestions.extend([
            'Files received successfully',
            'Processing your documents',
            'We\'ll review and get back to you'
        ])
    
    # Add general SafeChain AI suggestions
    suggestions.extend([
        f'Join {SAFECHAIN_KNOWLEDGE["statistics"]["investors_joined"]} other investors',
        f'Platform has paid out {SAFECHAIN_KNOWLEDGE["statistics"]["total_payouts"]}',
        f'{SAFECHAIN_KNOWLEDGE["statistics"]["ai_strategies"]} AI strategies running'
    ])
    
    # Add general suggestions
    suggestions.extend([
        'Stay calm, we\'re here to help',
        'Your issue is being processed',
        'We\'ll get back to you soon'
    ])
    
    return suggestions[:6]  # Return top 6 suggestions

def generate_admin_suggestions(ticket):
    """Generate AI suggestions for admin actions"""
    suggestions = []  # Initialize suggestions list
    
    # Add suggestions based on ticket status and category
    if ticket.status == 'pending':  # If ticket is pending
        if ticket.intent_category == 'billing':  # If billing issue
            suggestions.extend([
                'Review uploaded POP documents',
                'Verify payment details',
                'Check transaction records'
            ])
        elif ticket.intent_category == 'technical':  # If technical issue
            suggestions.extend([
                'Request system logs',
                'Check user environment',
                'Test issue reproduction'
            ])
        else:  # General suggestions
            suggestions.extend([
                'Gather more information',
                'Assign to appropriate team',
                'Set priority level'
            ])
    elif ticket.status == 'in_progress':  # If ticket is in progress
        suggestions.extend([
            'Update user on progress',
            'Request additional details',
            'Escalate if needed'
        ])
    
    # Add resolution suggestions
    suggestions.extend([
        'Mark as resolved when complete',
        'Ask user for confirmation',
        'Follow up after resolution'
    ])
    
    return suggestions[:4]  # Return top 4 suggestions

# Keep the old function for backward compatibility
def get_ai_response(message, ticket):
    """Legacy AI response function for backward compatibility"""
    enhanced_response = get_enhanced_ai_response(message, ticket)  # Get enhanced response
    return enhanced_response['response']  # Return just the response text

def notify_admins_new_pop(pop):
    """Notify admins when new POP is uploaded with detailed information"""
    admins = CustomUser.objects.filter(is_admin=True)  # Get all admin users
    for admin in admins:  # Loop through admins
        # Create detailed notification message
        notification_message = f"""
📎 **New Document Uploaded**

**User:** {pop.user.email}
**File:** {pop.file_name}
**Size:** {format_file_size(pop.file_size)}
**Uploaded:** {pop.created_at.strftime('%Y-%m-%d %H:%M')}

**Ticket:** {pop.ticket.title if pop.ticket else 'No ticket associated'}
**Category:** {pop.ticket.intent_category if pop.ticket else 'N/A'}
**Priority:** {pop.ticket.priority if pop.ticket else 'N/A'}

**Action Required:** Review document and process user request.
        """.strip()
        
        Notification.objects.create(
            user=admin,  # Set admin as recipient
            title="📎 New Document Uploaded - Action Required",  # Set notification title
            message=notification_message  # Set detailed notification message
        )

@login_required  # Require user to be logged in
def logout_view(request):
    """Handle user logout"""
    logout(request)  # Log the user out
    messages.success(request, 'You have been logged out successfully.')  # Show success message
    return redirect('home')  # Redirect to home page

# Profile view (following SafeCrypto pattern)
@login_required  # Require user to be logged in
def profile_view(request):
    """Display and handle user profile management"""
    user = request.user  # Get current user
    
    if request.method == 'POST':  # If form is submitted
        # Get form data
        first_name = request.POST.get('first_name')  # Get first name
        last_name = request.POST.get('last_name')  # Get last name
        phone = request.POST.get('phone')  # Get phone number
        current_password = request.POST.get('current_password')  # Get current password
        new_password = request.POST.get('new_password')  # Get new password
        confirm_password = request.POST.get('confirm_password')  # Get password confirmation
        
        # Update basic info
        user.first_name = first_name  # Update first name
        user.last_name = last_name  # Update last name
        user.phone = phone  # Update phone number
        
        # Handle password change if provided
        if current_password and new_password and confirm_password:  # If password change is requested
            if not user.check_password(current_password):  # Check if current password is correct
                messages.error(request, 'Current password is incorrect.')  # Show error message
                return redirect('profile')  # Redirect back to profile
            
            if new_password != confirm_password:  # Check if new passwords match
                messages.error(request, 'New passwords do not match.')  # Show error message
                return redirect('profile')  # Redirect back to profile
            
            user.set_password(new_password)  # Set new password (will be hashed)
            messages.success(request, 'Password updated successfully!')  # Show success message
        
        user.save()  # Save user changes
        messages.success(request, 'Profile updated successfully!')  # Show success message
        return redirect('profile')  # Redirect back to profile
    
    context = {
        'user': user,  # Pass user to template
    }
    return render(request, 'core/profile.html', context)  # Render profile template

# Ticket confirmation view
@login_required  # Require user to be logged in
def ticket_confirmation_view(request, ticket_id):
    """Handle ticket confirmation and satisfaction feedback"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)  # Get ticket
    
    if request.method == 'POST':  # If form is submitted
        action = request.POST.get('action')  # Get action (confirm/reject)
        satisfaction_rating = request.POST.get('satisfaction_rating')  # Get satisfaction rating
        feedback_comment = request.POST.get('feedback_comment', '')  # Get feedback comment
        
        if action == 'confirm':  # If user confirms resolution
            ticket.status = 'confirmed'  # Update status
            if satisfaction_rating:  # If rating provided
                try:
                    rating = int(satisfaction_rating)  # Convert to integer
                    if 1 <= rating <= 5:  # If rating is valid
                        ticket.user_satisfaction = rating  # Set satisfaction rating
                except ValueError:  # If rating is not a number
                    pass  # Ignore invalid rating
            
            ticket.save()  # Save changes
            
            # Create notification for admin
            if ticket.assigned_to:  # If ticket is assigned
                Notification.objects.create(
                    user=ticket.assigned_to,  # Set admin as recipient
                    title="Ticket Resolved",  # Set notification title
                    message=f"User confirmed resolution for ticket: {ticket.title}"  # Set notification message
                )
            
            messages.success(request, 'Thank you for confirming! Your issue has been marked as resolved.')  # Show success message
            return redirect('tickets')  # Redirect to tickets page
            
        elif action == 'reject':  # If user rejects resolution
            ticket.status = 'rejected'  # Update status
            ticket.admin_notes += f"\n\nUser Feedback: {feedback_comment}"  # Add user feedback
            ticket.save()  # Save changes
            
            # Create notification for admin
            if ticket.assigned_to:  # If ticket is assigned
                Notification.objects.create(
                    user=ticket.assigned_to,  # Set admin as recipient
                    title="Ticket Reopened",  # Set notification title
                    message=f"User rejected resolution for ticket: {ticket.title}. Feedback: {feedback_comment}"  # Set notification message
                )
            
            messages.success(request, 'We understand the issue isn\'t resolved yet. We\'ll continue working on it.')  # Show success message
            return redirect('tickets')  # Redirect to tickets page
    
    context = {
        'ticket': ticket,  # Pass ticket to template
    }
    return render(request, 'core/ticket_confirmation.html', context)  # Render confirmation template

# Admin Dashboard Views
@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_dashboard(request):
    """Admin dashboard with overview of all tickets and statistics"""
    # Get statistics
    total_tickets = SupportTicket.objects.count()
    new_tickets = SupportTicket.objects.filter(status='pending').count()
    active_tickets = SupportTicket.objects.filter(status='in_progress').count()
    resolved_tickets = SupportTicket.objects.filter(status='fixed').count()
    confirmed_tickets = SupportTicket.objects.filter(status='confirmed').count()
    
    # Get document statistics
    total_documents = ProofOfPayment.objects.count()
    recent_documents = ProofOfPayment.objects.select_related('user', 'ticket').order_by('-created_at')[:5]
    pending_documents = ProofOfPayment.objects.filter(status='pending').count()
    
    # Get admin report statistics by management area
    admin_reports = AdminReport.objects.all()
    reports_by_area = {}
    for area_code, area_name in AdminReport.ADMIN_MANAGEMENT_AREAS:
        reports_by_area[area_name] = {
            'total': admin_reports.filter(admin_management_area=area_code).count(),
            'pending': admin_reports.filter(admin_management_area=area_code, status='pending').count(),
            'urgent': admin_reports.filter(admin_management_area=area_code, priority='urgent').count(),
            'recent': admin_reports.filter(admin_management_area=area_code).order_by('-created_at')[:3]
        }
    
    # Get recent tickets
    recent_tickets = SupportTicket.objects.select_related('user').order_by('-created_at')[:10]
    
    # Get urgent tickets
    urgent_tickets = SupportTicket.objects.filter(priority='urgent').count()
    
    context = {
        'total_tickets': total_tickets,
        'new_tickets': new_tickets,
        'active_tickets': active_tickets,
        'resolved_tickets': resolved_tickets,
        'confirmed_tickets': confirmed_tickets,
        'total_documents': total_documents,
        'recent_documents': recent_documents,
        'pending_documents': pending_documents,
        'reports_by_area': reports_by_area,
        'recent_tickets': recent_tickets,
        'urgent_tickets': urgent_tickets,
    }
    
    return render(request, 'core/admin/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_tickets(request):
    """Admin view for managing all tickets with filtering"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    tickets = SupportTicket.objects.select_related('user', 'assigned_to').prefetch_related('messages')
    
    # Apply filters
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if category_filter:
        tickets = tickets.filter(intent_category=category_filter)
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Order by priority and creation date
    tickets = tickets.order_by('-priority', '-created_at')
    
    # Pagination
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
        'intent_choices': SupportTicket.INTENT_CHOICES,
    }
    
    return render(request, 'core/admin/tickets.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_ticket_detail(request, ticket_id):
    """Detailed view of a specific ticket with chat history and actions"""
    ticket = get_object_or_404(SupportTicket.objects.select_related('user', 'assigned_to'), id=ticket_id)
    messages = ticket.messages.select_related('user').order_by('created_at')
    
    # Get related POP files
    pop_files = ProofOfPayment.objects.filter(ticket=ticket).order_by('-created_at')
    
    # Get AI suggestions
    ai_suggestions = generate_ai_suggestions(ticket)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_status':
            new_status = request.POST.get('status')
            admin_notes = request.POST.get('admin_notes', '')
            
            ticket.status = new_status
            ticket.admin_notes = admin_notes
            ticket.assigned_to = request.user
            ticket.save()
            
            # Log admin activity
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action=f'Updated ticket status to {new_status}',
                target_model='SupportTicket',
                target_id=ticket.id,
                details=f'Status changed to {new_status}. Notes: {admin_notes}'
            )
            
            messages.success(request, f'Ticket status updated to {new_status}')
            
        elif action == 'add_note':
            note = request.POST.get('note')
            if note:
                ticket.admin_notes += f'\n\n{timezone.now().strftime("%Y-%m-%d %H:%M")} - {request.user.email}: {note}'
                ticket.save()
                
                # Log admin activity
                AdminActivityLog.objects.create(
                    admin_user=request.user,
                    action='Added admin note',
                    target_model='SupportTicket',
                    target_id=ticket.id,
                    details=f'Note added: {note}'
                )
                
                messages.success(request, 'Admin note added successfully')
    
    context = {
        'ticket': ticket,
        'messages': messages,
        'pop_files': pop_files,
        'ai_suggestions': ai_suggestions,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
    }
    
    return render(request, 'core/admin/ticket_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_pop_viewer(request, pop_id):
    """View and manage proof of payment files"""
    pop = get_object_or_404(ProofOfPayment, id=pop_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            pop.status = 'approved'
            pop.admin_notes = request.POST.get('notes', '')
            pop.save()
            
            # Update related ticket if exists
            if pop.ticket:
                pop.ticket.status = 'in_progress'
                pop.ticket.save()
            
            messages.success(request, 'POP approved successfully')
            
        elif action == 'reject':
            pop.status = 'rejected'
            pop.admin_notes = request.POST.get('notes', '')
            pop.save()
            
            messages.success(request, 'POP rejected')
    
    context = {
        'pop': pop,
        'file_extension': pop.file_name.split('.')[-1].lower() if '.' in pop.file_name else '',
    }
    
    return render(request, 'core/admin/pop_viewer.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_analytics(request):
    """Analytics and insights page"""
    # Date range filter
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get tickets in date range
    tickets_in_range = SupportTicket.objects.filter(created_at__range=[start_date, end_date])
    
    # Calculate statistics
    total_tickets = tickets_in_range.count()
    resolved_tickets = tickets_in_range.filter(status__in=['fixed', 'confirmed']).count()
    avg_resolution_time = calculate_avg_resolution_time(tickets_in_range)
    
    # Category breakdown
    category_data = tickets_in_range.values('intent_category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Status breakdown
    status_data = tickets_in_range.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Daily ticket creation
    daily_data = tickets_in_range.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Admin performance
    admin_performance = AdminActivityLog.objects.filter(
        timestamp__range=[start_date, end_date],
        action__icontains='resolved'
    ).values('admin_user__email').annotate(
        resolved_count=Count('id')
    ).order_by('-resolved_count')
    
    context = {
        'total_tickets': total_tickets,
        'resolved_tickets': resolved_tickets,
        'resolution_rate': (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0,
        'avg_resolution_time': avg_resolution_time,
        'category_data': list(category_data),
        'status_data': list(status_data),
        'daily_data': list(daily_data),
        'admin_performance': admin_performance,
        'days': days,
    }
    
    return render(request, 'core/admin/analytics.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_archive(request):
    """Archive view for resolved tickets"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    user_email = request.GET.get('user_email', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset for resolved tickets
    tickets = SupportTicket.objects.filter(
        status__in=['fixed', 'confirmed', 'rejected']
    ).select_related('user', 'assigned_to')
    
    # Apply filters
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if user_email:
        tickets = tickets.filter(user__email__icontains=user_email)
    if date_from:
        tickets = tickets.filter(created_at__gte=date_from)
    if date_to:
        tickets = tickets.filter(created_at__lte=date_to)
    
    tickets = tickets.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tickets, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'user_email': user_email,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'core/admin/archive.html', context)

# Helper functions
def generate_ai_suggestions(ticket):
    """Generate AI suggestions for ticket handling"""
    try:
        # This would integrate with OpenAI API
        # For now, return mock suggestions based on ticket data
        suggestions = []
        
        if ticket.priority == 'urgent':
            suggestions.append({
                'action': 'Immediate Response Required',
                'confidence': 'High',
                'reason': 'Urgent priority ticket'
            })
        
        if ticket.intent_category == 'billing':
            suggestions.append({
                'action': 'Check Payment Records',
                'confidence': 'Medium',
                'reason': 'Billing-related issue'
            })
        
        if ticket.requires_pop:
            suggestions.append({
                'action': 'Request Proof of Payment',
                'confidence': 'High',
                'reason': 'POP required for this ticket'
            })
        
        return suggestions
    except Exception as e:
        return []

def calculate_avg_resolution_time(tickets):
    """Calculate average resolution time for tickets"""
    resolved_tickets = tickets.filter(
        status__in=['fixed', 'confirmed'],
        resolution_time__isnull=False
    )
    
    if resolved_tickets.exists():
        total_time = sum(ticket.resolution_time.total_seconds() for ticket in resolved_tickets)
        avg_seconds = total_time / resolved_tickets.count()
        return timedelta(seconds=avg_seconds)
    
    return timedelta(0)

# Missing view functions
@login_required  # Require user to be logged in
def ticket_detail(request, ticket_id):
    """Display detailed view of a specific ticket"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)  # Get ticket for this user
    messages = ChatMessage.objects.filter(ticket=ticket).order_by('created_at')  # Get chat messages for this ticket
    
    context = {
        'ticket': ticket,  # Pass ticket to template
        'messages': messages,  # Pass messages to template
    }
    return render(request, 'core/ticket_detail.html', context)  # Render ticket detail template

@login_required  # Require user to be logged in
def ticket_confirmation(request, ticket_id):
    """Handle ticket confirmation by user"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)  # Get ticket for this user
    
    if request.method == 'POST':  # If form is submitted
        satisfaction = request.POST.get('satisfaction')  # Get satisfaction rating
        if satisfaction:  # If satisfaction is provided
            ticket.user_satisfaction = int(satisfaction)  # Set satisfaction rating
            ticket.status = 'confirmed'  # Mark as confirmed
            ticket.save()  # Save changes
            messages.success(request, 'Ticket confirmed and rated. Thank you!')  # Show success message
            return redirect('tickets')  # Redirect to tickets list
    
    context = {
        'ticket': ticket,  # Pass ticket to template
    }
    return render(request, 'core/ticket_confirmation.html', context)  # Render confirmation template

@login_required
@user_passes_test(lambda u: u.is_admin)  # Require admin access
def admin_ticket_detail(request, ticket_id):
    """Admin view to manage a specific ticket"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id)  # Get ticket by ID
    messages = ChatMessage.objects.filter(ticket=ticket).order_by('created_at')  # Get chat messages for this ticket
    
    if request.method == 'POST':  # If form is submitted
        action = request.POST.get('action')  # Get action from form
        
        if action == 'update_status':  # If updating status
            new_status = request.POST.get('status')  # Get new status
            if new_status in dict(SupportTicket.STATUS_CHOICES):  # If status is valid
                ticket.status = new_status  # Update status
                ticket.save()  # Save changes
                messages.success(request, f'Ticket status updated to {ticket.get_status_display()}')  # Show success message
                
        elif action == 'assign':  # If assigning ticket
            admin_id = request.POST.get('admin')  # Get admin ID
            try:
                admin_user = CustomUser.objects.get(id=admin_id, is_admin=True)  # Get admin user
                ticket.assigned_to = admin_user  # Assign to admin
                ticket.save()  # Save changes
                messages.success(request, f'Ticket assigned to {admin_user.email}')  # Show success message
            except CustomUser.DoesNotExist:  # If admin doesn't exist
                messages.error(request, 'Invalid admin selected.')  # Show error message
    
    # Get all admin users for assignment dropdown
    admin_users = CustomUser.objects.filter(is_admin=True, is_active=True).order_by('email')  # Get all active admins
    
    context = {
        'ticket': ticket,  # Pass ticket to template
        'messages': messages,  # Pass messages to template
        'admin_users': admin_users,  # Pass admin users for assignment
        'status_choices': SupportTicket.STATUS_CHOICES,  # Pass status choices
        'priority_choices': SupportTicket.PRIORITY_CHOICES,  # Pass priority choices
    }
    return render(request, 'core/admin/ticket_detail.html', context)  # Render admin ticket detail template

# Action-related views
@login_required  # Require user to be logged in
def actions_view(request):
    """Display user's assigned actions"""
    # Get user's actions with different statuses
    pending_actions = Action.objects.filter(
        user=request.user, 
        status='pending'
    ).order_by('-priority', '-created_at')  # Order by priority first, then by newest
    
    in_progress_actions = Action.objects.filter(
        user=request.user, 
        status='in_progress'
    ).order_by('-priority', '-created_at')
    
    completed_actions = Action.objects.filter(
        user=request.user, 
        status='completed'
    ).order_by('-completed_at')[:10]  # Show last 10 completed
    
    confirmed_actions = Action.objects.filter(
        user=request.user, 
        status='confirmed'
    ).order_by('-updated_at')[:10]  # Show last 10 confirmed
    
    # Calculate statistics
    total_actions = Action.objects.filter(user=request.user).count()
    overdue_actions = Action.objects.filter(
        user=request.user,
        status__in=['pending', 'in_progress']
    ).filter(due_date__lt=timezone.now()).count()
    
    context = {
        'pending_actions': pending_actions,  # Pass pending actions
        'in_progress_actions': in_progress_actions,  # Pass in-progress actions
        'completed_actions': completed_actions,  # Pass completed actions
        'confirmed_actions': confirmed_actions,  # Pass confirmed actions
        'total_actions': total_actions,  # Pass total count
        'overdue_actions': overdue_actions,  # Pass overdue count
        'pending_count': pending_actions.count(),  # Pass pending count
        'in_progress_count': in_progress_actions.count(),  # Pass in-progress count
    }
    return render(request, 'core/actions.html', context)  # Render actions template

@login_required  # Require user to be logged in
def action_detail_view(request, action_id):
    """Display detailed view of a specific action"""
    action = get_object_or_404(Action, id=action_id, user=request.user)  # Get action for this user
    
    if request.method == 'POST':  # If form is submitted
        action_type = request.POST.get('action_type')  # Get action type from form
        
        if action_type == 'start':  # If user wants to start the action
            action.status = 'in_progress'  # Mark as in progress
            action.save()  # Save changes
            messages.success(request, 'Action marked as in progress.')  # Show success message
            
        elif action_type == 'complete':  # If user wants to complete the action
            completion_notes = request.POST.get('completion_notes', '')  # Get completion notes
            action.status = 'completed'  # Mark as completed
            action.completion_notes = completion_notes  # Save completion notes
            action.completed_at = timezone.now()  # Set completion time
            action.save()  # Save changes
            messages.success(request, 'Action marked as completed. Waiting for admin confirmation.')  # Show success message
            
        elif action_type == 'cancel':  # If user wants to cancel the action
            action.status = 'cancelled'  # Mark as cancelled
            action.save()  # Save changes
            messages.success(request, 'Action cancelled.')  # Show success message
    
    context = {
        'action': action,  # Pass action to template
        'status_choices': Action.STATUS_CHOICES,  # Pass status choices
        'priority_choices': Action.PRIORITY_CHOICES,  # Pass priority choices
    }
    return render(request, 'core/action_detail.html', context)  # Render action detail template

@login_required  # Require user to be logged in
def action_update_status(request, action_id):
    """AJAX endpoint to update action status"""
    if request.method == 'POST':  # If POST request
        action = get_object_or_404(Action, id=action_id, user=request.user)  # Get action for this user
        new_status = request.POST.get('status')  # Get new status from form
        
        if new_status in dict(Action.STATUS_CHOICES):  # If status is valid
            action.status = new_status  # Update status
            
            if new_status == 'completed':  # If marking as completed
                action.completed_at = timezone.now()  # Set completion time
                completion_notes = request.POST.get('completion_notes', '')  # Get completion notes
                action.completion_notes = completion_notes  # Save completion notes
            
            action.save()  # Save changes
            
            return JsonResponse({  # Return success response
                'success': True,
                'message': f'Action status updated to {action.get_status_display()}',
                'status': new_status,
                'status_display': action.get_status_display()
            })
        else:  # If status is invalid
            return JsonResponse({  # Return error response
                'success': False,
                'message': 'Invalid status'
            }, status=400)
    
    return JsonResponse({  # Return error for non-POST requests
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@login_required
@user_passes_test(lambda u: u.is_admin)  # Require admin access
def admin_actions_view(request):
    """Admin view to manage all actions"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')  # Get status filter
    priority_filter = request.GET.get('priority', '')  # Get priority filter
    user_email = request.GET.get('user_email', '')  # Get user email filter
    assigned_by = request.GET.get('assigned_by', '')  # Get assigned by filter
    
    # Base queryset
    actions = Action.objects.select_related('user', 'assigned_by', 'ticket')  # Get all actions with related data
    
    # Apply filters
    if status_filter:  # If status filter is applied
        actions = actions.filter(status=status_filter)
    if priority_filter:  # If priority filter is applied
        actions = actions.filter(priority=priority_filter)
    if user_email:  # If user email filter is applied
        actions = actions.filter(user__email__icontains=user_email)
    if assigned_by:  # If assigned by filter is applied
        actions = actions.filter(assigned_by__email__icontains=assigned_by)
    
    actions = actions.order_by('-priority', '-created_at')  # Order by priority first, then by newest
    
    # Pagination
    paginator = Paginator(actions, 25)  # Show 25 actions per page
    page_number = request.GET.get('page')  # Get page number
    page_obj = paginator.get_page(page_number)  # Get page object
    
    # Statistics
    total_actions = Action.objects.count()  # Count total actions
    pending_actions = Action.objects.filter(status='pending').count()  # Count pending actions
    overdue_actions = Action.objects.filter(
        status__in=['pending', 'in_progress']
    ).filter(due_date__lt=timezone.now()).count()  # Count overdue actions
    
    context = {
        'page_obj': page_obj,  # Pass page object
        'status_filter': status_filter,  # Pass status filter
        'priority_filter': priority_filter,  # Pass priority filter
        'user_email': user_email,  # Pass user email filter
        'assigned_by': assigned_by,  # Pass assigned by filter
        'total_actions': total_actions,  # Pass total count
        'pending_actions': pending_actions,  # Pass pending count
        'overdue_actions': overdue_actions,  # Pass overdue count
        'status_choices': Action.STATUS_CHOICES,  # Pass status choices
        'priority_choices': Action.PRIORITY_CHOICES,  # Pass priority choices
    }
    return render(request, 'core/admin/actions.html', context)  # Render admin actions template

@login_required
@user_passes_test(lambda u: u.is_admin)  # Require admin access
def admin_action_detail_view(request, action_id):
    """Admin view to manage a specific action"""
    action = get_object_or_404(Action, id=action_id)  # Get action by ID
    
    if request.method == 'POST':  # If form is submitted
        action_type = request.POST.get('action_type')  # Get action type from form
        
        if action_type == 'confirm':  # If admin wants to confirm completion
            action.status = 'confirmed'  # Mark as confirmed
            action.save()  # Save changes
            messages.success(request, 'Action confirmed as completed.')  # Show success message
            
        elif action_type == 'reassign':  # If admin wants to reassign
            new_user_id = request.POST.get('new_user')  # Get new user ID
            try:
                new_user = CustomUser.objects.get(id=new_user_id)  # Get new user
                action.user = new_user  # Reassign to new user
                action.status = 'pending'  # Reset status to pending
                action.save()  # Save changes
                messages.success(request, f'Action reassigned to {new_user.email}')  # Show success message
            except CustomUser.DoesNotExist:  # If user doesn't exist
                messages.error(request, 'Invalid user selected.')  # Show error message
                
        elif action_type == 'update_notes':  # If admin wants to update notes
            admin_notes = request.POST.get('admin_notes', '')  # Get admin notes
            action.admin_notes = admin_notes  # Update admin notes
            action.save()  # Save changes
            messages.success(request, 'Admin notes updated.')  # Show success message
    
    # Get all users for reassignment dropdown
    users = CustomUser.objects.filter(is_active=True).order_by('email')  # Get all active users
    
    context = {
        'action': action,  # Pass action to template
        'users': users,  # Pass users for reassignment
        'status_choices': Action.STATUS_CHOICES,  # Pass status choices
        'priority_choices': Action.PRIORITY_CHOICES,  # Pass priority choices
    }
    return render(request, 'core/admin/action_detail.html', context)  # Render admin action detail template

@login_required
@user_passes_test(lambda u: u.is_admin)  # Require admin access
def admin_create_action_view(request):
    """Admin view to create new actions"""
    if request.method == 'POST':  # If form is submitted
        # Get form data
        user_id = request.POST.get('user')  # Get user ID
        title = request.POST.get('title')  # Get title
        description = request.POST.get('description')  # Get description
        instructions = request.POST.get('instructions')  # Get instructions
        priority = request.POST.get('priority')  # Get priority
        due_date_str = request.POST.get('due_date')  # Get due date string
        ticket_id = request.POST.get('ticket')  # Get ticket ID (optional)
        
        try:
            user = CustomUser.objects.get(id=user_id)  # Get user
            due_date = None  # Initialize due date
            if due_date_str:  # If due date is provided
                due_date = timezone.datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')  # Parse due date
                due_date = timezone.make_aware(due_date)  # Make timezone aware
            
            ticket = None  # Initialize ticket
            if ticket_id:  # If ticket ID is provided
                ticket = SupportTicket.objects.get(id=ticket_id)  # Get ticket
            
            # Create new action
            action = Action.objects.create(
                user=user,  # Set user
                title=title,  # Set title
                description=description,  # Set description
                instructions=instructions,  # Set instructions
                priority=priority,  # Set priority
                due_date=due_date,  # Set due date
                ticket=ticket,  # Set ticket (optional)
                assigned_by=request.user  # Set assigned by as current admin
            )
            
            messages.success(request, f'Action "{title}" created for {user.email}')  # Show success message
            return redirect('admin_action_detail', action_id=action.id)  # Redirect to action detail
            
        except CustomUser.DoesNotExist:  # If user doesn't exist
            messages.error(request, 'Invalid user selected.')  # Show error message
        except SupportTicket.DoesNotExist:  # If ticket doesn't exist
            messages.error(request, 'Invalid ticket selected.')  # Show error message
        except ValueError:  # If date parsing fails
            messages.error(request, 'Invalid date format.')  # Show error message
    
    # Get all users and tickets for form
    users = CustomUser.objects.filter(is_active=True).order_by('email')  # Get all active users
    tickets = SupportTicket.objects.filter(status__in=['pending', 'in_progress']).order_by('-created_at')  # Get active tickets
    
    context = {
        'users': users,  # Pass users to template
        'tickets': tickets,  # Pass tickets to template
        'priority_choices': Action.PRIORITY_CHOICES,  # Pass priority choices
    }
    return render(request, 'core/admin/create_action.html', context)  # Render create action template 

# Admin action view for chat interface
@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_action_view(request):
    """Handle admin actions in chat interface"""
    if request.method == 'POST':  # If POST request
        action = request.POST.get('action')  # Get action type
        ticket_id = request.POST.get('ticket_id')  # Get ticket ID
        
        try:
            ticket = get_object_or_404(SupportTicket, id=ticket_id)  # Get ticket
            
            if action == 'mark_resolved':  # If mark resolved action
                ticket.status = 'fixed'  # Update status to fixed
                ticket.save()  # Save changes
                
                # Create admin message
                admin_message = "✅ Issue marked as resolved. Please confirm if this resolves your problem."
                
                # Log admin activity
                AdminActivityLog.objects.create(
                    admin_user=request.user,  # Set admin user
                    action='Marked Ticket Resolved',  # Set action description
                    target_model='SupportTicket',  # Set target model
                    target_id=ticket.id,  # Set target ID
                    details=f'Admin marked ticket as resolved: {ticket.title}'  # Set details
                )
                
            elif action == 'ask_info':  # If ask for info action
                ticket.status = 'in_progress'  # Update status to in progress
                ticket.save()  # Save changes
                
                # Create admin message
                admin_message = "🔍 I need more information to help you better. Could you please provide additional details about your issue?"
                
                # Log admin activity
                AdminActivityLog.objects.create(
                    admin_user=request.user,  # Set admin user
                    action='Requested More Info',  # Set action description
                    target_model='SupportTicket',  # Set target model
                    target_id=ticket.id,  # Set target ID
                    details=f'Admin requested more information for ticket: {ticket.title}'  # Set details
                )
                
            elif action == 'escalate':  # If escalate action
                ticket.priority = 'urgent'  # Update priority to urgent
                ticket.status = 'in_progress'  # Update status to in progress
                ticket.save()  # Save changes
                
                # Create admin message
                admin_message = "🚨 This issue has been escalated to our priority team. We'll address it immediately."
                
                # Log admin activity
                AdminActivityLog.objects.create(
                    admin_user=request.user,  # Set admin user
                    action='Escalated Ticket',  # Set action description
                    target_model='SupportTicket',  # Set target model
                    target_id=ticket.id,  # Set target ID
                    details=f'Admin escalated ticket: {ticket.title}'  # Set details
                )
            
            else:  # If unknown action
                return JsonResponse({'success': False, 'error': 'Invalid action'})  # Return error
            
            # Save admin message to chat
            ChatMessage.objects.create(
                ticket=ticket,  # Associate with ticket
                user=request.user,  # Set admin user
                message=admin_message,  # Save admin message
                is_ai_response=False  # Mark as admin message (not AI)
            )
            
            # Prepare response data
            response_data = {  # Initialize response data
                'success': True,
                'message': admin_message,
                'ticket_info': {  # Add updated ticket info
                    'summary': ticket.ai_summary or 'No summary available',  # Ticket summary
                    'status': ticket.status,  # Ticket status
                    'category': ticket.intent_category,  # Ticket category
                    'priority': ticket.priority,  # Ticket priority
                    'created_at': ticket.created_at.strftime('%B %d, %Y at %I:%M %p'),  # Created time
                    'admin_suggestions': generate_admin_suggestions(ticket),  # Admin suggestions
                }
            }
            
            return JsonResponse(response_data)  # Return success response
            
        except Exception as e:  # Handle errors
            print(f"Admin Action Error: {str(e)}")  # Print error for debugging
            return JsonResponse({'success': False, 'error': 'An error occurred'})  # Return error
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})  # Return error for non-POST requests

def analyze_admin_workflow(message, ticket, uploaded_files=None):
    """Analyze user request and determine what admin action is needed"""
    message_lower = message.lower()
    
    # Define workflow patterns
    workflows = {
        'deposit_confirmation': {
            'keywords': ['deposit', 'payment', 'paid', 'sent money', 'transferred', 'invested'],
            'required_documents': ['proof_of_payment', 'bank_statement'],
            'additional_info': ['amount', 'date', 'reference_number', 'bank_name'],
            'admin_action': 'Confirm deposit and credit user account',
            'priority': 'high',
            'report_type': 'deposit_confirmation'
        },
        'withdrawal_processing': {
            'keywords': ['withdraw', 'withdrawal', 'payout', 'get money', 'cash out', 'return', 'withdrawal request', 'check withdrawal'],
            'required_documents': ['proof_of_payment'],
            'additional_info': ['email'],
            'admin_action': 'Process withdrawal and transfer funds',
            'priority': 'urgent',
            'report_type': 'withdrawal_processing'
        },
        'investment_verification': {
            'keywords': ['investment', 'tier', 'verify', 'confirm investment', 'check investment'],
            'required_documents': ['investment_confirmation', 'proof_of_payment'],
            'additional_info': ['tier_name', 'amount', 'expected_return', 'duration'],
            'admin_action': 'Verify investment and activate tier benefits',
            'priority': 'high',
            'report_type': 'investment_verification'
        },
        'tier_upgrade': {
            'keywords': ['upgrade', 'next tier', 'higher tier', 'move up', 'progress'],
            'required_documents': ['proof_of_payment', 'current_tier_confirmation'],
            'additional_info': ['current_tier', 'target_tier', 'amount', 'reason'],
            'admin_action': 'Process tier upgrade and update user status',
            'priority': 'medium',
            'report_type': 'tier_upgrade'
        },
        'referral_verification': {
            'keywords': ['referral', 'refer', 'bonus', 'commission', 'earn'],
            'required_documents': ['referral_proof', 'id_document'],
            'additional_info': ['referral_code', 'referred_user', 'bonus_amount'],
            'admin_action': 'Verify referral and credit bonus',
            'priority': 'medium',
            'report_type': 'referral_verification'
        },
        'account_verification': {
            'keywords': ['verify account', 'account verification', 'kyc', 'identity'],
            'required_documents': ['id_document', 'selfie', 'proof_of_address'],
            'additional_info': ['full_name', 'date_of_birth', 'address', 'phone'],
            'admin_action': 'Verify account and update verification status',
            'priority': 'high',
            'report_type': 'account_verification'
        }
    }
    
    # Determine which workflow applies
    detected_workflow = None
    for workflow_name, workflow_data in workflows.items():
        if any(keyword in message_lower for keyword in workflow_data['keywords']):
            detected_workflow = workflow_name
            break
    
    if not detected_workflow:
        return None
    
    workflow = workflows[detected_workflow]
    
    # Create admin report
    admin_report = AdminReport.objects.create(
        report_type=workflow['report_type'],
        title=f"{workflow['report_type'].replace('_', ' ').title()} - {ticket.user.email}",
        description=f"User request: {message}\n\nAI Analysis: This appears to be a {workflow['report_type'].replace('_', ' ')} request.",
        priority=workflow['priority'],
        user=ticket.user,
        ticket=ticket,
        required_documents=workflow['required_documents'],
        additional_info_required=workflow['additional_info'],
        ai_recommendation=workflow['admin_action'],
        ai_analysis=f"User is requesting {workflow['report_type'].replace('_', ' ')}. Required documents: {', '.join(workflow['required_documents'])}. Additional info needed: {', '.join(workflow['additional_info'])}."
    )
    
    # Update ticket
    ticket.admin_report = admin_report
    ticket.required_documents = workflow['required_documents']
    ticket.ai_recommendation = workflow['admin_action']
    ticket.next_admin_action = workflow['admin_action']
    ticket.status = 'waiting_for_documents'
    ticket.save()
    
    return {
        'workflow_type': detected_workflow,
        'required_documents': workflow['required_documents'],
        'additional_info': workflow['additional_info'],
        'admin_action': workflow['admin_action'],
        'priority': workflow['priority'],
        'admin_report': admin_report
    }

def generate_document_request_message(workflow_data):
    """Generate a message asking for required documents"""
    document_names = {
        'proof_of_payment': 'Proof of Payment (screenshot or photo of payment confirmation)',
        'bank_statement': 'Bank Statement (showing the transaction)',
        'id_document': 'ID Document (passport, driver\'s license, or national ID)',
        'selfie': 'Selfie with ID (you holding your ID document)',
        'investment_confirmation': 'Investment Confirmation (screenshot of investment details)',
        'withdrawal_request': 'Withdrawal Request Form (completed form)',
        'referral_proof': 'Referral Proof (screenshot showing referral)',
        'account_statement': 'Account Statement (current account status)',
        'proof_of_address': 'Proof of Address (utility bill or bank statement)',
        'current_tier_confirmation': 'Current Tier Confirmation (screenshot of current tier)'
    }
    
    documents_text = []
    for doc in workflow_data['required_documents']:
        documents_text.append(f"• {document_names.get(doc, doc)}")
    
    info_text = []
    for info in workflow_data['additional_info']:
        info_names = {
            'amount': 'Investment/Withdrawal Amount',
            'date': 'Transaction Date',
            'reference_number': 'Reference/Transaction Number',
            'bank_name': 'Bank Name',
            'bank_details': 'Bank Account Details',
            'account_number': 'Account Number',
            'reason': 'Reason for Request',
            'tier_name': 'Tier Name',
            'expected_return': 'Expected Return',
            'duration': 'Investment Duration',
            'current_tier': 'Current Tier',
            'target_tier': 'Target Tier',
            'referral_code': 'Referral Code',
            'referred_user': 'Referred User Email',
            'bonus_amount': 'Expected Bonus Amount',
            'full_name': 'Full Name',
            'date_of_birth': 'Date of Birth',
            'address': 'Full Address',
            'phone': 'Phone Number',
            'date_requested': 'Date You Requested the Withdrawal'
        }
        info_text.append(f"• {info_names.get(info, info)}")
    
    # Special handling for withdrawal requests
    if workflow_data['workflow_type'] == 'withdrawal_processing':
        return f"""🚨 **Withdrawal Request Processing** 🚨

I understand you have a withdrawal request that needs attention. To help resolve this quickly, I need:

**📋 Required:**
• **Proof of Payment** - Screenshot or photo showing your original payment confirmation
• **Email Address** - The email address associated with your account

**📎 How to Upload:**
Please use the attachment button (📎) to upload your proof of payment.

Once you provide these, I'll immediately compile a report for our admin team to process your withdrawal.

**⏱️ Priority:** This has been marked as URGENT and will be processed immediately."""
    
    # Default message for other workflows
    return f"""I understand you need {workflow_data['workflow_type'].replace('_', ' ').title()}. 

To process your request, I need the following documents:
{chr(10).join(documents_text)}

And please provide this additional information:
{chr(10).join(info_text)}

Once you upload these documents and provide the information, I'll compile a report for our admin team to {workflow_data['admin_action'].lower()}.

Please upload the documents using the attachment button (📎) and provide the additional information in your next message."""

def check_document_completion(ticket):
    """Check if all required documents have been collected"""
    if not ticket.admin_report:
        return False
    
    collected_docs = ticket.collected_documents.all()
    required_docs = ticket.required_documents
    
    # Simple check - if we have documents uploaded, consider it complete
    # In a real system, you'd want more sophisticated document type detection
    if collected_docs.count() >= len(required_docs):
        ticket.status = 'ready_for_admin'
        ticket.save()
        
        # Update admin report
        admin_report = ticket.admin_report
        admin_report.status = 'pending'
        admin_report.save()
        
        return True
    
    return False

def generate_admin_report_summary(ticket):
    """Generate a summary message for the admin report"""
    if not ticket.admin_report:
        return None
    
    report = ticket.admin_report
    collected_docs = ticket.collected_documents.all()
    
    summary = f"""📋 **ADMIN REPORT READY** 📋

**Report Type:** {report.report_type.replace('_', ' ').title()}
**User:** {ticket.user.email}
**Priority:** {report.priority.upper()}
**Status:** Ready for Admin Review

**User Request:** {ticket.description}

**AI Analysis:** {report.ai_analysis}

**AI Recommendation:** {report.ai_recommendation}

**Collected Documents:** {collected_docs.count()} documents uploaded
**Required Documents:** {len(report.required_documents)} documents needed

**Next Admin Action:** {ticket.next_admin_action}

**Report ID:** #{report.id}
**Created:** {report.created_at.strftime('%Y-%m-%d %H:%M')}

This report has been automatically compiled and sent to the admin dashboard for review."""
    
    return summary

@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_reports_view(request):
    """Admin view to handle admin reports and workflow"""
    # Get all admin reports
    pending_reports = AdminReport.objects.filter(status='pending').order_by('-priority', '-created_at')
    in_progress_reports = AdminReport.objects.filter(status='in_progress').order_by('-priority', '-created_at')
    completed_reports = AdminReport.objects.filter(status='completed').order_by('-created_at')[:20]
    requires_info_reports = AdminReport.objects.filter(status='requires_more_info').order_by('-created_at')
    
    # Handle admin actions
    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if report_id and action:
            report = get_object_or_404(AdminReport, id=report_id)
            
            if action == 'start_processing':
                report.status = 'in_progress'
                report.assigned_admin = request.user
                report.admin_notes = admin_notes
                report.save()
                
                # Update associated ticket
                if report.ticket:
                    report.ticket.status = 'in_progress'
                    report.ticket.assigned_to = request.user
                    report.ticket.save()
                
                messages.success(request, f'Started processing report #{report.id}')
                
            elif action == 'complete':
                report.status = 'completed'
                report.admin_action_taken = admin_notes
                report.completed_at = timezone.now()
                report.save()
                
                # Update associated ticket
                if report.ticket:
                    report.ticket.status = 'fixed'
                    report.ticket.save()
                
                messages.success(request, f'Completed report #{report.id}')
                
            elif action == 'reject':
                report.status = 'rejected'
                report.admin_action_taken = admin_notes
                report.save()
                
                # Update associated ticket
                if report.ticket:
                    report.ticket.status = 'rejected'
                    report.ticket.save()
                
                messages.success(request, f'Rejected report #{report.id}')
                
            elif action == 'request_more_info':
                report.status = 'requires_more_info'
                report.admin_notes = admin_notes
                report.save()
                
                # Update associated ticket
                if report.ticket:
                    report.ticket.status = 'waiting_for_documents'
                    report.ticket.save()
                
                messages.success(request, f'Requested more info for report #{report.id}')
            
            # Log admin activity
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action=f'Report {action.title()}',
                target_model='AdminReport',
                target_id=report.id,
                details=f'Admin {action} report #{report.id} for {report.user.email}'
            )
    
    context = {
        'pending_reports': pending_reports,
        'in_progress_reports': in_progress_reports,
        'completed_reports': completed_reports,
        'requires_info_reports': requires_info_reports,
        'total_pending': pending_reports.count(),
        'total_in_progress': in_progress_reports.count(),
        'total_completed': completed_reports.count(),
        'total_requires_info': requires_info_reports.count(),
    }
    
    return render(request, 'core/admin_reports.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_report_detail_view(request, report_id):
    """Detailed view of an admin report"""
    report = get_object_or_404(AdminReport, id=report_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        admin_action = request.POST.get('admin_action', '')
        
        if action == 'update':
            report.admin_notes = admin_notes
            report.admin_action_taken = admin_action
            report.save()
            
            messages.success(request, 'Report updated successfully')
            
        elif action in ['start_processing', 'complete', 'reject', 'request_more_info']:
            if action == 'start_processing':
                report.status = 'in_progress'
                report.assigned_admin = request.user
            elif action == 'complete':
                report.status = 'completed'
                report.completed_at = timezone.now()
            elif action == 'reject':
                report.status = 'rejected'
            elif action == 'request_more_info':
                report.status = 'requires_more_info'
            
            report.admin_notes = admin_notes
            report.admin_action_taken = admin_action
            report.save()
            
            # Update associated ticket
            if report.ticket:
                if action == 'start_processing':
                    report.ticket.status = 'in_progress'
                    report.ticket.assigned_to = request.user
                elif action == 'complete':
                    report.ticket.status = 'fixed'
                elif action == 'reject':
                    report.ticket.status = 'rejected'
                elif action == 'request_more_info':
                    report.ticket.status = 'waiting_for_documents'
                report.ticket.save()
            
            messages.success(request, f'Report {action.replace("_", " ")} successfully')
            
            # Log admin activity
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action=f'Report {action.title()}',
                target_model='AdminReport',
                target_id=report.id,
                details=f'Admin {action} report #{report.id} for {report.user.email}'
            )
    
    # Get related data
    collected_documents = report.collected_documents.all()
    missing_documents = report.get_missing_documents()
    chat_messages = ChatMessage.objects.filter(ticket=report.ticket).order_by('created_at') if report.ticket else []
    
    context = {
        'report': report,
        'collected_documents': collected_documents,
        'missing_documents': missing_documents,
        'chat_messages': chat_messages,
        'is_ready_for_review': report.is_ready_for_admin_review(),
        'document_names': {
            'proof_of_payment': 'Proof of Payment',
            'bank_statement': 'Bank Statement',
            'id_document': 'ID Document',
            'selfie': 'Selfie with ID',
            'investment_confirmation': 'Investment Confirmation',
            'withdrawal_request': 'Withdrawal Request Form',
            'referral_proof': 'Referral Proof',
            'account_statement': 'Account Statement',
            'proof_of_address': 'Proof of Address',
            'current_tier_confirmation': 'Current Tier Confirmation'
        }
    }
    
    return render(request, 'core/admin_report_detail.html', context)

def understand_and_draft_problem(message, ticket, uploaded_files=None):
    """Understand user problem, draft organized summary, and confirm with user before sending to admins"""
    try:
        # Import configuration and OpenAI client
        from ai_support.settings import OPENAI_API_KEY
        from openai import OpenAI
        
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Build context from ticket history
        context = f"User has a {ticket.intent_category} ticket: {ticket.title}. "
        context += f"Priority: {ticket.priority}. "
        context += f"Requires POP: {ticket.requires_pop}. "
        
        # Add file upload context if files were uploaded
        if uploaded_files:
            file_names = [f.name for f in uploaded_files]
            context += f"User uploaded files: {', '.join(file_names)}. "
            context += "These appear to be proof of payment documents. "
        
        # Add recent chat history
        recent_messages = ChatMessage.objects.filter(ticket=ticket).order_by('-created_at')[:10]
        chat_history = ""
        for msg in reversed(recent_messages):
            role = "assistant" if msg.is_ai_response else "user"
            chat_history += f"{role}: {msg.message}\n"
        
        system_prompt = """You are a professional problem-solving assistant for SafeChain AI. Your role is to:

1. **UNDERSTAND** the user's problem completely
2. **CATEGORIZE** the issue into the correct admin management area
3. **DRAFT** a clear, organized summary of the issue
4. **CONFIRM** with the user before sending to admins

**ADMIN MANAGEMENT AREAS:**
- **Deposits**: Issues with deposits made to the app, payment confirmations, deposit verification
- **Investment Tiers**: Problems with tier levels, tier upgrades, tier benefits, tier requirements
- **Investments**: Active/inactive investments, investment cycle completion, investment status, returns
- **Users**: User account issues, account verification, profile problems, login issues
- **Wallets**: Wallet balance issues, wallet transactions, wallet settings, wallet problems
- **Withdrawals**: Withdrawal requests, withdrawal processing, withdrawal delays
- **Referrals**: Referral bonuses, referral tracking, referral rewards
- **Daily Specials**: Special offers, promotions, bonus opportunities
- **Vouchers**: Voucher codes, voucher redemption, voucher issues
- **IP Addresses**: Security issues, IP restrictions, access problems

**PROBLEM UNDERSTANDING PROCESS:**
- Ask clarifying questions if needed
- Identify the root cause of the issue
- Determine what the user wants to achieve
- Assess urgency and impact
- Match to the correct admin management area

**DRAFTING GUIDELINES:**
- Use clear, professional language
- Organize information logically
- Include all relevant details
- Highlight key points for admin attention
- Suggest potential solutions if possible
- Clearly identify the admin area that needs to handle this

**CONFIRMATION PROCESS:**
- Present the draft summary to the user
- Ask: "Is this correct? Should I send this to the admin team?"
- Wait for user confirmation before proceeding
- Make adjustments if needed

**RESPONSE FORMAT:**
If you need more information:
"🔍 **Understanding Your Issue**
[Ask specific questions to clarify the problem and identify the admin area]

If you have enough information to draft:
"📋 **Problem Summary Draft**

**Admin Area:** [Deposits/Investment Tiers/Investments/Users/Wallets/Withdrawals/Referrals/Daily Specials/Vouchers/IP Addresses]
**Issue Type:** [Specific category within the admin area]
**Priority:** [High/Medium/Low]
**User:** [Email]
**Problem Description:** [Clear summary]
**What User Wants:** [Desired outcome]
**Additional Context:** [Any relevant details]
**Suggested Admin Action:** [What admin should do in their management area]

**Please confirm:** Is this summary accurate? Should I send this to the admin team for resolution?

✅ **Yes, send to admin** | ❌ **No, let me correct it**"

Always be empathetic and professional. Focus on understanding and helping the user."""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context}\n\nChat history:\n{chat_history}\n\nUser: {message}"}
            ],
            max_tokens=800
        )
        
        ai_response = response.choices[0].message.content
        
        # If the AI response is just a general info or onboarding answer, do not escalate
        if 'how cryptovault works' in message.lower() or 'how does this work' in message.lower() or 'how to use' in message.lower():
            return {
                'response': SAFECHAIN_KNOWLEDGE.get('cryptovault_how_it_works'),
                'needs_confirmation': False,
                'is_asking_questions': False
            }
        
        return {
            'response': ai_response,
            'needs_confirmation': '📋 **Problem Summary Draft' in ai_response,
            'is_asking_questions': '🔍 **Understanding Your Issue' in ai_response
        }
        
    except Exception as e:
        print(f"Error in understand_and_draft_problem: {str(e)}")
        return {
            'response': "I apologize, but I'm having trouble processing your request right now. Please try again later.",
            'needs_confirmation': False,
            'is_asking_questions': False
        }

def confirm_problem_with_user(message, ticket):
    """Handle user confirmation of problem summary"""
    try:
        # Import configuration and OpenAI client
        from ai_support.settings import OPENAI_API_KEY
        from openai import OpenAI
        
        # Create OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Check if user is confirming or correcting
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['yes', 'correct', 'send', 'confirm', 'ok', 'good', 'right']):
            # User confirmed - create admin report
            return create_confirmed_admin_report(ticket)
        elif any(word in message_lower for word in ['no', 'wrong', 'incorrect', 'change', 'edit', 'fix']):
            # User wants to correct - ask for corrections
            return {
                'response': "I understand you'd like to correct the summary. Please tell me what needs to be changed or provide the correct information, and I'll update the draft for you.",
                'needs_correction': True
            }
        else:
            # Ambiguous response - ask for clarification
            return {
                'response': "I'm not sure if you want me to send this to the admin team or make changes. Please respond with:\n\n✅ **Yes** - to send to admin team\n❌ **No** - to make corrections",
                'needs_clarification': True
            }
            
    except Exception as e:
        print(f"Error in confirm_problem_with_user: {str(e)}")
        return {
            'response': "I apologize, but I'm having trouble processing your confirmation. Please try again.",
            'needs_correction': False,
            'needs_clarification': False
        }

def create_confirmed_admin_report(ticket):
    """Create admin report after user confirmation"""
    try:
        # Get the latest AI message that contains the problem summary
        latest_ai_message = ChatMessage.objects.filter(
            ticket=ticket, 
            is_ai_response=True
        ).order_by('-created_at').first()
        
        if not latest_ai_message:
            return {
                'response': "I couldn't find the problem summary to send to admin. Please describe your issue again.",
                'error': True
            }
        
        # Extract problem details from the AI message
        summary_text = latest_ai_message.message
        
        # Extract admin management area from the summary
        admin_area = 'general_support'  # Default
        admin_area_mapping = {
            'deposits': 'deposits',
            'deposit': 'deposits',
            'payment': 'deposits',
            'investment tiers': 'investment_tiers',
            'tier': 'investment_tiers',
            'tiers': 'investment_tiers',
            'investments': 'investments',
            'investment': 'investments',
            'users': 'users',
            'user': 'users',
            'account': 'users',
            'wallets': 'wallets',
            'wallet': 'wallets',
            'balance': 'wallets',
            'withdrawals': 'withdrawals',
            'withdrawal': 'withdrawals',
            'withdraw': 'withdrawals',
            'referrals': 'referrals',
            'referral': 'referrals',
            'daily specials': 'daily_specials',
            'specials': 'daily_specials',
            'vouchers': 'vouchers',
            'voucher': 'vouchers',
            'ip addresses': 'ip_addresses',
            'ip address': 'ip_addresses',
            'ip': 'ip_addresses'
        }
        
        summary_lower = summary_text.lower()
        for keyword, area in admin_area_mapping.items():
            if keyword in summary_lower:
                admin_area = area
                break
        
        # Create admin report
        admin_report = AdminReport.objects.create(
            report_type='user_confirmed_issue',
            admin_management_area=admin_area,
            title=f"User Confirmed Issue - {ticket.user.email}",
            description=summary_text,
            priority=ticket.priority,
            user=ticket.user,
            ticket=ticket,
            required_documents=[],
            additional_info_required=[],
            ai_recommendation='User confirmed issue - requires admin review and resolution',
            ai_analysis=f'User has confirmed the problem summary. Issue type: {ticket.intent_category}. Priority: {ticket.priority}. Admin area: {admin_area}.'
        )
        
        # Update ticket
        ticket.admin_report = admin_report
        ticket.status = 'waiting_for_admin'
        ticket.save()
        
        # Notify admins
        notify_admins_new_report(admin_report)
        
        return {
            'response': """✅ **Confirmed and Sent to Admin Team!**

Your issue has been successfully sent to our admin team for resolution. Here's what happens next:

**📋 Admin Review Process:**
• Admin will review your issue within 24 hours
• You'll receive updates on the progress
• Admin may contact you for additional information if needed

**📊 Your Ticket Status:** Waiting for Admin Review
**🎫 Ticket ID:** #{ticket.id}
**🔧 Admin Area:** {admin_area_display}

**📧 How to Check Status:**
• Visit your dashboard to see ticket updates
• You'll receive notifications when admin responds
• You can also check the status in your tickets section

Thank you for your patience. Our admin team will work to resolve your issue as quickly as possible!""".format(
                ticket=ticket,
                admin_area_display=dict(AdminReport.ADMIN_MANAGEMENT_AREAS).get(admin_area, 'General Support')
            ),
            'admin_report_created': True,
            'ticket_id': ticket.id
        }
        
    except Exception as e:
        print(f"Error in create_confirmed_admin_report: {str(e)}")
        return {
            'response': "I apologize, but there was an error sending your issue to the admin team. Please try again or contact support directly.",
            'error': True
        }

def notify_admins_new_report(report):
    """Notify admins when new confirmed report is created"""
    admins = CustomUser.objects.filter(is_admin=True)
    for admin in admins:
        admin_area_display = dict(AdminReport.ADMIN_MANAGEMENT_AREAS).get(report.admin_management_area, 'General Support')
        notification_message = f"""
📋 **New User Confirmed Issue Report**

**User:** {report.user.email}
**Issue Type:** {report.report_type.replace('_', ' ').title()}
**Admin Area:** {admin_area_display}
**Priority:** {report.priority}
**Ticket ID:** #{report.ticket.id}

**Problem Summary:**
{report.description[:200]}{'...' if len(report.description) > 200 else ''}

**Action Required:** Review and resolve user issue in {admin_area_display} section
**Status:** User has confirmed the problem summary

Please review this report and take appropriate action in the {admin_area_display} management area.
        """.strip()
        
        Notification.objects.create(
            user=admin,
            title=f"📋 New User Confirmed Issue - {admin_area_display} - Action Required",
            message=notification_message
        )

def health_check(request):
    """Health check endpoint for Render monitoring"""
    from django.http import JsonResponse
    return JsonResponse({"status": "healthy"}, status=200)