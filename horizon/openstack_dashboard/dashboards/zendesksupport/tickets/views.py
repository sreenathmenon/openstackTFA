# _______________________________________________________________________
# | File Name: views.py                                                 |
# |                                                                     |
# | This file is for handling the views of support ticket display       |
# |_____________________________________________________________________|
# | Start Date: July 7th, 2016                                          |
# |                                                                     |
# | Package: Openstack Horizon Dashboard [liberity]                     |
# |                                                                     |
# | Copy Right: 2016@nephoscale                                         |
# |_____________________________________________________________________|

#from openstack_dashboard.dashboards.zendesksupport.api import zenpy_patch as zenpy
from openstack_dashboard.dashboards.zendesksupport.tickets import tabs as ticket_tabs
from django.utils.translation import ugettext_lazy as _
from openstack_dashboard.dashboards.zendesksupport.tickets import tables
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.http import  HttpResponseRedirect
from django.shortcuts import render
from horizon import forms
from horizon import views
from horizon import tabs
from horizon import exceptions
from horizon.utils import memoized
from openstack_dashboard.dashboards.zendesksupport.tickets import forms as ticket_form
from openstack_dashboard.dashboards.zendesksupport import api



class IndexView(tabs.TabbedTableView):
    """
    # | IndexView for showing ticket list 
    # |
    # | Code is in tabs.py 
    """
    tab_group_class = ticket_tabs.MyTicketsTab
    template_name   = "zendesk_support_dashboard/tickets/index.html"
    page_title      = "My Tickets"

class CreateTicketView(forms.ModalFormView):
    """
    # | Class to display create form function 
    """
    form_class    = ticket_form.CreateTicketForm
    template_name = 'zendesk_support_dashboard/tickets/create_ticket.html'
    success_url   = reverse_lazy("horizon:zendesk_support_dashboard:tickets:index")
    modal_id      = "create_ticket_modal"
    modal_header  = _("Create Ticket")
    submit_label  = _("Create Ticket")
    submit_url    = "horizon:zendesk_support_dashboard:tickets:create_ticket"
    def get_context_data(self, **kwargs):
        """
        # | Function to create the create ticket form 
        # | 
        # | Arguments: Kwargs 
        # |
        # | Returns: TEMPLATE CONTEXT
        """
        context = super(CreateTicketView, self).get_context_data(**kwargs)
        context['submit_url'] = reverse_lazy(self.submit_url, args=[])
        return context

def get_ticket_detail(request, **kwargs):
    """
    # | Function for handling ticket detail page
    # |
    # | @Arguments:
    # |     <request>: HTTP Request object
    # |     <kwargs>:  Request dictionary containing different dictionary
    # |
    # | @Returns:
    # |     HTTPResponse Object
    """
    ticket_id = kwargs['ticket_id']
    try:
        zenpy_obj = api.Zendesk(request)
        if request.method == "POST":
            # If the request method is POST
            # then we need to call for addCommentForm
            form = ticket_form.AddCommentForm(request.POST)
            if form.is_valid():
                comment = request.POST.get('comment')
                
                #Fetching the comment privacy type and passing the value for comment creation
                privacy = request.POST.get('comment_privacy')
                zenpy_obj.create_comment(ticket_id,  comment, privacy)
                return HttpResponseRedirect(reverse_lazy('horizon:zendesk_support_dashboard:tickets:ticket_detail', args=[ticket_id]))
            else:
                exceptions.handle(request, form.errors)
        
        ticket_detail   = zenpy_obj.get_ticket_detail(ticket_id)
        ticket_comments = zenpy_obj.get_ticket_comments(ticket_id)
        context = {
            "page_title": ticket_detail.subject,
            "ticket":     ticket_detail,
            "comments":   ticket_comments
        }
        return render(request, 'zendesk_support_dashboard/tickets/ticket_detail.html', context)
    except api.ZendeskError as err:
        if err.code == 403:
            context = {
                "page_title": "403:Forbidden",
                "error": "You are not authorized to view this ticket."
            }
        elif err.code == 404:
            context = {
                "page_title": "404: Not Found",
                "error": "This ticket does not exist."
            }
        else:
            context = {
                "page_title": "500:Unknown Error Occured",
                "error": "Unkown error occured. Unable to fetch ticket detail.."
            }

        return render(request, 'zendesk_support_dashboard/tickets/ticket_detail.html', context)

