from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login as lgin, logout as lgout
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import HttpResponseRedirect
from .models import ResetPasswordToken
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from django.http import HttpRequest
from .models import AuthenticationActions
from datetime import datetime, timedelta
from django.conf import settings
import uuid

def get_client_ip(request):
    # Assuming request is an instance of HttpRequest
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def password_complexity_check(password):
    uppercaseletters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    lowercaseletters = 'abcdefghijklmnopqrstuvwxyz'
    numbers = '0123456789'

    haveuppercaseletters = False
    havelowercaseletters = False
    havenumbers = False
    have8letters = False

    numberof_chars = 0

    for i in password:
        if i in uppercaseletters:
            haveuppercaseletters = True
        elif i in lowercaseletters:
            havelowercaseletters = True
        elif i in numbers:
            havenumbers = True
        numberof_chars += 1

    if numberof_chars >= 8:
        have8letters = True


    return have8letters and haveuppercaseletters \
        and havelowercaseletters and havenumbers

def send_password_recovery_mail(token):
    # informações iniciais
    login_email = settings.SMTP_LOGIN
    senha_email = settings.SMTP_PWD
    server_smtp = settings.SMTP_SERVER
    porta_smtp = settings.SMTP_PORT
    SERVER_URL = settings.SERVER_URL

    # montagem da mensagem
    msg = MIMEMultipart()
    msg['From'] = login_email
    msg['To'] = token.user_fk.email
    msg['Subject'] = "PASSWORD RECOVERY"
    body = f"""
    <html>
    <body>
    <h3>PASSWORD RECOVERY</h3>
    <p>To recover your password please click in the link bellow or copy and paste on your browser:</p>
    <p>
    <a href="https://{SERVER_URL}/auth_app/reset_password/{token.token}">https://{SERVER_URL}/auth_app/reset_password/{token.token}</a>
    </p>
    </body>
    </html>"""
    msg.attach(MIMEText(body, 'html'))    

    # conexão com o servidor
    server = smtplib.SMTP_SSL(server_smtp, porta_smtp)
    server.login(login_email, senha_email)
    text = msg.as_string()
    server.sendmail(login_email, token.user_fk.email, text)
    server.quit()

# Create your views here.
def register(request):
    responses = []

    if request.method == 'POST':
        username = request.POST['username'].lower()
        firstname = request.POST['firstname'].title()
        lastname = request.POST['lastname'].title()
        email = request.POST['email'].lower()
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        
        if '@' in username:
            responses.append({'color': 'red', 'text':'Username can not contain the \'@\'.'})

        # checking pwd complexity
        if password1 == password2:
            if not password_complexity_check(password1):
                responses.append({'color': 'red', 'text':'Password doesn\'t match the minimun complexity required.'})
        else:
            responses.append({'color': 'red', 'text':'Password mismatch.'})
        
        user = User.objects.filter(username=username)
        if user:
            responses.append({'color': 'red', 'text':'Username already in use.'})

        # check if this email is already in use
        user = User.objects.filter(username=username)
        if user:
            responses.append({'color': 'red', 'text':'Email already in use.'})
        
        if not responses:
            user = User()
            user.username = username
            user.first_name = firstname
            user.last_name = lastname
            user.email = email
            user.set_password(password1)
            user.save()
            lgin(request=request, user=user)

            action = AuthenticationActions()
            action.ip = get_client_ip(request)
            action.login_info = username
            action.authentication_type = 'register'
            action.success = True
            action.save()

            return HttpResponseRedirect('/')

    return render(request, 'auth_app/register.html', context={'responses':responses})

def login(request):
    responses = []

    if request.method == 'POST':
        logininfo = request.POST['logininfo'].lower()
        password = request.POST['password']

        now = datetime.now()
        five_minutes_ago = now - timedelta(minutes=5)

        if len(AuthenticationActions.objects.filter(login_info=logininfo, created_at__gte=five_minutes_ago, authentication_type='login')) >= 3:
            responses.append({'color':'red','text':'Too many incorrect logins in a short time, wait 5 minutes and try again.'})
        else:
            action = AuthenticationActions()
            action.ip = get_client_ip(request)
            action.login_info = logininfo
            action.authentication_type = 'login'

            if '@' in logininfo:
                user = User.objects.filter(email=logininfo) 
            else:
                user = User.objects.filter(username=logininfo) 

            if user:
                user = user[0]
                if not user.check_password(password):
                    responses.append({'color':'red','text':'Wrong password.'})
            else:
                responses.append({'color':'red','text':'User not found.'})

            
            if not responses:
                lgin(request=request, user=user)
                action.success = True
                action.save()
                return HttpResponseRedirect('/')
            else:
                action.success = False
                action.save()

    return render(request, 'auth_app/login.html', context={'responses':responses})

