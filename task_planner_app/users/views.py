"""Class and function views for all user related functionalities."""
from datetime import datetime
import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import HttpResponseRedirect, redirect, render
from django.views.generic import View
from .models import User, FriendList, FriendRequest
from tasks.models import Notification, TaskGroup, Task
from users.forms import RegistrationForm, UserAuthenticationForm, EditProfileForm, PDFForm
from django.contrib.auth.decorators import login_required
from .utils import get_friend_request_or_false
from .friend_request_status import FriendRequestStatus
from braces.views import LoginRequiredMixin
from django.shortcuts import render
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from django.views import View
from xhtml2pdf import pisa


def RegisterView(request, *args, **kwargs):
    """View for registering a user.

    Args:
        request: the HTTP request from the frontend.

    Returns:
        Redirection to the dashboard if already authenticated or 
        redirection to the register page if not.
    """
    user = request.user
    if user.is_authenticated:
        messages.success(request, 'You are already authenticated as ' + str(user.email))
        return redirect('tasks:dashboard')

    context = {}
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email').lower()
            password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=password)
            login(request, user)
            destination = kwargs.get('next')
            if destination:
                return redirect(destination)
            return redirect('tasks:dashboard')
        else:
            context['form'] = form
    else:
        form = RegistrationForm()
        context['form'] = form
    return render(request, 'register.html', context)


class LogoutView(SuccessMessageMixin, View):
    """View to logout a user.

    Inherits:
        SuccessMessageMixin: gives access to success messages.
        View: gives access to Django pre-built view methods.
    """
    def get(self, request):
        """Processes a logout request, sends a message and redirects to the login page."""
        logout(request)
        messages.success(request, 'Logged out successfully')
        return HttpResponseRedirect(settings.LOGOUT_REDIRECT_URL)


def LoginView(request):
    """View to login a user.

    Args:
        request: the HTTP request from the frontend.

    Returns:
        Redirection to the dashboard if already authenticated or 
        redirection to the login page if not.
    """
    context = {}
    user = request.user
    if user.is_authenticated:
        return redirect('tasks:dashboard')

    if request.POST:
        form = UserAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email'].lower()
            password = request.POST['password']
            user = authenticate(request, email=email, password=password)

            if user:
                login(request, user)
                messages.success(request, 'Logged in successfully')
                return redirect('tasks:dashboard')
    else:
        form = UserAuthenticationForm()
    context['form'] = form
    return render(request, 'login.html', context)


@login_required
def ProfileView(request, pk=None):
    """View to display details of a user's profile.
    
    Args:
        request: the HTTP request from the frontend.
        pk (default None): primary key of the user being viewed or None if viewing yourself.

    Returns:
        Rendered profile view template with the context.
    """
    if pk:
        account = User.objects.get(pk=pk)
    else:
        account = request.user 
        pk = request.user.id
    tasks = Task.objects.filter(assignee=account, status__in=['To do', 'In progress']).order_by('deadline')
    context = {'user': account, 'pk': pk, 'tasks': tasks}

    try:
        friend_list = FriendList.objects.get(user=account)
    except FriendList.DoesNotExist:
        friend_list = FriendList(user=account)
        friend_list.save()

    friends = friend_list.friends.all()
    context['friends'] = friends
    is_self = True
    is_friend = False
    request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
    friend_requests = None
    user = request.user
    if user.is_authenticated and user != account:
        is_self = False
        if friends.filter(pk=user.id):
            is_friend = True
        else:
            is_friend = False
            if get_friend_request_or_false(sender=account, receiver=user) != False:
                request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
                context['pending_friend_request_id'] = get_friend_request_or_false(sender=account, receiver=user).id
            elif get_friend_request_or_false(sender=user, receiver=account) != False:
                request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value
            else:
                request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
    
    elif not user.is_authenticated:
        is_self = False
    else:
        try:
            friend_requests = FriendRequest.objects.filter(receiver=user, is_active=True)
        except:
            pass

    context['is_self'] = is_self
    context['is_friend'] = is_friend
    context['request_sent'] = request_sent
    context['friend_requests'] = friend_requests   
    
    return render(request, 'profile_view.html', context)


@login_required
def EditProfileView(request):
    """View for editing the user's profile.

    Args:
        request: the HTTP request form the frontend.

    Returns:
        Redirection to the profile or renders the edit profile page.
    """
    user = User.objects.get(pk=request.user.pk)
    if request.method == 'POST':
        form = EditProfileForm(request.POST,request.FILES, instance=request.user)

        if form.is_valid():
            user.profile_image.delete()
            form.save()
            return redirect('profile_view')
    else:
        form = EditProfileForm(instance=request.user)
        tasks = Task.objects.filter(assignee=user, status__in=['To do', 'In progress']).order_by('deadline')
        context = {'form': form, 'tasks': tasks}
        return render(request, 'edit_profile.html', context)


