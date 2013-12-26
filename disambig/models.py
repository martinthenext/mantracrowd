from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count
import random

from django.conf import settings
import mturk
from accounts.models import TurkerAssignment

N_QUESTIONS_PER_DATA_ENTRY_REQUIRED = 3
N_QUESTIONS = 20

INITIAL_QUESTION = {
  'state' : 1,
  'text' : """<p>Terms of Use:</p>
  <p>This poll is a crowd sourcing approach for the disambiguation
   of concepts that have been identified from the biomedical literature.
   All concepts have been assigned semantic types. For some concepts the
   automatic assignment has produced two or three different results.</p>
  <p>We ask users of this Web site to chose the correct semantic
   type for the given term by working through a predefined number of
   questions. As alternative you may indicate that it is not possible
   to assign the correct type ("I don't know" or "None of the above").</p>
  <p>Please do the assignment as thoroughly as you can.</p>
  <p>Do you agree with the Terms of Use?</p>
  """,
  'options' : "Yes|No",
  'allow_multiple' : False,
  'allow_empty' : False
}

class Hit(models.Model):
  hit_id = models.CharField(max_length=32, blank=True, null=True)
  hit_url = models.URLField(blank=True, null=True)
  
  def __unicode__(self):
    if self.hit_id:
      return 'HIT#' + self.hit_id
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
    # get a set of user answers that have been answered by OTHER users 
    # but less than N_QUESTIONS_PER_DATA_ENTRY_REQUIRED times
    user_answers = UserAnswer.objects.annotate(n_questions=Count('question_data')).filter(
      n_questions__lt=N_QUESTIONS_PER_DATA_ENTRY_REQUIRED
    ).exclude(user=user)
    # exclude answers to the questions that USER answered
    seen_ids = user.useranswer_set.values_list('question_data__id', flat=True)
    to_chose_from = user_answers.exclude(question_data__id__in=seen_ids)
    if to_chose_from:
      # pick a random one from them
      index = random.randint(0, to_chose_from.count() - 1)
      return to_chose_from[index].question_data
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

  def finalize_poll(self, user):
    turker_assignment = TurkerAssignment.objects.filter(user=user)
    if turker_assignment:
      # Respondent was a turker, decide if we want to pay him and approve/reject assignment
      mturk.finalize_assignment(turker_assignment.assignment_id, True)

  def is_user_assignment_complete(self, user):
    final_state = N_QUESTIONS + 2
    return user.userstate_set.all()[0].state == final_state

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