def logout(request):

    action = AuthenticationActions()
    action.ip = get_client_ip(request)
    action.authentication_type = 'logout'

    user = User.objects.filter(id=request.user.id)
    if user:
        logininfo = user[0].username
    else:
        logininfo = 'noauth' 
    
    action.login_info = logininfo

    if request.user.is_authenticated:
        action.success = True
    else:
        action.login_info = ''
        action.success = False

    action.save()

    lgout(request=request)

    return render(request, 'auth_app/logout.html')

def request_password_reset(request):
    responses = []

    if request.method == 'POST':
        logininfo = request.POST['logininfo']

        action = AuthenticationActions()
        action.ip = get_client_ip(request)
        action.login_info = logininfo
        action.authentication_type = 'request_password_reset'

        if '@' in logininfo:
            user = User.objects.filter(email=logininfo) 
        else:
            user = User.objects.filter(username=logininfo) 

        if not user:
            responses.append({'color':'red','text':'User not found.'})
        else:
            user = user[0]
            
        if not responses:
            action.success = True
            action.save()
            token = ResetPasswordToken()
            token.user_fk = user
            token.save()
            
            send_password_recovery_mail(token)
            
            info = {
                'title': 'Reset Password',
                'content':'Reset password token sent to your email.',
            }
            return render(request, 'info.html', context={'info':info})
        else:
            action.success = False
            action.save()

    return render(request, 'auth_app/request_password_reset.html', context={'responses':responses})

def reset_password(request, token=''):
    responses = []

    if request.method == 'POST':

        action = AuthenticationActions()
        action.ip = get_client_ip(request)
        action.authentication_type = 'reset_password'

        try:
            token = ResetPasswordToken.objects.filter(token=uuid.UUID(token))
        except:
            responses.append({
                'color':'red',
                'text':'Invalid token.',
            })
            
        if not token:
            action.login_info = ''
            responses.append({'color': 'red', 'text':'Token does not exists.'})
        else:
            token = token[0]
            action.login_info = token.user_fk.username


        password1 = request.POST['password1']
        password2 = request.POST['password2']

        # checking pwd complexity
        if password1 == password2:
            if not password_complexity_check(password1):
                responses.append({'color': 'red', 'text':'Password doesn\'t match the minimun complexity required.'})
        else:
            responses.append({'color': 'red', 'text':'Password mismatch.'})

        if not responses:
            user = User.objects.get(id=token.user_fk.id)
            user.set_password(password1)
            user.save()
            token.delete()
            action.success = True
            action.save()
            return HttpResponseRedirect('/')
        else:
            action.success = False
            action.save()

    return render(request, 'auth_app/reset_password.html', context={'responses':responses, 'token': token if token else ''})

@login_required(login_url='/auth_app/login/')
def redefine_password(request):
    responses = []

    if request.method == 'POST':
        currentpassword = request.POST['currentpassword']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        action = AuthenticationActions()
        action.ip = get_client_ip(request)
        action.login_info = request.user.username
        action.authentication_type = 'redefine_password'

        # checking pwd complexity
        if password1 == password2:
            if not password_complexity_check(password1):
                responses.append({'color': 'red', 'text':'Password doesn\'t match the minimun complexity required.'})
        else:
            responses.append({'color': 'red', 'text':'Password mismatch.'})
        
        user = User.objects.get(id=request.user.id)
        if not user.check_password(currentpassword):
            responses.append({'color': 'red', 'text':'Password doesn\'t matches the current user password.'})

        if not responses:   
            user.set_password(password1)
            user.save()
            lgin(request, user)
            action.success = True
            action.save()
            return HttpResponseRedirect('/')
        else:
            action.success = False
            action.save()

    return render(request, 'auth_app/redefine_password.html', context={'responses':responses})

@login_required(login_url='/auth_app/login/')
def profile(request):
    responses = []

    if request.method == 'POST':

        action = AuthenticationActions()
        action.ip = get_client_ip(request)
        action.login_info = request.user.username
        action.authentication_type = 'edit_profile'

        user = User.objects.get(id=request.user.id)

        firstname = request.POST['firstname'].title()
        lastname = request.POST['lastname'].title()
        email = request.POST['email'].lower()

        if user.email != email:
            search = User.objects.filter(email=email)
            if search:
                responses.append({'color': 'red', 'text':'This email is already in use.'})
                action.success = False
                action.save()
        else:
            user.first_name = firstname
            user.last_name = lastname
            user.email = email
            user.save()
            action.success = True
            action.save()
            return HttpResponseRedirect('/')

    return render(request, 'auth_app/profile.html', context={'responses':responses})
