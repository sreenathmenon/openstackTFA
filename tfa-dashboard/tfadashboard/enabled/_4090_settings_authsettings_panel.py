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

#Slug of the Panel group
PANEL_GROUP = 'user_auth'

#Name of the Panel which is to be displayed
PANEL_DASHBOARD = 'settings'

#Slug of the panel
PANEL = 'authsettings'

#Python Panel class of the PANEL to be added
ADD_PANEL = \
    'tfadashboard.dashboards.settings.authsettings.panel.Settings_TwoFactorPanel'

# Adding js files
ADD_JS_FILES = [
    'dashboard/settings/authsettings/authsettings.js'
]

# Adding CSS FILES
ADD_SCSS_FILES = ['dashboard/settings/authsettings/authsettings.scss']

#If set to True, the PANEL will be removed from PANEL_DASHBOARD/PANEL_GROUP.
#Set the below option to TRUE if Two factor authentication management panel shouldn't be displayed
REMOVE_PANEL = False

