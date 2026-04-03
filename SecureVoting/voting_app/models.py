from django.db import models

class VoterProfile(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=10, unique=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=100)  
    has_voted = models.BooleanField(default=False) 
    
    def __str__(self):
        return self.username
    
class Candidate(models.Model):
    name   = models.CharField(max_length=100)
    party  = models.CharField(max_length=100)
    symbol = models.ImageField(upload_to='candidates/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.party})"
    
class Vote(models.Model):
    user = models.OneToOneField(VoterProfile, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    aadhaar_entered = models.CharField(max_length=12, unique=True) 
    phone_confirmed = models.CharField(max_length=10)
    photo = models.ImageField(upload_to='voter_photos/')
    face_phash = models.CharField(max_length=128, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.candidate.name}"