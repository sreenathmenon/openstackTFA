# _______________________________________________________________________
# | File Name: forms.py                                                 |
# |                                                                     |
# | This file is for handling the forms of zendesk support              |
# |_____________________________________________________________________|
# | Start Date: July 7th, 2016                                          |
# |                                                                     |
# | Package: Openstack Horizon Dashboard [liberity]                     |
# |                                                                     |
# | Copy Right: 2016@nephoscale                                         |
# |_____________________________________________________________________|

from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django  import forms as django_forms
from horizon import exceptions
from horizon import forms
from openstack_dashboard.dashboards.zendesksupport import api as zendesk_api
from django.shortcuts import render, redirect
from openstack_dashboard import api
from keystoneclient.v2_0 import client as kclient_v2
from keystoneclient.v3 import client as kclient_v3
from keystoneauth1 import identity
from keystoneauth1 import session
from django.conf import settings

#Setting the ticket priority choices
TICKET_PRIORITY_CHOICES = (
    ('low',    'Low'),
    ('normal', 'Normal'),
    ('high',   'High'),
    ('urgent', 'Urgent')
)

#Checking the auth version and calling the create token method accordingly
keystone_auth_version = getattr(settings, 'KEYSTONE_AUTH_VERSION', 'v2.0')
print keystone_auth_version
print '======^^^^^^^^^^^^^'

if keystone_auth_version == 'v3':
    kwargs = {
        "proj_name":           getattr(settings, 'KEYSTONE_ADMIN_PROJECT_NAME',''),
        "proj_domain_name":    getattr(settings, 'KEYSTONE_ADMIN_PROJECT_DOMAIN_NAME', ''),
        "user_name":           getattr(settings, 'KEYSTONE_ADMIN_USERNAME', ''),
        "user_domain_name":    getattr(settings, 'KEYSTONE_ADMIN_USER_DOMAIN_NAME', ''),
        "auth_url":            getattr(settings, 'KEYSTONE_ADMIN_AUTH_URL', ''),
        "password":            getattr(settings, 'KEYSTONE_ADMIN_PASSWORD', ''),
    }

    auth = identity.v3.Password(**kwargs)
    sess = session.Session(auth=auth)
    keystone = kclient_v3.Client(session=sess)
else:
    kwargs  = {
        "username":    getattr(settings, "KEYSTONE_ADMIN_USERNAME"),
        "password":    getattr(settings, "KEYSTONE_ADMIN_PASSWORD"),
        "auth_url":    getattr(settings, "KEYSTONE_ADMIN_AUTH_URL"),
        "tenant_name": getattr(settings, "KEYSTONE_ADMIN_TENANT_NAME"),
    }
    auth = identity.v2.Password(**kwargs)
    sess = session.Session(auth=auth)
    keystone = kclient_v2.Client(session=sess)

print keystone.__dict__
print '===================='

#Setting the keystone client
# credentials = {'username': 'admin', 'password': '5d6baead492b', 'tenant_name': 'admin', 'auth_url': 'https://api.stage1.nephoscale.com:5000/v2.0', 'region': 'stage1'}
# admin_client = client.Client(
#             username=credentials['username'],
#             password=credentials['password'],
#             tenant_name=credentials['tenant_name'],
#             auth_url=credentials['auth_url'],
#             region_name=credentials['region'])

#Setting the keystone client
#auth = v3.Password(user_domain_name='default', username='admin',password='admin',project_domain_name='default',project_name='admin',auth_url='http://198.89.118.193:5000/v3')
#sess = session.Session(auth=auth)
#keystone = client.Client(session=sess)

class BaseUserForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(BaseUserForm, self).__init__(request, *args, **kwargs)

        # Populate project choices
        user_choices = []
        role_check = False
        # If the user is already set (update action), list only projects which
        # the user has access to.
        try:

            #Getting the user list
            users = keystone.users.list()
            for user in users:

                #checking the tenant id and the user id values to verify the role of permission
                if hasattr(user, 'tenantId'):
                    if  user.id == request.user.id:
                        try:

                            #Getting the role of user
                            roles = keystone.roles.list(user=user.id, project= user.default_project_id)
                            
                            #Getting the role which have the create permission
                            #set_role = getattr(settings, 'ZENDESK_ROLE', 'admin')
                            set_role = ['admin', 'service']
                            for role in roles:
                                if role.name in set_role:
                                    role_check = True
                        except Exception, e:
                            print 'error in the role for user', e

                #Checking the user have email
                has_email = hasattr(user,  'email')
                if user.enabled and user.id != request.user.id and has_email:
                
                    #Only users with an email will be listed in the dropdown
                    if (getattr(user, 'email') != '') and (getattr(user, 'email') is not None):
                        
                        #Creating the dropdown value (user id, email and name)
                        user_value = str(user.id) + '--' +  str(user.email) + '--' + str(user.name)
                        user_choices.append((user_value, user.name))
                
            #to show the drop down first element.
            if not user_choices:
                user_choices.insert(0, ('', _("No available users")))
                self.fields['user'].widget = forms.HiddenInput()
            elif len(user_choices) > 1:
                user_choices.insert(0, ('', _("Select a user")))
        except Exception, e:
            #Hidding the user field for the users
            self.fields['user'].widget = forms.HiddenInput()
            user_choices.insert(0, ('', _("No available users")))
        self.fields['user'].choices = user_choices
        if role_check == False:
            self.fields['user'].widget = forms.HiddenInput()
 

class CreateTicketForm(BaseUserForm):
    """
    # | Form Class to handel the ticket create form
    """
    
    #Creating the fields
    subject     = forms.CharField(  label=_("Subject of your issue"), required=True,  widget=forms.TextInput)
    priority    = forms.ChoiceField(label=_("Priority"),              required=True,  widget=forms.Select,   choices=TICKET_PRIORITY_CHOICES)
    description = forms.CharField(  label=_("Describe your issue"),   required=True,  widget=forms.Textarea ) 
    #attachments = forms.FileField(  label=_("Attachments"),           required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))
    user = forms.DynamicChoiceField(label=_("User list"), required=False,)

    def handle(self, request, data):
        """ 
        * Form to handel the create ticket request
        *
        * @Arguments:
        *   <request>: Request object
        *   <data>:    Data containg form data
        """
        subject     = data['subject']
        description = data['description']
        priority    = data['priority']
        user        = data['user']
        #files       = request.FILES.getlist('attachments')

        # Okay, now we need to call our zenpy to create the 
        # ticket, with admin credential, on behalf of user
        try:
            zendesk = zendesk_api.Zendesk(self.request)
            # First if there is any file, then we need to
            # attach those
            # Currently our zenpy object is not supporting 
            # attachment. Need to decide later
            #if len(files):
            #    for f in files:
            #        zendesk.create_attachment(f)
            #        #f.save()
            #        print f.__dict__
            
            api_data = {
                "subject": subject,
                "priority": priority,
                "description": description,
                "user": user
            }
            
            #Calling the method to create the tickets
            ticket_audit = zendesk.create_ticket(api_data, request)
            ticket = ticket_audit.ticket
            return redirect(reverse_lazy("horizon:zendesk_support_dashboard:tickets:ticket_detail", args=[ticket.id]))
        except Exception as err:
            error_message = _(str(err))
            exceptions.handle(request, error_message)
            return []

class AddCommentForm(django_forms.Form):
    """
    | * Class to add the comments to thye tickets
    """
    comment = forms.CharField(label = _('Add Comment'), required=True, widget=forms.TextInput)
