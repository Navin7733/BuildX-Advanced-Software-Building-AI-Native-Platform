from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project-list'),
    path('<str:project_id>/', views.project_detail, name='project-detail'),
    path('<str:project_id>/files/', views.project_files, name='project-files'),
    path('<str:project_id>/files/<path:file_path>/', views.project_file_content, name='project-file-content'),
    path('<str:project_id>/decisions/', views.project_decisions, name='project-decisions'),
    path('<str:project_id>/tech-debt/', views.project_tech_debt, name='project-tech-debt'),
]
