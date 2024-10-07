# Third-party imports (Django Rest Framework)
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

# Local project imports (your serializers and models)
from .models import Comment, Project, Ticket, User
from .serializers import (
    CommentSerializer, 
    ProjectDetailSerializer, ProjectSerializer, 
    TicketDetailSerializer, TicketSerializer, 
    UserDetailSerializer, UserSerializer
)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        # Dynamically return the appropriate serializer class
        if self.action == 'list':
            return UserSerializer  # Use lightweight serializer for user list
        return UserDetailSerializer  # Use detailed serializer for other actions
    

class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()

    def get_serializer_class(self):
        # Dynamically return the appropriate serializer class
        if self.action == 'list':
            return ProjectSerializer  # Use simple serializer for listing projects
        return ProjectDetailSerializer  # Use detailed serializer for other actions
    
    def perform_create(self, serializer):
        user = self.request.user
        # Debugging: Check if the user is being passed correctly
        print(f"Authenticated User: {user}")  # This should print the user's details
        # Ensure the user is properly authenticated and is not None
        if not user or user.is_anonymous:
            raise ValueError("User must be authenticated to create a project.")
        project = serializer.save(creator=user)
        project.contributor.add(user)





class TicketViewSet(ModelViewSet):


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

    def create(self, request, *args, **kwargs):
        # Use the helper method to get the project
        project = self.get_project()

        # Prepare ticket data and associate it with the project
        data = request.data.copy()
        data['project'] = project.id
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
