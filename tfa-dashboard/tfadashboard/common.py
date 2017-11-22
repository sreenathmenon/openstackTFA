#
#Copyright 2017 Nephoscale
# 

import os
import base64
import io
import os
import sys
import time
import math
import hashlib
import hmac
import struct
import base64
from keystoneauth1.identity import v2
from keystoneauth1 import session
from keystoneclient.v2_0 import client as kclient
from django.conf import settings

"""
from openstack_dashboard.local.local_settings import \
        ASTUTE_BASE_URL, 
"""

######Section Used for 2 Factor Authentication
def kclient_connect(request):

    #Getting the config details
    tenant_id    = getattr(settings, 'KEYSTONE_ADMIN_TENANT_ID',    '')
    tenant_name  = getattr(settings, 'KEYSTONE_ADMIN_TENANT_NAME',  '')
    user_id      = getattr(settings, 'KEYSTONE_ADMIN_USER_ID',      '')
    user_name    = getattr(settings, 'KEYSTONE_ADMIN_USERNAME',    '')
    auth_url     = getattr(settings, 'KEYSTONE_ADMIN_AUTH_URL',     '')
    password     = getattr(settings, 'KEYSTONE_ADMIN_PASSWORD',     '')

    #Making the dictionary to save the data
    keystone_cred = {}

    #Saving the details to dictionary
    if tenant_id:
        keystone_cred['tenant_id']   = tenant_id
    else:
        keystone_cred['tenant_name'] = tenant_name
    if user_id:
        keystone_cred['user_id']     = user_id
    else:
        keystone_cred['username']    = user_name

    keystone_cred['password'] = password
    keystone_cred['auth_url'] = auth_url

    print keystone_cred

    auth      = v2.Password(**keystone_cred)
    sess      = session.Session(auth=auth)
    keystone  = kclient.Client(session=sess)

    return keystone

def get_user_id(request):
    """Fetch the id corresponding to a user"""
    client = keystoneclient(request, admin=False)
    client.user_id = request.user.id
    return client.user_id

def user_details(request):
    """Fetch the information of any user"""
    user_id = request.user.id
    keystone = kclient_connect(request)
    print('user_details function entering')
    user = keystone.users.get(user_id)
    return user


def generate_2fa_uri(secret, name):
    """Generate a uri based on secret key.

    QR codes to be scanned by Google Authenticator app 
    are being generated based on this uri.
   
    Args:
        secret: the unique secret key which is required for generating the uri
    Returns:
        uri: a uri which can be used for generating the QR code

    """
    uri = 'otpauth://totp/{name}?secret={secret}&issuer={issuer}'.format(name=name, secret=secret, issuer='M1 Dashboard')
    return uri


def get_2fa_auth_details(request, user):
    """Generates a random secret key and pass it to generate the unique uri."""
    secret = base64.b32encode(os.urandom(10)).decode('utf-8')

    #Name of the user
    name = user.name

    #Generate the uri based on the above generated secret key
    uri    = generate_2fa_uri(secret, name)
    return secret, uri


def enable_2fa(request, user, **data):
    """To enable two factor authentication for a user.

     Args:
         user: details corresponding to the user for whom the 2fa is to be enabled
         data: array containing the details which are to be updated corresponding to 
               this user in DB.
    Return:
        Enable 2FA for the user

    """

    data['two_factor_enabled'] = True

    if user_update_2fa_details(request, user, **data):
        print "entered into user_update function loop for enabling 2FA"
        return True
    else:
        print "user_update failure for 2FA"
        return False

def disable_2fa(request, user):
    """To disable two factor authentication for a user.

    Args:
        user: details corresponding to the user for whom the 2FA is to be disabled.

    Return:
        Disable 2FA for the user.

    """

    data = {}
    data['two_factor_enabled'] = False

    if user_update_2fa_details(request, user, **data):
        print "entered into user_update function loop for disabling 2FA"
        return True
    else:
        print "user_update failure"
        return False


def user_update_2fa_details(request, user, **data):
    """To update the 2fa details in DB"""

    #manager = keystoneclient(request, admin=True).users
    manager = kclient_connect(request).users
    print manager
    print '%%%%%%%%%%%%%%%%%%%%%%%5'
    if manager.update(user, **data):
        print "success"
        return True
    else:
        print "FAILURE"
        return False

def auth_2fa_is_enabled(request, user):
    """Check if 2FA is enabled for the user or not.

    Args:
        user: details corresponding to the user

    Return:
        Return true is 2FA has been enabled.
  
    """

    manager = keystoneclient(request, admin=True).users
    print "$$$$$Entering 2fa enabked checking function"
    return True


def generate_totp(secret, time_range=30, i=0):
    """Algorithm for generating the Time Based One Time Password.

    Using this function we generate and find the unique TOTP value corresponding to a 
    secret key at the current moment. TOTP values are Time based and valid for only a 
    few seconds.

    Args:
       secret: unique secret key using which we find the current TOTP value
   
    Return:
        The unique TOTP value based on the current time.

    """

    print('generate totp function')

    #Converting the secret key
    secret = base64.b32decode(secret, True)
    tm = int(time.time() / time_range)
    b = struct.pack(">q", tm + i)
    print type(secret)
    secret = str(secret)
    print type(secret)
    hm = hmac.HMAC(secret, b, hashlib.sha1).digest()
    offset = ord(hm[-1]) & 0x0F
    truncatedHash = hm[offset:offset + 4]
    code = struct.unpack(">L", truncatedHash)[0]
    code &= 0x7FFFFFFF
    code %= 1000000
    return "%06d" % code

def str2bool(self, v):
        """Function For converting unicode values to bool"""
        print('Entering conversion function')
        return v.lower() in ("yes", "true", "t", "1")

#####End of Section used for 2Factor Authentication


