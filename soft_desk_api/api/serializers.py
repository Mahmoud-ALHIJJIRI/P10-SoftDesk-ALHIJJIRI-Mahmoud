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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        # If it's a PUT request, set fields to required
        if request and request.method == 'PUT':
            self.fields['username'].required = True
            self.fields['first_name'].required = True
            self.fields['last_name'].required = True
            self.fields['email'].required = True
            self.fields['age'].required = True
            self.fields['contact_preference'].required = True
            self.fields['data_sharing'].required = True

    def validate(self, data):
        # Check if data_sharing is True and the user is under 16 years old
        if data.get('data_sharing') and data.get('age') < 16:
            raise serializers.ValidationError("Users must be at least 16 years old to share data.")
        return data


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
        
    def to_internal_value(self, data):
    # Iterate through each field in the serializer
        for field_name, field in self.fields.items():
            # Check if the field has choices and if it's in the incoming data
            if hasattr(field, 'choices') and field_name in data:
                # Get the valid choices for this field
                valid_choices = [str(choice) for choice in field.choices.keys()]   
                # Check if the provided value is not one of the valid choices
                if str(data[field_name]) not in valid_choices:
                    # Clear any previously validated data and raise a validation error
                    raise serializers.ValidationError({
                        field_name: [
                            (
                                f"\"{data[field_name]}\" is not a valid choice. "
                                f"Valid choices are: {', '.join(valid_choices)}."
                            )
                        ]
                    })
        # Call the parent method to continue processing other fields
        return super().to_internal_value(data)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        # If it's a PUT request, set fields to required
        if request and request.method == 'PUT':
            self.fields['priority'].required = True
            self.fields['status'].required = True
            self.fields['ticket_type'].required = True
            self.fields['assigned_to'].required = True

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
