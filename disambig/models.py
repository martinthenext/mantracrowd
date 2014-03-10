from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count
import random
import itertools

from django.conf import settings
import mturk
from accounts.models import TurkerAssignment

N_ANSWERS_PER_DATA_ENTRY_REQUIRED = 3
N_QUESTIONS = 20
N_TEST_QUESTIONS = 2

FIRST_QUESTION_STATE = 2
FINAL_STATE = N_QUESTIONS + FIRST_QUESTION_STATE

GROUP_NAMES = [
 'ACTI', 'ANAT', 'CHEM', 'DEVI',
 'DISO', 'GENE', 'GEOG', 'LIVB', 
 'OCCU', 'ORGA', 'PHYS', 'PROC',
 'PHEN', 'OBJC'
 ]

OPTION_NAMES = GROUP_NAMES + ['IDK', 'None']

INITIAL_QUESTION = {
  'state' : 1,
  'text' : """

  <h1>Disambiguation survey</h1>
  
  <p>In this survey you will be given a small portion of text with 
  word highlighted. For the highlighted word choose the category of 
  terms this word belongs to.</p>
  
  <p class='collapse_btn'><u>More details</u></p>

  <div class='collapsable'>
  
  <p>This poll is a crowd sourcing approach for the disambiguation
  of concepts that have been identified from the biomedical literature.
  All concepts have been assigned semantic types according to UMLS (see below).
  For some concepts the automatic assignment has produced two or three different results.</p>
  <p>We ask users to chose the correct semantic
  type for the given term by working through a predefined number of
  questions. As alternative you may indicate that it is not possible
  to assign the correct type ("I don't know" or "None of the above").</p>
  
  <h3>What is the UMLS?</h3>
  
  <p>The <a href="http://www.nlm.nih.gov/research/umls">UMLS</a>,
  or Unified Medical Language System, is a set of files and software
  that brings together many health and biomedical vocabularies and
  standards to enable interoperability between computer systems.
  </p>
  <h3>Links</h3>
  <p><a href="http://www.nlm.nih.gov/research/umls/quickstart.html">UMLS Quick Start Guide</a></p>
  <p>Full list of <a href="http://semanticnetwork.nlm.nih.gov/SemGroups/SemGroups.txt">semantic groups</a>.</p>

  </div>

  <p>Please do the assignment as thoroughly as you can.</p>
  <p>Proceed to survey?</p>

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
  '''
  >>>u = User.objects.all()[0]
  >>>UserAnswer.objects.filter(question_data=DisambigPollData.objects.get_poll_data_for_user(u)).count()
  if there are questions unsanswered fully should be 1 or 2
  '''
  def get_poll_data_for_user(self, user):
    # get a set of answers by OTHER users 
    # but less than N_ANSWERS_PER_DATA_ENTRY_REQUIRED times
    user_answers = UserAnswer.objects \
      .exclude(user=user) \
      .values('question_data').annotate(n_questions=Count('question_data')) \
      .filter(n_questions__lt=N_ANSWERS_PER_DATA_ENTRY_REQUIRED)
    # exclude answers to the questions that USER answered (not his answers though)
    seen_ids = user.useranswer_set.values_list('question_data__id', flat=True)
    to_choose_from = user_answers.exclude(question_data__id__in=seen_ids)
    if to_choose_from:
      # pick a random one from them
      index = random.randint(0, to_choose_from.count() - 1)
      chosen_id = to_choose_from[index]['question_data']
      return DisambigPollData.objects.get(id=chosen_id)
    else:
      # all questions envolved got enough answers, picking question randomly until unanswered found
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
      mturk.finalize_assignment(turker_assignment[0].assignment_id, True)

  def is_user_assignment_complete(self, user):
    return user.userstate_set.all()[0].state == FINAL_STATE

  # get unique data entries that has been answered sorted by ID of answer 
  def get_answered_question_data(self):
    return DisambigPollData.objects.filter(useranswer__id__isnull=False).annotate(n=Count('id')).order_by('-useranswer')

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

  def get_highlighted_repr(self):
    begin_highlight = int(self.offset)
    end_highlight = int(self.offset) + int(self.length)

    slice_one = self.unit_text[:begin_highlight]
    slice_two = self.unit_text[begin_highlight:end_highlight]
    slice_three = self.unit_text[end_highlight:]

    return "%s[[%s]]%s" % (slice_one, slice_two, slice_three)

  def get_answer_stats(self):
    answers = [row['answer'] for row in self.useranswer_set.values('answer')]
    grouped = [(answer_type, answers.count(answer_type)) for answer_type in set(answers)]
    return sorted(grouped, key=lambda (x,y) : y, reverse=True)

class UserState(models.Model):
  user = models.ForeignKey(User)
  state = models.PositiveSmallIntegerField()

  pending_question_data = models.ForeignKey(DisambigPollData, blank=True, null=True)

  def __unicode__(self):
    if self.state:
      return "%s has state %s" % (self.user.username, self.state)
    else:
      return "%s has been asked question %s" % (self.user.username, str(self.pending_question_id))

''' 

Instances of this class get created on state 2 to indicate
states to ask test questions on, see assign_test_questions()

Answers are filled in later

'''
class TestQuestionUserAnswer(models.Model):
  user = models.ForeignKey(User)
  test_question = models.ForeignKey('TestQuestion')
  answer = models.CharField(max_length=16, blank=True, null=True)
  state = models.PositiveSmallIntegerField()

  def __unicode__(self):
    if self.answer:
      return "%s answered %s to %s" % (self.user.username, self.answer, self.test_question.unit_text)
    else:
      return "%s on state %s has to answer [[%s]]" % (self.user.username, self.state, self.test_question.unit_text)

class TestQuestionManager(models.Manager):
  ''' Create <N_TEST_QUESTIONS> TestQuestionUserAnswer instances with random states
      and random test questions for the user
  '''
  def assign_test_questions(self, user):
    test_question_states = random.sample(range(FIRST_QUESTION_STATE, FINAL_STATE), N_TEST_QUESTIONS)
    test_questions = self.get_random(N_TEST_QUESTIONS)
    for state, question in itertools.izip(test_question_states, test_questions):
      TestQuestionUserAnswer.objects.create(user=user, test_question=question, state=state)

  def get_random(self, k=1):
    n_rows = self.model.objects.count()
    indices = random.sample(range(1, n_rows), k)
    all_questions = self.model.objects.all()
    return [all_questions[i] for i in indices]

  def get_answered_question_data(self):
    return self.model.objects.filter(testquestionuseranswer__id__isnull=False).order_by('-testquestionuseranswer')

class TestQuestion(models.Model):
  unit_text = models.TextField()
  text = models.CharField(max_length=32)
  offset = models.PositiveSmallIntegerField()
  length = models.PositiveSmallIntegerField()
  groups = models.CharField(max_length=16)
  correct_group = models.CharField(max_length=8)

  objects = TestQuestionManager()

  def __unicode__(self):
    return self.get_highlighted_repr() + '->' + self.correct_group

  def get_highlighted_repr(self):
    begin_highlight = int(self.offset)
    end_highlight = int(self.offset) + int(self.length)

    slice_one = self.unit_text[:begin_highlight]
    slice_two = self.unit_text[begin_highlight:end_highlight]
    slice_three = self.unit_text[end_highlight:]

    return "%s[[%s]]%s" % (slice_one, slice_two, slice_three)

  def get_fake_poll_data_dict(self):
    return {
      'unit_text' : self.unit_text,
      'text' : self.text,
      'unit_id' : "d5245412.u1",
      'length' : self.length,
      'groups' : self.groups,
      'offset' : self.offset,
      'corpus' : "EMEA",
      "id" : 239888
    }

  def get_answer_stats(self):
    answers = [row['answer'] for row in self.testquestionuseranswer_set.values('answer')]
    grouped = [(answer_type, answers.count(answer_type)) for answer_type in set(answers)]
    return sorted(grouped, key=lambda (x,y) : y, reverse=True)
