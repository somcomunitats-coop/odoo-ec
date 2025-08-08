from odoo.addons.component.core import Component


class AccountUtils(Component):
    _name = "account.utils"
    _usage = "account.utils"
    _apply_on = "account.chart.template"  # Not really necessary on this component. Not sure if we should use account.account
    _collection = "utils.backend"
