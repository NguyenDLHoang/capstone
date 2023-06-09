from users.views import LoginView
from django.urls import path, re_path
from tasks.views import *

app_name='tasks'

urlpatterns = [
    # Plain url sends user to login page.
    path('', LoginView, name='home'),

    # URLs for tasks and it's related functionalities.
    re_path('tasks/(?P<pk>\d+)', TaskDetailView.as_view(), name='task_details'),
    re_path('tasks_delete/(?P<pk>\d+)', TaskDeleteView.as_view(), name='task_delete'),
    re_path('tasks?sort=(.*)', TaskCreateView.as_view(), name='task_sort'),

    # URLs for task lists and it's related functionalities.
    re_path('lists/(?P<pk>\d+)$', TaskCreateView.as_view(), name='list_tasks'),
    re_path('lists_delete/(?P<pk>\d+)', ListDeleteView.as_view(), name='list_delete'),
    re_path('list_details/(?P<pk>\d+)$', ListDetailView.as_view(), name='list_details'),

    # URLs for task groups and it's related functionalities.
    re_path('groups/(?P<pk>\d+)$', TaskListCreateView.as_view(), name='group_list'),
    re_path('groups_delete/(?P<pk>\d+)', GroupDeleteView.as_view(), name='group_delete'),
    re_path('group_details/(?P<pk>\d+)$', GroupDetailView.as_view(), name='group_details'),
    re_path('groups_notify/(?P<pk>\d+)$', TaskGroupNotifyView.as_view(), name='group_notify'),

    # URLs for managing group members and it's related functionalities.
    re_path('group_members/(?P<pk>\d+)$', TaskGroupMembersView.as_view(), name='members_list'),
    path('group_members/promote', TaskGroupMembersView.promote, name='members_promote'),
    path('group_members/demote', TaskGroupMembersView.demote, name='members_demote'),
    path('group_members/kick', TaskGroupMembersView.kick, name='members_kick'),
    path('group_members/leave', TaskGroupMembersView.leave, name='members_leave'),
    
    # URLs for actioning notifications.
    path('notification/delete/<int:notification_pk>', RemoveNotification.as_view(), name='notification_delete'),
    path('notification/accept/<int:notification_pk>', AcceptNotification.as_view(), name='notification_accept'),
    path('notification/decline/<int:notification_pk>', DeclineNotification.as_view(), name='notification_decline'),
    
    # URL for creating tags (not necessary if preloaded fixtures).
    path('tags/', TagCreateView.as_view(), name='tags'),
    
    # URLs for the dashboard and it's related functionalities.
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('groups/', DashboardGroups.as_view(), name='dashboard_groups'),
    path('dashboard/get_help/', get_help, name='get_help'),
]






    
