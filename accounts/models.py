from django.db import models
from django.contrib.auth.models import User

# One turker - one poll assignment
class TurkerAssignment(models.Model):
  user = models.ForeignKey(User)

  worker_id = models.CharField(max_length=40)
  hit_id = models.CharField(max_length=40)
  assignment_id = models.CharField(max_length=40)

  def __unicode__(self):
    return "%s -> %s" % (self.user.username, self.hit_id)
