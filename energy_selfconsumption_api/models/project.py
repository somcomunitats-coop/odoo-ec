from odoo import fields, models


class EnergyProject(models.Model):
    _inherit = "energy_project.project"

    def _get_ir_rule_service_selfconsumption_monitoring(self):
        """
        This method is used to set the domain of the api ir rule. I tried insert this in the domain data but I can't
         find a way to implement the reference and the 'user' var via evaluation or value.
        :return:
        """
        return """
        [
            ('service_contract_ids.service_id', '=', {service_xml_id}),
            ('service_contract_ids.active', '=', True),
            ('service_contract_ids.provider_id.user_id', '=', user.id)
        ]""".format(
            service_xml_id=self.env.ref(
                "energy_selfconsumption_api.service_selfconsumption_monitoring"
            ).id
        )
