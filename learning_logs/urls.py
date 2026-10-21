from django.urls import path
from . import views

app_name = 'learning_logs'

urlpatterns = [
    # Landing & Dashboard
    path('', views.index_view, name='index'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Topics
    path('topics/', views.topic_list_view, name='topic_list'),
    path('topics/new/', views.topic_create_view, name='topic_create'),
    path('topics/<int:topic_id>/', views.topic_detail_view, name='topic_detail'),
    path('topics/<int:topic_id>/edit/', views.topic_edit_view, name='topic_edit'),
    path('topics/<int:topic_id>/delete/', views.topic_delete_view, name='topic_delete'),

    # Entries
    path('topics/<int:topic_id>/entries/new/', views.entry_create_view, name='topic_entry_create'),
    path('entries/new/', views.entry_create_view, name='entry_create'),
    path('entries/<int:entry_id>/edit/', views.entry_edit_view, name='entry_edit'),
    path('entries/<int:entry_id>/delete/', views.entry_delete_view, name='entry_delete'),

    # Search
    path('search/', views.search_view, name='search'),
]
