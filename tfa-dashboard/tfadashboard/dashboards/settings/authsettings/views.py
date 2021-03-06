# Copyright 2017 Nephoscale
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect

from horizon import forms
from horizon import views
from horizon.utils import functions as utils
from tfadashboard.dashboards.settings.authsettings import forms as twofactor_forms
from tfadashboard.common import user_details, generate_totp, enable_2fa
from horizon import tabs
from openstack_dashboard import api

from django.http import JsonResponse

class IndexView(forms.ModalFormView):
    """View for Managing the 2Factor Authentication Settings"""
    
    form_class = twofactor_forms.Manage2FAForm
    template_name = 'settings/authsettings/two_factor.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        #Fetching the userid and using that to get the full user information
        user = user_details(self.request)
        two_factor_enabled = getattr(user, 'two_factor_enabled', False)

	    #Converting to bool to fix errors
    	if type(two_factor_enabled) == unicode:
	        two_factor_enabled = self.str2bool(two_factor_enabled)

    	#Set true if the user has enabled 2FA
    	if two_factor_enabled:
	        context['two_factor_enabled'] = True
    	else:
	        context['two_factor_enabled'] = False
        return context

class Disable2FAView(forms.ModalFormView):
    form_class = twofactor_forms.Disable2FAForm
    template_name = 'settings/authsettings/two_factor_disable.html'

    def dispatch(self, request, *args, **kwargs):
        user_id = self.request.user.id
        user = user_details(request)
        if not user.two_factor_enabled:
            return redirect('horizon:settings:authsettings:index')

        return super(Disable2FAView, self).dispatch(request, args, kwargs)


class Manage2FAKeyView(views.APIView):
    template_name = 'settings/authsettings/two_factor_newkey.html'

    def get_template_names(self):
        if self.request.is_ajax():
            if not hasattr(self, "ajax_template_name"):

                # Transform standard template name into ajax name (starting with "_")
                bits = list(os.path.split(self.template_name))
                bits[1] = "".join(("_", bits[1]))
                self.ajax_template_name = os.path.join(*bits)
            template = self.ajax_template_name
        else:
            template = self.template_name
        return template

    def get_context_data(self, **kwargs):
        context = super(Manage2FAKeyView, self).get_context_data(**kwargs)
        cache_key = self.request.session['two_factor_data']
        del self.request.session['two_factor_data']
        return context

    def dispatch(self, request, *args, **kwargs):
        #if 'two_factor_data' not in self.request.session:
        #return redirect('horizon:settings:authsettings:index')
        return super(Manage2FAKeyView, self).dispatch(request, args, kwargs)

def validate_code(request):
    """To validate the TOTP code entered by the user for enabling 2FA"""
    
    user_id = request.user.id
    user = user_details(request)
    user_auth_code = request.GET.get('auth_code', None)
    secret = request.GET.get('secret', None)

    #Generate a code form our side using algorithm and use it to validate
    generated_code = generate_totp(secret)
    data = {}
    extra = {}

    #Code comparison
    if user_auth_code == generated_code:
        data['totp_authenticated'] = True
        extra['two_factor_enabled'] = True
        extra['secret_key'] = secret
        enable_2fa(request, user, **extra)
    else:
        data['totp_authenticated'] = False
    return JsonResponse(data)
