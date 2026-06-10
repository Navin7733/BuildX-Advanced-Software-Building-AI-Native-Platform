from django.urls import path
from . import views

urlpatterns = [
    path('projects/<str:project_id>/memory/', views.list_memories, name='list-memories'),
    path('projects/<str:project_id>/memory/search/', views.search_memories, name='search-memories'),
]
