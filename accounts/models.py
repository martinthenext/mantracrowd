from django.db import models
from django.contrib.auth.models import User

# One turker - one poll assignment
class TurkerAssignment(models.Model):
  user = models.ForeignKey(User)

  worker_id = models.CharField(max_length=40)
  hit_id = models.CharField(max_length=40)
  assigment_id = models.CharField(max_length=40)