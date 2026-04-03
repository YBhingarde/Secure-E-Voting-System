from django.contrib import admin
from .models import VoterProfile, Candidate, Vote

# add feature for admin panel
admin.site.register(VoterProfile)
admin.site.register(Candidate)
admin.site.register(Vote)