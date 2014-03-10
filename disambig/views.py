from django.http import HttpResponse, Http404
from models import UserState, DisambigPollData, UserAnswer, N_QUESTIONS, INITIAL_QUESTION, TestQuestion, TestQuestionUserAnswer, OPTION_NAMES
from django.contrib.auth.models import User
import json
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.db.models import Count
import itertools

""" 

STATE>          1                2      3   ...   FINAL_STATE - 1     FINAL_STATE

SERVE>  INITIAL_QUESTION         Q      Q   ...         Q               FINISH

"""
def next_question(request):
  if request.user.is_authenticated():
    try:
      user_state_data = UserState.objects.get(user=request.user)
      # write down answer if posted and update UserState
      if request.method=="POST":
        # Check if user is in the state we assume he is
        if user_state_data.state == int(request.POST['state']):
          if user_state_data.state == 1:
            # Check if user agrees to terms and conditions
            if request.POST['answer'] == u'Yes':
              user_state_data.state = 2
              user_state_data.save()
              # Assign test questions to the person
              TestQuestion.objects.assign_test_questions(request.user)
          else:
            if user_state_data.state < N_QUESTIONS + 2:
              # Check if the answer is to a test question
              test_question_answer = TestQuestionUserAnswer.objects.filter(user=request.user, state=user_state_data.state)
              if test_question_answer:
                # TODO test if answers are being written
                test_question_answer[0].answer = request.POST['answer']
                test_question_answer[0].save()
              else:
                DisambigPollData.objects.save_answer_by_user(
                  request.user,
                  user_state_data.pending_question_data,
                  request.POST['answer']
                )
            user_state_data.state = user_state_data.state + 1
            user_state_data.pending_question_data = None
            user_state_data.save()
        else:
          reply =  { 'error' : "Server error. Please reload page (F5)" }
    
    except ObjectDoesNotExist:
      # New user, create UserState
      user_state_data = UserState.objects.create(user=request.user, state=1)

    # get question for UserState

    if user_state_data.state == 1:
      reply = INITIAL_QUESTION
    else:
      if user_state_data.state < N_QUESTIONS + 2:
        # Here we fetch a question from database ### POLL SPECIFIC

        # Check if there is a pending question
        user_state = UserState.objects.get(user=request.user)
        if user_state.pending_question_data:
          poll_data = user_state.pending_question_data
          instance = model_to_dict(poll_data)
        else:
          # Check if we need to ask a test question now
          test_question_answer = TestQuestionUserAnswer.objects.filter(user=request.user, state=user_state_data.state)
          if test_question_answer:
            instance = test_question_answer[0].test_question.get_fake_poll_data_dict()
          else:
            poll_data = DisambigPollData.objects.get_poll_data_for_user(request.user)  
            user_state.pending_question_data = poll_data
            user_state.save()
            instance = model_to_dict(poll_data)

        reply = {
         'instance' : instance,
         'state' : user_state.state
        }
      else:
        reply = {
          'finish' : True,
        }
        # DisambigPollData.objects.finalize_poll(request.user)
        # Accept/reject assignments by hand now that in test mode

  else:
    reply = { 'error' : "noauth" }

  return HttpResponse(json.dumps(reply, ensure_ascii=False), content_type='application/json')

def answers(request):
  if request.user.is_authenticated:
    questions = DisambigPollData.objects.get_answered_question_data()
    reply = {}
    reply['answer_count'] = UserAnswer.objects.count()
    reply['user_count'] = User.objects.count()

    def serialize_question_and_answers(question):
      result = {}
      result['question'] = model_to_dict(q)
      result['answers'] = q.get_answer_stats()
      return result

    reply['questions'] = [serialize_question_and_answers(q) for q in questions]
  else:
    raise Http404

  return HttpResponse(json.dumps(reply, ensure_ascii=False), content_type='application/json')

def answers_csv(request):
  if request.user.is_authenticated():
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="answers.csv"'

    result = 'sep=,\n' + ','.join(OPTION_NAMES) + ',TEXT,CORPUS,UNIT\n'

    questions = DisambigPollData.objects.get_answered_question_data()

    for question in questions:
      answers = dict(question.get_answer_stats())
      options = question.groups.split('|')
      for group_name in OPTION_NAMES:
        if group_name in answers.keys():
          result += str(answers[group_name])
        else:
          if group_name in options:
            result += '0'
          else:
            result += '-'
        result += ','
      result += question.text + ',' + question.corpus + ',' + question.unit_id
      result += '\n'

    response.write(result)
    return response
  else:
    raise Http404

def questions_csv(request):
  if request.user.is_authenticated():
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="questions.csv"'

    result = 'sep=,\n'

    questions = DisambigPollData.objects.get_answered_question_data()
    for question in questions:
      result += str(question.id) + ',' + question.corpus + ',' + question.unit_id + ','
      result += question.get_highlighted_repr() + ',' + question.groups + '|None|IDK\n'

    response.write(result)
    return response
  else:
    raise Http404