def send_friend_request(request, *args, **kwargs):
    """Sends a friend request.
    
    Args:
        request: HTTP request from the frontend.

    Returns:
        HttpResponse with the context containing friend request and a text response.
    """
    user = request.user
    context = {}
    if request.method == 'POST' and user.is_authenticated:
        user_id = request.POST.get('receiver_user_id')
        if user_id:
            receiver = User.objects.get(pk=user_id)
            try:
                friend_requests = FriendRequest.objects.filter(sender=user, receiver=receiver)
                try:
                    for request in friend_requests:
                        if request.is_active:
                            raise Exception('You already sent them a friend request.')
                    friend_request = FriendRequest(sender=user, receiver=receiver)
                    notification = Notification.objects.get_or_create(
                        notification_type=2, 
                        sender=user, 
                        receiver=receiver, 
                        description='hello!', 
                        seen=False
                    )
                    notification[0].save() 
                    friend_request.save()
                    context['response'] = 'Friend request sent.'
                except Exception as e:
                    context['response'] = str(e)
            except FriendRequest.DoesNotExist:
                friend_request = FriendRequest(sender=user, receiver=receiver)
                friend_request.save()
                context['response'] = 'Friend request sent.'

            if context['response'] == None:
                context['response'] = 'Something went wrong.'
        else:
            context['response'] = 'Unable to sent a friend request.'
    else:
        context['response'] = 'You must be authenticated to send a friend request.'
    return HttpResponse(json.dumps(context), content_type='application/json')


def accept_friend_request(request, *args, **kwargs):
    """Processes the friend request if the receiver accepts.
    
    Args:
        request: HTTP request from the frontend.

    Returns:
        HttpResponse with the context containing friend request and a text response.
    """
    user = request.user
    context = {}
    if request.method == 'GET' and user.is_authenticated:
        friend_request_id = kwargs.get('friend_request_id')
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            if friend_request.receiver == user:
                if friend_request: 
                    friend_request.accept()
                    context['response'] = 'Friend request accepted.'
                else:    
                    context['response'] = 'Something went wrong.'
            else:
                context['response'] = 'That is not your request to accept.'
        else:
            context['response'] = 'Unable to accept that friend request.'
    return HttpResponse(json.dumps(context), content_type='application/json')


def remove_friend(request, *args, **kwargs):
    """View to handle removing a friend from the friend list
    
    Args:
        request: HTTP request from the frontend.

    Returns:
        HttpResponse with the context containing friend request and a text response.
    """
    user = request.user
    context = {}
    if request.method == 'POST' and user.is_authenticated:
        user_id = request.POST.get('receiver_user_id')
        if user_id:
            try:
                removee = User.objects.get(pk=user_id)
                friend_list = FriendList.objects.get(user=user)
                friend_list.unfriend(removee)
                context['response'] = 'Successfully removed that friend.'
            except Exception as e:
                context['response'] = f'Something went wrong: {str(e)}'
        else:
            context['response'] = 'There was an error. Unable to remove that friend.'
    return HttpResponse(json.dumps(context), content_type='application/json')


def cancel_friend_request(request, *args, **kwargs):
    """Processes the friend request if the sender cancels.
    
    Args:
        request: HTTP request from the frontend.

    Returns:
        HttpResponse with the context containing friend request and a text response.
    """
    user = request.user
    context = {}
    if request.method == 'POST' and user.is_authenticated:
        user_id = request.POST.get('receiver_user_id')
        if user_id:
            receiver = User.objects.get(pk=user_id)
            try:
                friend_requests = FriendRequest.objects.filter(sender=user, receiver=receiver, is_active=True)
            except FriendRequest.DoesNotExist:
                context['response'] = 'Nothing to cancel. Friend request does not exist.'
            if len(friend_requests) > 1:
                for request in friend_requests:
                    request.cance()
                context['response'] = 'Friend request canceled.'
            else:
                friend_requests.first().cancel()
                context['response'] = 'Friend request canceled.'
        else:
            context['response'] = 'Unable to cancel that friend request.'
    return HttpResponse(json.dumps(context), content_type='application/json')


def decline_friend_request(request, *args, **kwargs):
    """Processes the friend request if the receiver declines.
    
    Args:
        request: HTTP request from the frontend.

    Returns:
        HttpResponse with the context containing friend request and a text response.
    """
    user = request.user
    context = {}
    if request.method == 'GET' and user.is_authenticated:
        friend_request_id = kwargs.get('friend_request_id')
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            if friend_request.receiver == user:
                if friend_request: 
                    friend_request.decline()
                    context['response'] = 'Friend request declined.'
                else:
                    context['response'] = 'Something went wrong.'
            else:
                context['response'] = 'That is not your friend request to decline.'
        else:
            context['response'] = 'Unable to decline that friend request.'
    return HttpResponse(json.dumps(context), content_type='application/json')


