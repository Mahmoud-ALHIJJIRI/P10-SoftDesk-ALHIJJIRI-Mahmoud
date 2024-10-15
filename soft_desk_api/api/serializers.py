# Importing necessary serializer classes from Django Rest Framework
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
# Importing models to be used in the serializers
from .models import User, Project, Ticket, Comment


# Serializer for User model with basic fields
class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username']


# Serializer for Project model with basic fields
class ProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']


# Detailed serializer for Project model
class ProjectDetailSerializer(ModelSerializer):
    # Contributor field using PrimaryKeyRelatedField for adding contributors to the project
    contributor = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())

    # Custom field to show the number of incidents related to the project
    incidents_count = serializers.SerializerMethodField()

    # Read-only field for the creator of the project
    creator = serializers.PrimaryKeyRelatedField(read_only=True)

    # Serializer to include creator's detailed information
    creator_detail = UserSerializer(read_only=True, source='creator')

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'creator', 'creator_detail', 'description', 'type', 
            'created_at', 'incidents_count', 'contributor'
        ]

    # Override to_internal_value method to validate custom fields
    def to_internal_value(self, data):
        for field_name, field in self.fields.items():
            if field_name == 'contributor':
                continue
            if hasattr(field, 'choices') and field_name in data:
                valid_choices = [str(choice) for choice in field.choices.keys()]
                if str(data[field_name]) not in valid_choices:
                    raise serializers.ValidationError({
                        field_name: [
                            (
                                f"\"{data[field_name]}\" is not a valid choice. "
                                f"Valid choices are: {', '.join(valid_choices)}."
                            )
                        ]
                    })
        return super().to_internal_value(data)

    # Method to get the count of incidents related to the project
    def get_incidents_count(self, obj):
        return obj.incidents.count()

    # Validate the uniqueness of the project name
    def validate_name(self, value):
        normalized_value = value.lower()
        if Project.objects.filter(name__iexact=normalized_value).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError('Project with this name already exists')
        return normalized_value

    # Custom update method to handle contributors separately
    def update(self, instance, validated_data):
        new_contributors = validated_data.pop('contributor', [])
        for contributor in new_contributors:
            if contributor not in instance.contributor.all():
                instance.contributor.add(contributor)
        return super().update(instance, validated_data)


# Detailed serializer for User model with additional fields and related projects
class UserDetailSerializer(ModelSerializer):
    # Serializer for projects the user has contributed to
    contributed_project = ProjectSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'age', 'date_joined', 
            'last_login', 'is_active', 'is_staff', 'is_superuser', 'contact_preference', 
            'data_sharing', 'contributed_project'
        ]
        read_only_fields = ['is_active']

    # Custom initialization to set fields as required for PUT requests
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'PUT':
            self.fields['username'].required = True
            self.fields['first_name'].required = True
            self.fields['last_name'].required = True
            self.fields['email'].required = True
            self.fields['age'].required = True
            self.fields['contact_preference'].required = True
            self.fields['data_sharing'].required = True

    # Custom validation to ensure age requirements for data sharing
    def validate(self, data):
        user_instance = self.instance
        if 'age' in data:
            age = data['age']
        else:
            age = user_instance.age if user_instance and user_instance.age is not None else None
        # Raise an error if age is still None (meaning it wasn't provided)
        if age is None:
            raise serializers.ValidationError("The age must be provided.")

        if age is not None and data.get('data_sharing') and age < 16:
            raise serializers.ValidationError("Users must be at least 16 years old to share data.")
        return data


# Detailed serializer for Ticket model with additional fields
class TicketDetailSerializer(ModelSerializer):
    # Serializer for affected user and assigned user with read-only access
    affected_user = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'affected_user', 'assigned_to', 'title', 'details', 'project', 
            'created_at', 'priority', 'status', 'ticket_type'
        ]
    # Override to_internal_value method to validate custom fields
    def to_internal_value(self, data):
        for field_name, field in self.fields.items():
            if hasattr(field, 'choices') and field_name in data:
                valid_choices = [str(choice) for choice in field.choices.keys()]
                if str(data[field_name]) not in valid_choices:
                    raise serializers.ValidationError({
                        field_name: [
                            (
                                f"\"{data[field_name]}\" is not a valid choice. "
                                f"Valid choices are: {', '.join(valid_choices)}."
                            )
                        ]
                    })
        return super().to_internal_value(data)

    # Custom initialization to set fields as required for PUT requests
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'PUT':
            self.fields['priority'].required = True
            self.fields['status'].required = True
            self.fields['ticket_type'].required = True
            self.fields['assigned_to'].required = True


# Serializer for Ticket model with basic fields
class TicketSerializer(ModelSerializer):

    class Meta:
        model = Ticket
        fields = ['id', 'title']


# Serializer for Comment model with related user, ticket, and project information
class CommentSerializer(ModelSerializer):
    # Serializer for the user who made the comment, the ticket, and the project
    commenter = UserSerializer(read_only=True)
    parent_ticket = TicketSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'text', 'commenter', 'parent_ticket', 'project', 'created_at']
