from django.contrib import admin
from .models import User, Ticket, Project, Comment



class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'age',) 
    search_fields = ('name',) 


class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'ticket_type', 'priority', 'created_at')
    list_filter = ('status', 'project', 'ticket_type','priority')
    search_fields = ('name',)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'creator', 'created_at')
    list_filter = ('creator', 'type')
    search_fields = ('name',)
    filter_vertical = ('contributor',)
    

class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'contributor', 'parent_ticket', 'created_at')

# Register the User model with the custom admin class
admin.site.register(User, UserAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Comment, CommentAdmin)