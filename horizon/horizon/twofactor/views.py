from django.http import HttpResponse
from django.template import RequestContext, loader
from openstack_dashboard.views import get_user_home,callKeystoneForTotp
from django import shortcuts
from horizon import exceptions
import logging
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.http import  HttpResponseRedirect
from django.shortcuts import render

LOG = logging.getLogger(__name__)

def index(request):
    """
    Function to show the TOTP page.
    @param : request
    @return : HTTP response
    """

    request.session['totp_valid'] = False
    if not request.user.is_authenticated():
        raise exceptions.NotAuthenticated()
     
    template = loader.get_template('auth/twofactor.html')
    context = RequestContext(request, {
    #    'totpVal': "test",
    })

    return HttpResponse(template.render(context))

def totpSubmit(request):
    """
	TOTP submit call. This will get the submitted TOTP from request and call keystone for TOTP validation.
	@param : request object
	"""
    
    print '%%%%%%%%%%%%%%%%%%RRRRRRRRRRRRRRRRR$$$$$$$$$$$$$'
    print request.__dict__
    LOG.info('totpSubmit function')
    res = callKeystoneForTotp(request)
    LOG.info('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    #LOG.info('87878dffsdf7f878787788')
    LOG.info(request.session.__dict__)
    LOG.info(res)
    LOG.info('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    
    if request.session.get('totp_valid', False):
        totp_val = request.session['totp_valid']
        if totp_val:
            print 'totp val is settttt as true'
            response = shortcuts.redirect(get_user_home(request.user))
            return response
        else:
            print 'top value is falseeeeeee 1'
            request.session['totp_error'] = 'Two Factor Code is Incorrect!'
            response = shortcuts.redirect('/dashboard/twofactor')
            return response
    else:
        print 'top value is falseeeeeee 2'
        request.session['totp_error'] = 'Two Factor Code is Incorrect!2'
        response = shortcuts.redirect('/dashboard/twofactor')
        return response

def backToLogin(request):
	"""
	Function to destroy session and move back to login screen.
	"""
    
	request.session.flush()
	return shortcuts.redirect("/auth/login")


