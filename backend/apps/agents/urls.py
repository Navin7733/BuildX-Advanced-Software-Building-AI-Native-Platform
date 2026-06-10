from django.urls import path
from . import views

urlpatterns = [
    path('projects/<str:project_id>/agents/run/', views.run_workflow, name='run-workflow'),
    path('projects/<str:project_id>/agents/<str:agent_type>/run/', views.run_agent, name='run-agent'),
    path('projects/<str:project_id>/agents/runs/', views.list_agent_runs, name='list-agent-runs'),
]
