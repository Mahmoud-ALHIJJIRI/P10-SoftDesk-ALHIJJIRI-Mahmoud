from django.contrib import admin
from .models import User, Ticket, Project, Comment
from django.contrib.auth.hashers import make_password




class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'contributor', 'parent_ticket', 'created_at')


class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'ticket_type', 'priority', 'created_at')
    list_filter = ('status', 'project', 'ticket_type','priority')
    search_fields = ('name',)


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'age',) 
    search_fields = ('username',)

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('password') and not obj.password.startswith('pbkdf2_sha256'):
            # Hash the password if it's not already hashed
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)   

    exclude = ('last_login', 'groups', 'user_permissions',)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'creator', 'created_at')
    list_filter = ('creator', 'type')
    search_fields = ('name',)
    filter_vertical = ('contributor',)
    

# Register the User model with the custom admin class
admin.site.register(Comment, CommentAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(User, UserAdmin)