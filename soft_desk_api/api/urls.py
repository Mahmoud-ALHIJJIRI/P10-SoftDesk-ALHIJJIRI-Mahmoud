from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from api.views import UserViewSet, ProjectViewSet, TicketViewSet, CommentViewSet


# Main router for users and projects
router = DefaultRouter()
router.register(r'user', UserViewSet, basename='user')
router.register(r'project', ProjectViewSet, basename='project')


# Nested router for tickets under projects
project_router = NestedDefaultRouter(router, r'project', lookup='project')
project_router.register(r'ticket', TicketViewSet, basename='ticket')


ticket_router = NestedDefaultRouter(project_router, r'ticket', lookup='ticket')
ticket_router.register(r'comment', CommentViewSet, basename='comment')


# URL patterns
urlpatterns = [
    path('', include(router.urls)),  # Include main router
    path('', include(project_router.urls)),  # Include nested ticket routes
    path('', include(ticket_router.urls)),
]
