from django.db import models
from django.contrib.auth.models import User
import random

N_QUESTIONS_PER_DATA_REQUIRED = 3

class UserAnswer(models.Model):
  user = models.ForeignKey(User)
  question_data = models.ForeignKey('DisambigPollData')
  answer = models.CharField(max_length=16)

  def __unicode__(self):
    return "%s replied %s to %s" % (self.user.username, self.answer, unicode(self.question_data))

''' Questions with 0 < answers < N_QUESTIONS_PER_DATA_REQUIRED - pending ones
'''
class PollDataInProgress(models.Model):
  data = models.ForeignKey('DisambigPollData')

''' Questions with answers = N_QUESTIONS_PER_DATA_REQUIRED - complete ones
'''
class PollDataComplete(models.Model):
  data = models.ForeignKey('DisambigPollData')

class DisambigPollDataManager(models.Manager):
  def get_poll_data_for_user(self, user):
    # By far, it only returns random data entry that user hasn't seen
    seen_ids = user.useranswer_set.values_list('question_data__id', flat=True)
    unseen_poll_data = DisambigPollData.objects.exclude(id__in=seen_ids)
    index = random.randint(1, unseen_poll_data.count()) - 1
    return unseen_poll_data[index]

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
