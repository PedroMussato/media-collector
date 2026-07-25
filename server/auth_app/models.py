from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.
class ResetPasswordToken(models.Model):
    user_fk = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

class AuthenticationActions(models.Model):
    login_info = models.CharField(max_length=256)
    authentication_type = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=256)
    success = models.BooleanField()


