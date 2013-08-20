from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
import json

def login_view(request):
    if request.method == "GET":
        return HttpResponse(json.dumps({'username':request.user.username}), mimetype='application/json')
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
