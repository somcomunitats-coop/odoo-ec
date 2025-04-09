from odoo.addons.component.core import Component


class ContractUtils(Component):
    _inherit = "contract.utils"

    def _setup_contract_get_update_dict_initial(self):
        contract_update_dict = super()._setup_contract_get_update_dict_initial()
        if "selfconsumption_id" in contract_update_dict.keys():
            del contract_update_dict["selfconsumption_id"]
        if "supply_point_id" in contract_update_dict.keys():
            del contract_update_dict["supply_point_id"]
        return contract_update_dict
