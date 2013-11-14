from django.conf import settings
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.middleware import csrf
import json
from django.contrib.auth.models import User

@csrf_protect
def login_view(request):
    if request.method == "GET":
        response = HttpResponse(json.dumps({'username':request.user.username}), mimetype='application/json')
        response.set_cookie(settings.CSRF_COOKIE_NAME, csrf.get_token(request))
        return response
    try:
        username = request.POST['login']
        password = request.POST['pwd']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                reply = {'username': request.user.username}
            else:
                reply = {'error' : 'Your registration is not yet confirmed'}
        else:
            reply = {'error' : 'Wrong login/password'}
    except KeyError:
        reply = {'error' : 'Login data malformed'} 

    return HttpResponse(json.dumps(reply), mimetype='application/json')

@csrf_protect
def login_turker(request):
    if request.method == "GET":
        result = {'status':'GET'}
    if request.method == "POST":
        if 'worker_id' not in request.POST:
            result = {'status' : 'error'}
        else:
            worker_id = request.POST['worker_id']
            turker_name = 'turker#' + worker_id
            if not User.objects.filter(username=turker_name):
                result = {'status' : 'created and logged in'}
                user = User(username=turker_name, is_active=True)
                user.set_password('turker')
                user.save()
            else:
                result = {'status' : 'logged in'}
            turker_user = authenticate(username=turker_name, password='turker')
            login(request, turker_user)

    return HttpResponse(json.dumps(result), mimetype='application/json')
    
        

def logout_view(request):
    if request.method == "POST":
        raise Http404
    logout(request)
    if request.is_ajax():
        return HttpResponse(json.dumps({'success' : True}), mimetype='application/json')
    else:
        return HttpResponseRedirect('/')
    
@csrf_protect
def register_view(request):
    if request.user.is_authenticated():
        return HttpResponse('You\'re already registered as %s' % request.user.username)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            new_user.is_active = False
            new_user.save()
            return HttpResponse('Your registration request has been sent.')
    else:
        form = UserCreationForm()
        
    return render_to_response('form.html', { 'form' : form , 'title' : 'User registration'},
                               context_instance=RequestContext(request) )
