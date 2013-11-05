from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count
import random

from boto.mturk.connection import MTurkConnection
from django.conf import settings
import mturk

N_QUESTIONS_PER_DATA_ENTRY_REQUIRED = 3

class Hit(models.Model):
  hit_id = models.CharField(max_length=32, blank=True, null=True)
  hit_url = models.URLField(blank=True, null=True)
  
  def __unicode__(self):
    if self.hit_id:
      return self.hit_url
    else:
      return "Unasigned HIT"

  class Meta:
    verbose_name = "HIT"
    verbose_name_plural = "HITs"

  def save(self, *args, **kwargs):
    if self.pk is None:
      hit = mturk.create_disambig_hit()
      self.hit_id = hit.HITId
      self.hit_url = mturk.get_hit_url(hit)
    super(Hit, self).save(*args, **kwargs)

class UserAnswer(models.Model):
  user = models.ForeignKey(User)
  question_data = models.ForeignKey('DisambigPollData')
  answer = models.CharField(max_length=16)

  def __unicode__(self):
    return "%s replied %s to %s" % (self.user.username, self.answer, unicode(self.question_data))

class DisambigPollDataManager(models.Manager):
  def get_poll_data_for_user(self, user):
    # get a set of user answers that have been answered but less than N_QUESTIONS_PER_DATA_ENTRY_REQUIRED
    user_answers = UserAnswer.objects.annotate(n_questions=Count('question_data')).filter(
      n_questions__lt=N_QUESTIONS_PER_DATA_ENTRY_REQUIRED
    ).exclude(user=user)
    if user_answers:
      # pick a random one from them
      index = random.randint(0, user_answers.count() - 1)
      return user_answers[index].question_data
    else:
      # all questions envolved got enough answers, picking question randomly until fits
      while True:
        question = self.get_random()
        # check if this question has been answered by this user
        if not UserAnswer.objects.filter(question_data=question):
          break
      return question

  def get_random(self):
    n_rows = DisambigPollData.objects.count()
    index = random.randint(1, n_rows)
    return DisambigPollData.objects.get(id=index)

  def save_answer_by_user(self, user, question_data, answer):
    UserAnswer.objects.create(user=user, question_data=question_data, answer=answer)

class DisambigPollData(models.Model):
  unit_id = models.CharField(max_length=20)
  text = models.CharField(max_length=32)
  groups = models.CharField(max_length=16)
  offset = models.PositiveSmallIntegerField()
  length = models.PositiveSmallIntegerField()
  unit_text = models.TextField()
  corpus = models.CharField(max_length=10)

  objects = DisambigPollDataManager()

  def __unicode__(self):
    return "%s @ %s, %s, %s (%s)" % (self.text, self.unit_id, str(self.offset), str(self.length), self.corpus)

class UserState(models.Model):
  user = models.ForeignKey(User)
  state = models.PositiveSmallIntegerField()

  pending_question_data = models.ForeignKey(DisambigPollData, blank=True, null=True)

  def __unicode__(self):
    if self.state:
      return "%s has state %s" % (self.user.username, self.state)
    else:
      return "%s has been asked question %s" % (self.user.username, str(self.pending_question_id))
