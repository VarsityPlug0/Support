from django.urls import path  # Import path function for URL patterns
from . import views  # Import our views

urlpatterns = [
    path('', views.chat_view, name='home'),  # Chat as main page
    path('register/', views.register_view, name='register'),  # User registration route
    path('login/', views.login_view, name='login'),  # User login route
    path('logout/', views.logout_view, name='logout'),  # User logout route
    path('profile/', views.profile_view, name='profile'),  # User profile route
    path('dashboard/', views.chat_view, name='dashboard'),  # Redirect dashboard to chat
    path('chat/', views.chat_view, name='chat'),  # AI chat route
    path('admin-action/', views.admin_action_view, name='admin_action'),  # Admin action route
    path('upload-pop/', views.chat_view, name='upload_pop'),  # Redirect POP upload to chat
    path('tickets/', views.chat_view, name='tickets'),  # Redirect tickets to chat
    path('actions/', views.chat_view, name='actions'),  # Redirect actions to chat
    path('action/<int:action_id>/', views.chat_view, name='action_detail'),  # Redirect action detail to chat
    path('action/<int:action_id>/update-status/', views.action_update_status, name='action_update_status'),  # Action status update route
    path('ticket/<int:ticket_id>/confirm/', views.ticket_confirmation_view, name='ticket_confirmation'),  # Ticket confirmation route
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),  # Admin dashboard route
    path('admin-pops/', views.admin_pops_view, name='admin_pops'),  # Admin POPs management route
    path('admin-tickets/', views.admin_tickets_view, name='admin_tickets'),  # Admin tickets management route
    path('admin-actions/', views.admin_actions_view, name='admin_actions'),  # Admin actions management route
    path('admin-action/<int:action_id>/', views.admin_action_detail_view, name='admin_action_detail'),  # Admin action detail route
    path('admin-create-action/', views.admin_create_action_view, name='admin_create_action'),  # Admin create action route
    path('ticket/<int:ticket_id>/', views.chat_view, name='ticket_detail'),  # Redirect ticket detail to chat
    path('ticket-confirmation/<int:ticket_id>/', views.ticket_confirmation, name='ticket_confirmation'),  # Ticket confirmation
    path('admin-ticket/<int:ticket_id>/', views.admin_ticket_detail, name='admin_ticket_detail'),  # Admin ticket detail
    path('admin-pop/<int:pop_id>/', views.admin_pop_viewer, name='admin_pop_viewer'),  # Admin POP viewer
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),  # Admin analytics
    path('admin-archive/', views.admin_archive, name='admin_archive'),  # Admin archive
    path('admin-reports/', views.admin_reports_view, name='admin_reports'),  # Admin reports management route
    path('admin-report/<int:report_id>/', views.admin_report_detail_view, name='admin_report_detail'),  # Admin report detail route
    path('health/', views.health_check, name='health_check'),
] 