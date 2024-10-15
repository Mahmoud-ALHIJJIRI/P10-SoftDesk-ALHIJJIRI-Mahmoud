# Importing necessary modules for URL routing
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

# Importing viewsets from the API views
from api.views import UserViewSet, ProjectViewSet, TicketViewSet, CommentViewSet

# Setting up the main router for users and projects
router = DefaultRouter()
router.register(r'user', UserViewSet, basename='user')
router.register(r'project', ProjectViewSet, basename='project')

# Setting up nested router for tickets under projects
project_router = NestedDefaultRouter(router, r'project', lookup='project')
project_router.register(r'ticket', TicketViewSet, basename='ticket')

# Setting up nested router for comments under tickets
ticket_router = NestedDefaultRouter(project_router, r'ticket', lookup='ticket')
ticket_router.register(r'comment', CommentViewSet, basename='comment')

# Defining URL patterns
urlpatterns = [
    # Include main router URLs
    path('', include(router.urls)),
    # Include nested project routes URLs
    path('', include(project_router.urls)),
    # Include nested ticket routes URLs
    path('', include(ticket_router.urls)),
]
