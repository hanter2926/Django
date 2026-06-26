from django.contrib import admin
from .models import Announcement
from .models import TeamMember
from .models import Gallery


admin.site.register(Announcement)
admin.site.register(TeamMember)
admin.site.register(Gallery)
