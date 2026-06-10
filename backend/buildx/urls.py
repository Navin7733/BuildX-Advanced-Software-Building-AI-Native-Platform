from django.urls import path, include

urlpatterns = [
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/projects/', include('apps.projects.urls')),
    path('api/v1/', include('apps.agents.urls')),
    path('api/v1/', include('apps.memory.urls')),
]