def friends_list_view(request, *args, **kwargs,):
    """View to display a list containing ther user's friends.
    
    Args:
        request: HTTP request from the frontend.

    Returns:
        HttpResponse with the context containing friend request and a text response.
    """
    context = {}
    user = request.user
    if user.is_authenticated:
        user_id = kwargs.get('user_id')
        if user_id:
            try:
                this_user = User.objects.get(pk=user_id)
                context['this_user'] = this_user
            except User.DoesNotExist:
                return HttpResponse('That user does not exist.')
            try:
                friend_list = FriendList.objects.get(user=this_user)
            except FriendList.DoesNotExist:
                return HttpResponse(f'Could not find a friends list for {this_user.username}')
        
            if user != this_user:
                if not user in friend_list.friends.all():
                    return HttpResponse('You must be friends to view their friends list.')
            friends = []
            auth_user_friend_list = FriendList.objects.get(user=user)
            
            for friend in friend_list.friends.all():
                friends.append((friend, auth_user_friend_list.is_mutual_friend(friend)))
            context['friends'] = friends
    else:		
        return HttpResponse('You must be friends to view their friends list.')
    return render(request, 'friend_list.html', context)


class AcceptFriendNotification(LoginRequiredMixin, View):
    """View to accept a friend request as a notification.
    
    Inherits:
        LoginRequiredMixin: gives site access to signed in users.
        View: gives access to Django pre-built view methods.
    """

    def delete(self, request, notification_pk, *args, **kwargs):
        """Processes the notification and deletes it.

        Args:
            request: the HTTP request from the frontend.
            notification_pk: the primary key of the notification.

        Returns:
            Successful HttpResponse 
        """
        notification = Notification.objects.get(pk=notification_pk)

        notification.seen = True
        notification.save()
        receiver_friend_list = FriendList.objects.get(user=notification.receiver)
        receiver_friend_list.add_friend(notification.sender)
        sender_friend_list = FriendList.objects.get(user=notification.sender)
        sender_friend_list.add_friend(notification.receiver)

        friend_requests = FriendRequest.objects.get(sender=notification.sender, receiver=notification.receiver, is_active=True)
        friend_requests.is_active = False
        receiver_friend_list.save()
        sender_friend_list.save()
        friend_requests.save()
        return HttpResponse('Success', content_type='text/plain')


class DeclineFriendNotification(LoginRequiredMixin, View):
    """View to decline a friend request as a notification.
    
    Inherits:
        LoginRequiredMixin: gives site access to signed in users.
        View: gives access to Django pre-built view methods.
    """

    def delete(self, request, notification_pk, *args, **kwargs):
        """Processes the notification and deletes it.

        Args:
            request: the HTTP request from the frontend.
            notification_pk: the primary key of the notification.

        Returns:
            Successful HttpResponse 
        """
        notification = Notification.objects.get(pk=notification_pk)
        notification.seen = True
        notification.save()
        friend_requests = FriendRequest.objects.get(sender=notification.sender, receiver=notification.receiver, is_active=True)
        friend_requests.is_active = False
        friend_requests.save()
        return HttpResponse('Success', content_type='text/plain')


def render_to_pdf(template_src, context_dict={}):
    """Renders a HTML template as a PDF file.

    Args:
        template_src: filepath of the template to be rendered.
        context_dict (default {}): dictionary containing context data.

    Returns:
        Generated PDF file or None.
    """
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('ISO-8859-1')), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


def index(request):
    """Deprecated?"""
    context = {}
    return render(request, 'profile_view.html', context)


@login_required
def PDFView(request):
    """View to process generating the PDF file.

    Args:
        request: the HTTP request from the frontend.

    Returns:
        Rendered template with the generated PDF file.
    """
    form = PDFForm()
    if request.method == 'POST':
        member = User.objects.get(pk=request.POST['user'])
        data = {
            'group' : TaskGroup.objects.get(pk=request.POST['group']),
            'member' : member,
            'tasks' : [],
            'capacity' : member.capacity,
        }
        to_date = datetime.strptime(request.POST['to_date'], '%Y-%m-%d')
        from_date = datetime.strptime(request.POST['from_date'], '%Y-%m-%d')
        if ((from_date.date() - to_date.date()).days) > 0:
            messages.error(request, 'Please select proper from and to dates.')
            context = {'form' : form}
            return render(request, 'PDFView.html', context)
        for task in Task.objects.filter(list_group=data['group'], assignee=request.POST['user']):
            if not task.deadline:
                data['tasks'].append(task)
            else:
                if is_within_dates(task.deadline, to_date, from_date):
                    data['tasks'].append(task)
                else:
                    messages.error(request, 'The member does not have any assigned tasks between selected dates')
                    context = {'form' : form}
                    return render(request, 'PDFView.html', context)
        if not data['tasks']:
            messages.error(request, 'There are no valid tasks for the report')
            return render(request, 'PDFView.html', {'form' : form})
        pdf = render_to_pdf('pdf_template.html', data)
        return HttpResponse(pdf, content_type='application/pdf')
    
    context = {'form' : form}
    return render(request, 'PDFView.html', context)


def is_within_dates(t1, t2, t3):
    """Helper function to check if a date is between two others.
    
    Args:
        t1: the time to check.
        t2: the lower bound time.
        t3: the upper bound time.

    Returns:
        Boolean indicating if the date is within or not.
    """
    return (t1.date() - t2.date()).days <= 0 and (t1.date() - t3.date()).days >=0


def view_404(request, exception=None):
    """Helper function to redirect to the dashboard if a 404 is raised."""
    return redirect('tasks:dashboard')