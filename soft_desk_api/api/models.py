"Third-party imports (Django)"
from django.db import models
from django.core.validators import MinValueValidator

class User(models.Model):
    "A model representing a user in the system."
    name = models.fields.CharField(max_length=50)
    age = models.IntegerField(validators=[MinValueValidator(15)])

    contact_preference = models.BooleanField(default=False,
        help_text="Check if the user agrees to be contacted")

    data_sharing = models.BooleanField(default=False,
        help_text="Check if the user agrees to share their data")


    def __str__(self):
        return f"User ID: {self.id} - Name: {self.name}"


class Project(models.Model):
    "A model representing a Project in the system."

    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_projects')
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000)
    contributor = models.ManyToManyField(User, blank=True, related_name='contributed_projects',
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
            if not self in user.contributed_projects.all():
                user.projects.add(self)


    def __str__(self):
        return self.name


class Ticket(models.Model):
    "A model representing a Project in the system."

    affected_user = models.ForeignKey("User", on_delete=models.CASCADE)
    assigned_to = models.ForeignKey("User", on_delete=models.SET_NULL, null=True,
                                    related_name="assigned_to")
    title = models.CharField(max_length=200)
    details = models.CharField(max_length=2000)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='incidents')
    created_at = models.DateTimeField(auto_now_add=True)


    HIGH = 'High Priority'
    MID = 'Midume Priority'
    LOW = 'Low Priority'

    PROGRESS = 'In Progress'
    HOLD = 'On Hold'
    RESOLVED = 'Resolved'

    BUG = 'Bug ticket'
    TASK = 'TASK ticket'
    IMPROVEMENT = 'Improvement ticket'

    ticket_priority = [
        (HIGH, 'High Priority'),
        (MID, 'Midume Priority'),
        (LOW, 'Low Priority'),
    ]

    ticket_current_status = [
        (PROGRESS, 'In Progress'),
        (HOLD, 'On Hold'),
        (RESOLVED, 'Resolved')
    ]
    ticket_type_choices = [
        (BUG, 'Bug'),
        (TASK, 'Task'),
        (IMPROVEMENT, 'Improvement Ticket')
    ]

    priority = models.CharField(
        max_length=20,
        choices=ticket_priority,
        default=LOW
    )
    ticket_type = models.CharField(
        max_length=50,
        choices=ticket_type_choices,
        default=TASK
    )
    status = models.CharField(
        max_length=40,
        choices=ticket_current_status,
        default=PROGRESS
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    "A model representing a Comment in the system."

    contributor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    contributor_name = models.CharField(max_length=200, blank=True, null=True, editable=False)
    text = models.CharField(max_length=500)
    parent_ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.contributor_name and self.contributor:
            self.contributor_name = self.contributor.name

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Comment by {self.contributor_name if self.contributor_name else 'Unknown'}"
    