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
    
    contributor = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), write_only=True)
    # For reading contributor details (with full user information)
    contributors = UserSerializer(many=True, read_only=True, source='contributor')    
    incidents_count = serializers.SerializerMethodField()  # Custom field to show only the number of incidents
    creator = serializers.PrimaryKeyRelatedField(read_only=True)
    creator_detail = UserSerializer(read_only=True, source='creator')

    class Meta:
        model = Project
        fields = ['id', 
                  'name', 
                  'creator', 
                  'creator_detail', 
                  'description', 
                  'type', 
                  'created_at', 
                  'incidents_count', 
                  'contributor', 
                  'contributors']


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
    
    def update(self, instance, validated_data):
        # Handle contributors separately to avoid overwriting
        new_contributors = validated_data.pop('contributor', [])

        # For each contributor in the new list, add them if not already a contributor
        for contributor in new_contributors:
            if contributor not in instance.contributor.all():
                instance.contributor.add(contributor)  # Append new contributors

        # Call the default update method for other fields
        return super().update(instance, validated_data)


class UserDetailSerializer(ModelSerializer):
    
    contributed_project = ProjectSerializer(many=True, read_only=True)

    class Meta: 
        model = User
        fields = fields = [
            'id', 
            'username', 
            'first_name', 
            'last_name', 
            'email', 
            'age', 
            'date_joined', 
            'last_login',
            'is_active', 
            'is_staff', 
            'is_superuser', 
            'contact_preference', 
            'data_sharing', 
            'contributed_project', 
        ]
        read_only_fields = ['is_active']  # Ensures that is_active is only read-only


class TicketDetailSerializer(ModelSerializer):

    affected_user = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 
                  'affected_user', 
                  'assigned_to', 
                  'title', 
                  'details', 
                  'project', 
                  'created_at', 
                  'priority',
                  'status',
                  'ticket_type',
                  ]


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
