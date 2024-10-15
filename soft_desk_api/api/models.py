# Importing the uuid module to generate universally unique identifiers
import uuid
# Importing AbstractUser from Django's authentication system to extend the default user model
from django.contrib.auth.models import AbstractUser, BaseUserManager
# Importing models from Django to define custom model fields
from django.db import models


# Custom user manager
class CustomUserManager(BaseUserManager):
    
    def create_user(self, username, password=None, **extra_fields):
        # Check if username is provided
        if not username:
            raise ValueError('The Username field must be set')
        # Check if password is provided
        if not password:
            raise ValueError('The Password field must be set')
        # Ensure that age is provided for normal users
        if 'age' not in extra_fields or extra_fields['age'] is None:
            raise ValueError('The Age field must be set for normal users')
        # Create the user instance with the provided username and extra fields
        user = self.model(username=username, **extra_fields)
        # Set and hash the user's password
        user.set_password(password)
        # Save the user instance to the database
        user.save(using=self._db)
        # Return the created user instance
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        # Set default values for superuser fields if not provided
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        # For superusers, allow age to be optional
        if 'age' not in extra_fields:
            extra_fields['age'] = 20  # Age can be is 20 for superusers

        # Ensure that is_staff and is_superuser are set to True for superuser
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        # Call create_user method to create the superuser
        return self.create_user(username, password, **extra_fields)
     

class User(AbstractUser):
    # Custom user model extending AbstractUser
    # Age field to store the user's age
    age = models.IntegerField()
    # Boolean field indicating if the user is active
    is_active = models.BooleanField(default=True)
    # Boolean field for user's contact preference
    contact_preference = models.BooleanField(default=False, 
        help_text="Check if the user agrees to be contacted")
    # Boolean field for data sharing preference
    data_sharing = models.BooleanField(default=False,
        help_text="Check if the user agrees to share their data")
    # String representation of the user instance
    def __str__(self):
        return f"User ID: {self.id} - Username: {self.username}"


class Project(models.Model):
    # Custom model representing a project in the system
    # Foreign key to the User model for the project creator
    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_project')
    # Name of the project with a maximum length of 200 characters
    name = models.CharField(max_length=200)
    # Description of the project with a maximum length of 1000 characters
    description = models.TextField(max_length=1000)
    # Many-to-many relationship for contributors to the project
    contributor = models.ManyToManyField(User, blank=True, related_name='contributed_project',
        verbose_name="Users registered to this project")
    # Date and time when the project was created
    created_at = models.DateTimeField(auto_now_add=True)
    # Defining constants for different project types
    BACKEND = 'Backend Project'
    FRONTEND = 'Frontend Project'
    IOS = 'IOS Project'
    ANDROID = 'Android Project'
    # Choices for the type of project
    project_type = [
        (BACKEND, 'Backend Project'),
        (FRONTEND, 'Frontend Project'),
        (IOS, 'IOS Project'),
        (ANDROID, 'Android Project')
    ]
    # CharField to specify the type of project
    type = models.CharField(
        max_length=100,
        choices=project_type
    )
    # Overriding the save method to add contributors to the project
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for user in self.contributor.all():
            if not self in user.contributed_project.all():
                user.projects.add(self)
    # String representation of the project instance
    def __str__(self):
        return self.name


class Ticket(models.Model):
    # Defining relationships for the Ticket model
    # Foreign key relationship to the User model representing the affected user
    affected_user = models.ForeignKey("User", on_delete=models.CASCADE)
    # Foreign key relationship to the Project model representing the project the ticket is related to
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='incidents')
    # Foreign key relationship to the User model for the assigned user handling the ticket
    assigned_to = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_tickets",
        default=None
    )
    # Defining fields for the Ticket model
    # Title of the ticket with a maximum length of 200 characters
    title = models.CharField(max_length=200)
    # Detailed description of the ticket with a maximum length of 2000 characters
    details = models.CharField(max_length=2000)
    # Date and time when the ticket was created
    created_at = models.DateTimeField(auto_now_add=True)
    # Defining constants for priority choices
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    # Defining constants for status choices
    IN_PROGRESS = 'in_progress'
    ON_HOLD = 'on_hold'
    RESOLVED = 'resolved'
    # Defining constants for ticket type choices
    BUG = 'bug'
    TASK = 'task'
    IMPROVEMENT = 'improvement'
    # Defining choice options for priority, status, and ticket type
    # Priority choices as tuples
    PRIORITY_CHOICES = [
        (HIGH, 'High Priority'),
        (MEDIUM, 'Medium Priority'),
        (LOW, 'Low Priority'),
    ]
    # Status choices as tuples
    STATUS_CHOICES = [
        (IN_PROGRESS, 'In Progress'),
        (ON_HOLD, 'On Hold'),
        (RESOLVED, 'Resolved'),
    ]
    # Ticket type choices as tuples
    TICKET_TYPE_CHOICES = [
        (BUG, 'Bug'),
        (TASK, 'Task'),
        (IMPROVEMENT, 'Improvement Ticket'),
    ]
    # Field for specifying the priority of the ticket
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=LOW
    )
    # Field for specifying the status of the ticket
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=IN_PROGRESS
    )
    # Field for specifying the type of the ticket
    ticket_type = models.CharField(
        max_length=20,
        choices=TICKET_TYPE_CHOICES,
        default=TASK
    )
    # String representation of the ticket instance
    def __str__(self):
        return self.title


class Comment(models.Model):
    # Model representing a comment in the system
    # Unique identifier for each comment, using UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Foreign key relationship to the User model for the commenter
    commenter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # Username of the commenter, stored as a separate field
    commenter_username = models.CharField(max_length=200, blank=True, null=True, editable=False)
    # Text content of the comment, with a maximum length of 500 characters
    text = models.CharField(max_length=500)
    # Foreign key relationship to the Ticket model for the parent ticket of the comment
    parent_ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE, related_name='comments')
    # Date and time when the comment was created
    created_at = models.DateTimeField(auto_now_add=True)
    # Foreign key relationship to the Project model for the project related to the comment
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    # Overriding the save method to populate the commenter_username if not already set
    def save(self, *args, **kwargs):
        if not self.commenter_username and self.commenter:
            self.commenter_username = self.commenter.username

        super().save(*args, **kwargs)
    # String representation of the comment instance
    def __str__(self):
        return f"Comment by {self.commenter_username if self.commenter_username else 'Unknown'}"
    