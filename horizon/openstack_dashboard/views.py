# Copyright 2012 Nebula, Inc.
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

from django import shortcuts
import django.views.decorators.vary

import horizon
from horizon import base
from horizon import exceptions

import logging
import json
from openstack_dashboard import api
import requests as reqs
from django.http import  HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.core.urlresolvers import reverse
from django.conf import settings

LOG = logging.getLogger(__name__)
LOG.info(__name__)

def get_user_home(user):
    LOG.info('get user home function')
    dashboard = None
    if user.is_superuser:
        LOG.info('super user section')
        try:
            dashboard = horizon.get_dashboard('admin')
            LOG.info('admin dashboard section')
        except base.NotRegistered:
            LOG.info('not registered section')
            pass

    if dashboard is None:
        LOG.info('no dashboard section')
        dashboard = horizon.get_default_dashboard()

    LOG.info('last section of fn')
    return dashboard.get_absolute_url()

"""
@django.views.decorators.vary.vary_on_cookie
def splash(request):
    if not request.user.is_authenticated():
        raise exceptions.NotAuthenticated()

    response = shortcuts.redirect(horizon.get_user_home(request.user))
    if 'logout_reason' in request.COOKIES:
        response.delete_cookie('logout_reason')
    return response
"""

@django.views.decorators.vary.vary_on_cookie
def splash(request):
    print 'entering splash'
    LOG.info(request.__dict__)
    LOG.info("In splash function")
    LOG.info(request.user)
    LOG.info(request.user.id)
    if not request.user.is_authenticated():
        LOG.info("User not autenticated ")
        raise exceptions.NotAuthenticated()

    print '$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$4'
    user_id = api.keystone.get_user_id(request)
    LOG.info('##############################################')
    user_details = api.keystone.user_details(request, user_id)
    LOG.info(type(user_details))
   
    """ 
    if user_details.two_factor_enabled:
         two_factor_enabled = user_details.two_factor_enabled
    else:
        two_factor_enabled = False
    """
    two_factor_enabled = getattr(user_details, 'two_factor_enabled', False)
    #two_factor_enabled = False
    print two_factor_enabled
    print '%%%%%%%%%%%%%%%%%%%%%%%%%'
    print two_factor_enabled
    print('after tested')
    #LOG.info(request.session)
    print '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'

    #Login case
    if two_factor_enabled:
        request.session['user_2fa_enabled'] = True
        
        #Check whether 2factor page is shown. If else show it
        LOG.info('redirecting to 2 factor form display page')
        response = shortcuts.redirect('twofactor')
    else:
        print "Redirecting users to their home page/dashboard since 2FA isn't enabled"
        response = shortcuts.redirect(horizon.get_user_home(request.user))

    #Logout case
    if 'logout_reason' in request.COOKIES:
        response.delete_cookie('logout_reason')

    #Return the response corresponding to all above conditions
    return response

def str2bool(v):
    """Function For converting unicode values to bool"""
    print('Entering conversion function')
    return v.lower() in ("yes", "true", "t", "1")

def callKeystoneForTotp(request):
    """TOTP CHECK"""
    try:
        #import urllib2
        print request.__dict__
        totpVal = request.POST.get("totp","")
        LOG.info('TOTP value is ')
        LOG.info(totpVal)
        #url = 'http://192.168.122.230:5000/v3/auth/tokens'
        keystone_auth_url = getattr(settings, 'KEYSTONE_V3_TOKEN_URL')
        print keystone_auth_url
        #url = 'http://localhost:5000/v2.0/tokens'
        print '1111111111111'

        #Setting the data to be passed
        data = '{"auth":{"identity":{"twofactor":{"totp_value":"' + str(totpVal) + '"},"methods": ["token","twofactor"],"token": { "id":"' + request.user.token.id +'"}}}}'
        headers = {'Content-type': 'application/json'}
        request.session['totp_valid'] = False

        print '========STATUS CODE=============='
        try:
            resp = reqs.post(keystone_auth_url, data=data, headers=headers)
            if not resp.status_code >= 400:
                jsonResponse = resp.json()
                print jsonResponse
                for x in jsonResponse:
                    print '5555555555555555'
                    LOG.info('x section')
                    request.session['totp_valid'] = True
                    print "****"
                    print(x)
            else:
                request.session['totp_valid'] = False
                LOG.error('Response is incorrect!')
                raise ValueError('Response is incorrect')        
            print '544444444444444444444444444444444444444444444444'
        except Exception, e:
            print '66666666666666'
            print e
            #request.session['totp_invalid'] = True
            LOG.info('exception section')
            LOG.info(e)
            return False
    
        print('+++++++++++++++++RESPONSE++++++++')
        print request.user.token.id
        print '===============TOKEN================'

        #data = '{ "auth": { "identity":{ "twofactor": {"totp_value": "' + str(totpVal) + '"}, "methods": ["token","twofactor"],"token": { "id":"' + request.user.token.id +'"}   } }  }'
        """
        data = '{ \
                    "auth":{ \
                        "identity":{ \
                            "methods": ["token", "twofactor"], \
                                "twofactor": { \
                                    "totp_value": {"totp_value": "' + str(totpVal) + '"}, \
                                } \
                                "token": { \
                                    "id":"' + request.user.token.id + '" \
                                } \
                        } \
                    } \
                }'
        """
                
        LOG.info('session printing')
        LOG.info(request.session)
        response = shortcuts.redirect(horizon.get_user_home(request.user))
        return response
    except Exception,e:
        LOG.debug("Error occurred while connecting to Keystone")
        response = shortcuts.redirect('/dashboard/totp')
        return response



