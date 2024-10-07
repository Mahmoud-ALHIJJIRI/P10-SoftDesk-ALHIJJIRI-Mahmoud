from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import User, Project, Ticket, Comment


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username']


class ProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']

    
class ProjectDetailSerializer(ModelSerializer):
    
    contributor = UserSerializer(many=True, read_only=True)  # 'many=True' because it's a ManyToManyField
    incidents_count = serializers.SerializerMethodField()  # Custom field to show only the number of incidents
    creator = serializers.ReadOnlyField(source='creator.username')  # Make the creator field read-only

    class Meta:
        model = Project
        fields = ['id', 'name', 'creator', 'description', 'type', 'created_at', 'incidents_count', 
                  'contributor']


    def get_incidents_count(self, obj):
        # Return the count of incidents (related tickets) for the project
        return obj.incidents.count()
    
    def validate_name(self, value):
        # Normalize value to lowercase to ensure consistency in storage
        normalized_value = value.lower()
        if Project.objects.filter(
            name__iexact=normalized_value).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError('Project with this name already exists')
        return normalized_value


class UserDetailSerializer(ModelSerializer):
    
    contributed_projects = ProjectSerializer(many=True, read_only=True)

    class Meta: 
        model = User
        fields = '__all__' 


class TicketDetailSerializer(ModelSerializer):

    affected_user = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'affected_user', 'assigned_to', 'title', 'details', 'project', 'created_at']


class TicketSerializer(ModelSerializer):

    class Meta:
        model = Ticket
        fields = ['id', 'title']


class CommentSerializer(ModelSerializer):

    contributor = UserSerializer(read_only=True)
    parent_ticket = TicketSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'contributor', 'text', 'parent_ticket', 'created_at']
