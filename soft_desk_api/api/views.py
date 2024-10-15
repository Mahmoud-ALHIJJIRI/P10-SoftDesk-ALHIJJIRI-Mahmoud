# Importing necessary classes from Django Rest Framework
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, BasePermission

# Importing local models and serializers
from .models import Comment, Project, Ticket, User
from .serializers import (
    CommentSerializer,
    ProjectDetailSerializer, ProjectSerializer,
    TicketDetailSerializer, TicketSerializer,
    UserDetailSerializer, UserSerializer
)


# Custom permission class to check if user is a project contributor
class IsProjectContributor(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Ensure only contributors or superusers can perform actions on tickets
        project = obj.project
        if any((request.user.is_superuser, request.user in project.contributor.all())):
            return True
        raise PermissionDenied('You do not have permission to do this action')


# Mixin to handle project retrieval
class GetProjectMixin:

    def get_project(self):
        # Helper method to retrieve the project from the URL
        project_id = self.kwargs.get('project_pk')
        if not project_id:
            raise NotFound(detail="Project ID not provided.")
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise NotFound(detail="Project not found.")
        return project


# ViewSet for User model to handle CRUD operations
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Choose serializer based on action type
        if self.action == 'list':
            return UserSerializer
        return UserDetailSerializer

    def check_user_permission(self, request, user_to_modify):
        # Check if user has permission to modify or delete
        authenticated_user = request.user
        if authenticated_user != user_to_modify and not authenticated_user.is_superuser:
            raise PermissionDenied('You do not have permission to modify or delete this user.')

    def update(self, request, *args, **kwargs):
        # Update user information if permission is granted
        self.check_user_permission(request, self.get_object())
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        # Partially update user information if permission is granted
        self.check_user_permission(request, self.get_object())
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Delete user if permission is granted
        self.check_user_permission(request, self.get_object())
        return super().destroy(request, *args, **kwargs)


# ViewSet for Project model to handle CRUD operations
class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Choose serializer based on action type
        if self.action == 'list':
            return ProjectSerializer
        return ProjectDetailSerializer

    def check_creator_permission(self, request):
        # Ensure only the creator or a superuser can modify or delete the project
        project = self.get_object()
        authenticated_user = request.user
        if project.creator != authenticated_user and not authenticated_user.is_superuser:
            raise PermissionDenied('You do not have permission to modify or delete this project.')

    def perform_create(self, serializer):
        # Assign the authenticated user as the project creator and add as contributor
        user = self.request.user
        if not user or user.is_anonymous:
            raise ValueError("User must be authenticated to create a project.")
        project = serializer.save(creator=user)
        project.contributor.add(user)

    def partial_update(self, request, *args, **kwargs):
        # Partially update the project if permission is granted
        self.check_creator_permission(request)
        return super().partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Update the project if permission is granted
        self.check_creator_permission(request)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Delete the project if permission is granted
        self.check_creator_permission(request)
        return super().destroy(request, *args, **kwargs)


# ViewSet for Ticket model to handle CRUD operations
class TicketViewSet(ModelViewSet, GetProjectMixin):
    queryset = Ticket.objects.all()
    permission_classes = [IsAuthenticated, IsProjectContributor]

    def get_serializer_class(self):
        # Choose serializer based on action type
        if self.action == 'list':
            return TicketSerializer
        return TicketDetailSerializer

    def get_queryset(self):
        # Get project and filter tickets by project
        project = self.get_project()
        return Ticket.objects.filter(project=project)

    def check_ticket_permission(self):
        # Ensure only the affected user or superuser can modify or delete the ticket
        authenticated_user = self.request.user
        ticket = self.get_object()
        if not any([ticket.affected_user == authenticated_user, authenticated_user.is_superuser]):
            raise PermissionDenied('You do not have permission to modify or delete this ticket')

    def list_contributor(self):
        # Get contributors to the project
        project = self.get_project()
        return project.contributor.all()

    def ticket_assigne(self, request):
        # Assign a user to the ticket if they are a project contributor
        contributors = self.list_contributor()
        data = request.data.copy()
        assigned_to_id = data.get('assigned_to')

        if assigned_to_id is None:
            return

        try:
            assigned_to_id = int(assigned_to_id)
        except (ValueError, TypeError):
            raise ValidationError("Assigned user ID should be a valid User ID.")

        try:
            assigned_to = User.objects.get(id=assigned_to_id)
        except User.DoesNotExist:
            raise NotFound('User not found')

        if assigned_to not in contributors:
            raise PermissionDenied('The user you are trying to assign the ticket to is not a project contributor.')

        return assigned_to

    def create(self, request, *args, **kwargs):
        # Create a new ticket with validated data
        project = self.get_project()
        user = self.request.user
        data = request.data.copy()
        assigned_to = self.ticket_assigne(request)

        data['project'] = project.id
        data['affected_user'] = user.id

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(project=project, affected_user=user, assigned_to=assigned_to)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        # Get the list of contributors for the project associated with the ticket
        contributors = self.list_contributor()
        ticket = self.get_object()

        # If the request contains 'status', check if the user is a contributor
        if 'status' in request.data:
            # Check if the user is a contributor
            if not contributors.filter(id=request.user.id).exists():
                raise ValidationError('You do not have permission to update the status of this ticket.')
                # Ensure the contributor is only updating the 'status' field
                if set(request.data.keys()) != {'status'}:
                    raise ValidationError('As a contributor, you are only allowed to update the status of the ticket.')
        else:
            # If the user is not trying to update 'status', check broader permissions
            self.check_ticket_permission()

        # Check if 'assigned_to' is in the request and handle that if the user has permission
        if 'assigned_to' in request.data and self.check_ticket_permission():
            ticket.assigned_to = self.ticket_assigne(request)

        # Proceed with the partial update for the fields allowed
        serializer = self.get_serializer(ticket, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


    def update(self, request, *args, **kwargs):
        # Update ticket information if permission is granted
        self.check_ticket_permission()
        ticket = self.get_object()
        ticket.assigned_to = self.ticket_assigne(request)

        if 'assigned_to' not in request.data:
            raise ValidationError('The following field is required: assigned_to')

        serializer = self.get_serializer(ticket, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        # Delete ticket and return custom response with details
        instance = self.get_object()
        object_id = instance.id
        object_title = instance.title
        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": f"Object with ID {object_id} and title '{object_title}' has been deleted."},
            status=status.HTTP_200_OK
        )


# ViewSet for Comment model to handle CRUD operations
class CommentViewSet(ModelViewSet, GetProjectMixin):
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated, IsProjectContributor]
    serializer_class = CommentSerializer

    def get_queryset(self):
        # Get ticket and filter comments by ticket
        ticket = self.get_ticket()
        return Comment.objects.filter(parent_ticket=ticket)

    def get_ticket(self):
        # Get the ticket and validate it belongs to the correct project
        project = self.get_project()
        ticket_id = self.kwargs.get('ticket_pk')
        if not ticket_id.isdigit():
            raise ValidationError(
                detail="Invalid Ticket ID format. Ticket ID must be a number.",
                code=status.HTTP_400_BAD_REQUEST
            )
        try:
            ticket = Ticket.objects.get(id=ticket_id, project=project)
        except Ticket.DoesNotExist:
            raise ValidationError(
                detail="Ticket not found for the specified project.",
                code=status.HTTP_404_NOT_FOUND
            )
        return ticket

    def check_comment_permission(self, request):
        # Ensure only the commenter or a superuser can modify or delete the comment
        comment = self.get_object()
        authenticated_user = request.user
        if comment.commenter != authenticated_user and not authenticated_user.is_superuser:
            raise PermissionDenied('You do not have permission to modify or delete this comment.')

    def create(self, request, *args, **kwargs):
        # Create a new comment with validated data
        ticket = self.get_ticket()
        project = self.get_project()
        user = self.request.user
        data = request.data.copy()

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(parent_ticket=ticket, project=project, commenter=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        # Update comment information if permission is granted
        self.check_comment_permission(request)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Delete comment and return custom response with details
        self.check_comment_permission(request)
        comment = self.get_object()
        comment_id = comment.id
        super().destroy(request, *args, **kwargs)
        return Response({"message": f"Object with ID {comment_id} has been deleted."})
