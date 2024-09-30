from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from .serializers import UserSerializer, UserDetailSerializer, ProjectSerializer, ProjectDetailSerializer 
from .serializers import TicketSerializer, CommentSerializer
from .models import User, Project, Ticket, Comment
from rest_framework import status




class UserViewSet(ModelViewSet):
    
    queryset = User.objects.all()

    def get_serializer_class(self):

        if self.action == 'list':
            return UserSerializer
        return UserDetailSerializer
    
    def list(self,request, *args, **kwargs):

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    


class ProjectViewSet(ModelViewSet):

    queryset = Project.objects.all()

    def get_serializer_class(self):

        if self.action == 'list':
            return ProjectSerializer
        return ProjectDetailSerializer
    
    def list(self, request, *args, **kwargs):

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    


class TicketViewSet(ModelViewSet):
    serializer_class = TicketSerializer

    def get_queryset(self):
        # Retrieve the project_id from the nested router URL (passed as 'project_pk')
        project_id = self.kwargs.get('project_pk')
        # Filter tickets by project_id
        return Ticket.objects.filter(project__id=project_id)

    def create(self, request, *args, **kwargs):
        # Retrieve the project_id from the URL
        project_id = self.kwargs.get('project_pk')
        try:
            # Get the project instance
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
        
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

    def get_queryset(self):
        # Retrieve the ticket_id from the URL (nested router passes this)
        ticket_id = self.kwargs.get('ticket_pk')
        
        # Filter comments based on the correct field 'parent_ticket'
        return Comment.objects.filter(parent_ticket__id=ticket_id)

    def create(self, request, *args, **kwargs):
        # Get the ticket ID from the nested URL
        ticket_id = self.kwargs.get('ticket_pk')
        
        try:
            # Fetch the ticket instance
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return Response({"error": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare the data and associate the comment with the correct field 'parent_ticket'
        data = request.data.copy()
        data['parent_ticket'] = ticket.id  # Use 'parent_ticket' as the foreign key field
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(parent_ticket=ticket)  # Use 'parent_ticket' in save
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
