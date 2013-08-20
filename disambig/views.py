from django.http import HttpResponse, Http404
from models import UserState, DisambigPollData, UserAnswer
import json
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict

N_QUESTIONS = 2

INITIAL_QUESTION = {
  'state' : 1,
  'text' : """<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.
           Suspendisse pellentesque vulputate magna, ac blandit diam suscipit
           sit amet. Etiam bibendum turpis vitae lorem eleifend, non dapibus 
           enim tincidunt. Vivamus sollicitudin, tellus eu ultrices cursus, 
           viverra ut elit. Sed non cursus turpis, ac rhoncus erat. Etiam elementum
           laoreet nunc, a posuere lorem egestas non. Fusce volutpat eget nulla at blandit.
           Sed gravida eu lacus a pharetra. Nam sed adipiscing orci, eu accumsan 
           turpis. Aenean vestibulum ultricies ornare.</p>
           <p>Do you agree with Terms of Use?</p>""",
  'options' : "Yes|No",
  'allow_multiple' : False,
  'allow_empty' : False
}

""" Send emtpy answers to get current state
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
          else:
            if user_state_data.state < N_QUESTIONS + 2:
              UserAnswer.objects.create(
                user=request.user, 
                question_data=user_state_data.pending_question_data,
                answer=request.POST['answer']
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
        else:
          poll_data = DisambigPollData.objects.get_poll_data_for_user(request.user)  
          user_state.pending_question_data = poll_data
          user_state.save()

        reply = {
         'instance' : model_to_dict(poll_data),
         'state' : user_state.state
        }
      else:
        reply = {
          'finish' : True,
        }

  else:
    reply = { 'error' : "noauth" }

  return HttpResponse(json.dumps(reply, ensure_ascii=False), content_type='application/json')
