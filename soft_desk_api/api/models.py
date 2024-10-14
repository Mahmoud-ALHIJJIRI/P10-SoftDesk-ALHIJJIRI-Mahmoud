"Third-party imports (Django)"
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
  

class User(AbstractUser):
    "A model representing a user in the system."
    age = models.IntegerField(default=18)
    is_active = models.BooleanField(default=True)
    contact_preference = models.BooleanField(default=False, 
        help_text="Check if the user agrees to be contacted")
    data_sharing = models.BooleanField(default=False,
        help_text="Check if the user agrees to share their data")
    
    def __str__(self):
        return f"User ID: {self.id} - Username: {self.username}"


class Project(models.Model):
    "A model representing a Project in the system."

    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_project')
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000)
    contributor = models.ManyToManyField(User, blank=True, related_name='contributed_project',
        verbose_name="Users registered to this project")
    created_at = models.DateTimeField(auto_now_add=True)

    BACKEND = 'Backend Project'
    FRONTEND = 'Frontend Project'
    IOS = 'IOS Project'
    ANDROID = 'Android Project'

    project_type = [
        (BACKEND, 'Backend Project'),
        (FRONTEND, 'Frontend Project'),
        (IOS, 'IOS Project'),
        (ANDROID, 'Android Project')
    ]

    type = models.CharField(
        max_length=100,
        choices=project_type
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for user in self.contributor.all():
            if not self in user.contributed_project.all():
                user.projects.add(self)

    def __str__(self):
        return self.name


class Ticket(models.Model):
    # Relationships
    affected_user = models.ForeignKey("User", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='incidents')
    assigned_to = models.ForeignKey(
        "User", 
        on_delete=models.SET_NULL, 
        null=True,   # Allow the database to store NULL (None in Python)
        related_name="assigned_tickets",
        default=None  # 'assigned_to' is already used as the field name
    )

    # Fields
    title = models.CharField(max_length=200)
    details = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    # Constants for choices
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

    IN_PROGRESS = 'in_progress'
    ON_HOLD = 'on_hold'
    RESOLVED = 'resolved'

    BUG = 'bug'
    TASK = 'task'
    IMPROVEMENT = 'improvement'

    # Choices as tuples
    PRIORITY_CHOICES = [
        (HIGH, 'High Priority'),
        (MEDIUM, 'Medium Priority'),
        (LOW, 'Low Priority'),
    ]

    STATUS_CHOICES = [
        (IN_PROGRESS, 'In Progress'),
        (ON_HOLD, 'On Hold'),
        (RESOLVED, 'Resolved'),
    ]

    TICKET_TYPE_CHOICES = [
        (BUG, 'Bug'),
        (TASK, 'Task'),
        (IMPROVEMENT, 'Improvement Ticket'),
    ]

    # Model fields for choices
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=LOW
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=IN_PROGRESS
    )

    ticket_type = models.CharField(
        max_length=20,
        choices=TICKET_TYPE_CHOICES,
        default=TASK
    )

    def __str__(self):
        return self.title


class Comment(models.Model):
    "A model representing a Comment in the system."
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commenter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    commenter_username = models.CharField(max_length=200, blank=True, null=True, editable=False)
    text = models.CharField(max_length=500)
    parent_ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')


    def save(self, *args, **kwargs):
        if not self.commenter_username and self.commenter:
            self.commenter_username = self.commenter.username

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Comment by {self.commenter_username if self.commenter_username else 'Unknown'}"
    