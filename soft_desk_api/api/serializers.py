from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import User, Project, Ticket, Comment


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'name']

class TicketSerializer(ModelSerializer):

    class Meta:
        model = User

class ProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']

    
class ProjectDetailSerializer(ModelSerializer):
    
    contributor = UserSerializer(many=True, read_only=True)  # 'many=True' because it's a ManyToManyField
    incidents_count = serializers.SerializerMethodField()  # Custom field to show only the number of incidents

    class Meta:
        model = Project
        fields = ['id', 'name', 'creator', 'description', 'type', 'created_at', 'incidents_count', 'contributor']


    def get_incidents_count(self, obj):
        # Return the count of incidents (related tickets) for the project
        return obj.incidents.count()

class UserDetailSerializer(ModelSerializer):
    
    contributed_projects = ProjectSerializer(many=True, read_only=True)

    class Meta: 
        model = User
        fields = ['id', 'name', 'age', 'contact_preference', 'data_sharing', 'contributed_projects']


class TicketSerializer(ModelSerializer):

    affected_user = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'affected_user', 'assigned_to', 'title', 'details', 'project', 'created_at']


class CommentSerializer(ModelSerializer):

    class Meta:
        model = Comment
        fields = ['id', 'contributor', 'text', 'parent_ticket', 'created_at']