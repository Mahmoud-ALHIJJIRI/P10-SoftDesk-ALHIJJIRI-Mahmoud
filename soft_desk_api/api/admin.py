# Importing necessary modules for Django admin
from django.contrib import admin
from .models import User, Ticket, Project, Comment
from django.contrib.auth.hashers import make_password

# Custom admin class for managing comments in the admin interface
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'commenter', 'parent_ticket', 'created_at', 'project')

# Custom admin class for managing tickets in the admin interface
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'ticket_type', 'priority', 'created_at')
    list_filter = ('status', 'project', 'ticket_type', 'priority')
    search_fields = ('name',)

# Custom admin class for managing users in the admin interface
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'age')
    search_fields = ('username',)

    # Override save_model to hash password if not already hashed
    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('password') and not obj.password.startswith('pbkdf2_sha256'):
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)

    exclude = ('last_login', 'groups', 'user_permissions')

# Custom admin class for managing projects in the admin interface
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'creator', 'created_at')
    list_filter = ('creator', 'type')
    search_fields = ('name',)
    filter_vertical = ('contributor',)

# Register models with the custom admin classes
admin.site.register(Comment, CommentAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(User, UserAdmin)
