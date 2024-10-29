import logging

from odoo import api, fields, models, tools

logger = logging.getLogger(__name__)


class MailingTraceReport(models.Model):
    _name = "mailing.trace.report"
    _inherit = "mailing.trace.report"

    # In order to being able to use correct context on graph views
    # we have to execute the query again just before loading the view
    @api.model
    def load_views(self, views, options=None):
        self.env.cr.execute(self._report_get_request())
        result = super().load_views(views, options)
        return result

    def _report_get_request_where_items(self):
        return [
            "mailing.company_id = {}".format(str(self.env.company.id)),
        ]
