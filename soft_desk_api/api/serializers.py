from rest_framework.serializers import ModelSerializer

from .models import User, Project, Ticket, Comment

class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'name', 'age', 'contacted_prefernce', 'data_sharing']

    
class ProjectSerializer(ModelSerializer):
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'creator', 'description', 'tickets', 'type', 'contributor', 'created_at']


class TicketSerializer(ModelSerializer):

    class Meta:
        model = Ticket
        fields = ['id', 'affected_user', 'assigned_to', 'title', 'details', 'project', 'created_at']


class CommentSerializer(ModelSerializer):

    class Meta:
        model = Comment
        fields = ['id', 'contributor', 'text', 'parent_ticket', 'created_at']