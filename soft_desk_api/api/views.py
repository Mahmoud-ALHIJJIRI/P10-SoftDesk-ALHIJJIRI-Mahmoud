# Third-party imports (Django Rest Framework)
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, BasePermission



# Local project imports (your serializers and models)
from .models import Comment, Project, Ticket, User
from .serializers import (
    CommentSerializer, 
    ProjectDetailSerializer, ProjectSerializer, 
    TicketDetailSerializer, TicketSerializer, 
    UserDetailSerializer, UserSerializer
)

class IsProjectContributor(BasePermission):
    #Custom permission to ensure only users registered to a project can perform CRUD on tickets.
    def has_object_permission(self, request, view, obj):
        # Get the project associated with the ticket (obj is the ticket)
        project = obj.project
        # Check if the authenticated user is associated with the project
        if any((
            request.user.is_superuser, 
            request.user in project.contributor.all()
            )):
            return True
        # Otherwise, deny permission
        raise PermissionDenied('You do not have permission to do this action')

      
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Dynamically return the appropriate serializer class
        if self.action == 'list':
            return UserSerializer  # Use lightweight serializer for user list
        return UserDetailSerializer  # Use detailed serializer for other actions
    
    def check_user_permission(self, request, user_to_modify):
        # Check if the authenticated user is the same as the user being modified, or if the authenticated user is a superuser
        authenticated_user = request.user
        if authenticated_user != user_to_modify and not authenticated_user.is_superuser:
            raise PermissionDenied('You do not have permission to modify or delete this user.')
    
    def update(self, request, *args, **kwargs):
        # Check permission
        self.check_user_permission(request, self.get_object())
        return super().update(request, *args, **kwargs)  # Allow update

    def partial_update(self, request, *args, **kwargs):
        # Check permission
        self.check_user_permission(request, self.get_object())
        return super().partial_update(request, *args, **kwargs)  # Allow partial update

    def destroy(self, request, *args, **kwargs):
        # Check permission
        self.check_user_permission(request, self.get_object())
        return super().destroy(request, *args, **kwargs)  # Allow delete


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Dynamically return the appropriate serializer class
        if self.action == 'list':
            return ProjectSerializer  # Use simple serializer for listing projects
        return ProjectDetailSerializer  # Use detailed serializer for other actions
    
    def check_creator_permission(self, request):
        # Retrieve the project instance
        project = self.get_object()
        authenticated_user = request.user
        # Check if the authenticated user is either the creator or a superuser
        if project.creator != authenticated_user and not authenticated_user.is_superuser:
            raise PermissionDenied('You do not have permission to modify or delete this project.')
    
    def perform_create(self, serializer):
        user = self.request.user

        if not user or user.is_anonymous:
            raise ValueError("User must be authenticated to create a project.")
        project = serializer.save(creator=user)
        project.contributor.add(user)
    
    def partial_update(self, request, *args, **kwargs):
        # Check if the user has permission to update the project
        self.check_creator_permission(request)
        # Proceed with the partial update if permission is granted
        return super().partial_update(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        # Check if the user has permission to update the project
        self.check_creator_permission(request)
        # Proceed with the update if permission is granted
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        # Check if the user has permission to delete the project
        self.check_creator_permission(request)
        # Proceed with the deletion if permission is granted
        return super().destroy(request, *args, **kwargs)


class TicketViewSet(ModelViewSet):
    queryset = Ticket.objects.all()
    permission_classes = [IsAuthenticated, IsProjectContributor]

    def get_serializer_class(self):
        # Dynamically return the appropriate serializer class
        if self.action == 'list':
            return TicketSerializer
        return TicketDetailSerializer

    def get_project(self):
        # Helper method to retrieve the project from the URL and validate it
        project_id = self.kwargs.get('project_pk')
        if not project_id:
            raise NotFound(detail="Project ID not provided.")
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise NotFound(detail="Project not found.")
        return project

    def get_queryset(self):
        # Use the helper method to get the project
        project = self.get_project()
        # Filter tickets by project
        return Ticket.objects.filter(project=project)

    def check_ticket_permission(self):
        project = self.get_project()
        authenticated_user = self.request.user
        ticket = self.get_object()

        if not any([
            ticket.affected_user == authenticated_user,
            authenticated_user.is_superuser
            ]):
            raise PermissionDenied('You do not have permission to modify or delete this ticket')
    
    def list_contributor(self):
        project = self.get_project()
        contributors = project.contributor.all()  # Use a different variable name for clarity
        return contributors  # Return the list of contributor objects
    
    def ticket_assinge(self, request):
        contributors = self.list_contributor()  # Call the method to get the list
        data = request.data.copy()
        assigned_to_id = data.get('assigned_to')

        if assigned_to_id is not None:
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
            except User.DoesNotExist:
                raise NotFound('User not found')
            if assigned_to not in contributors:
                raise PermissionDenied(
                    'The user you are trying to assign the ticket to is not a project contributor.'
                )
            return assigned_to
        return None

    def create(self, request, *args, **kwargs):
        project = self.get_project()
        user = self.request.user
        data = request.data.copy()
        assigned_to = self.ticket_assinge(request)


        data['project'] = project.id
        data['affected_user'] = user.id

        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            serializer.save(project=project, affected_user=user, assigned_to=assigned_to)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)            
  
    def partial_update(self, request, *args, **kwargs):
        self.check_ticket_permission()
        self.ticket_assinge(request)
        return super().partial_update(request, *args, **kwargs)

class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer

    def get_ticket(self):
        # Retrieve the ticket ID from the URL and fetch the ticket instance
        ticket_id = self.kwargs.get('ticket_pk')

        if not ticket_id:
            raise NotFound(detail="Ticket ID not provided.")
        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            raise NotFound(detail="Ticket not found.")
        return ticket
    
    def get_queryset(self):
        # Use get_ticket() to get the ticket and filter comments
        ticket = self.get_ticket()
        return Comment.objects.filter(parent_ticket=ticket)

    def create(self, request, *args, **kwargs):
        # Use get_ticket() to get the ticket
        ticket = self.get_ticket()
        
        # Prepare the data and associate the comment with the parent ticket
        data = request.data.copy()
        data['parent_ticket'] = ticket.id  # Set the foreign key to the parent ticket
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(parent_ticket=ticket)  # Save the comment with the parent ticket
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
