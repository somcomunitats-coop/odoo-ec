from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.easy_my_coop_website.controllers import main as emyc_wsc


class WebsiteSubscriptionCCEE(emyc_wsc.WebsiteSubscription):
    @http.route()
    def display_become_cooperator_page(self, **kwargs):

        target_odoo_company_id = False
        if kwargs.get('odoo_company_id', False):
            try:
                target_odoo_company_id = int(kwargs.get('odoo_company_id'))
            except:
                pass

        if ('odoo_company_id' in kwargs) and (not target_odoo_company_id or not request.env['res.company'].sudo().search(
                [('id', '=', target_odoo_company_id)])):
            return http.Response(_("Not valid parameter value [odoo_company_id]"), status=500)

        ctx = dict(request.context)
        ctx.update({'target_odoo_company_id': target_odoo_company_id})
        request.context = ctx


        res = super(WebsiteSubscriptionCCEE,
                    self).display_become_cooperator_page(**kwargs)
        return res

    def fill_values(self, values, is_company, logged, load_from_user=False):
        values = super(WebsiteSubscriptionCCEE, self).fill_values(
            values, is_company, logged, load_from_user)

        default_company = request.env["res.company"]._company_default_get()


        target_company_id = request.context.get('target_odoo_company_id', False) and int(
            request.context.get('target_odoo_company_id')) or None
        if target_company_id and target_company_id != default_company.id:
            company = request.env['res.company'].sudo().search(
                [('id', '=', target_company_id)])
    
            values["company"] = company
            if not values.get("country_id"):
                if company.default_country_id:
                    # company.default_country_id.id
                    values["country_id"] = "68"
                else:
                    values["country_id"] = "68"
            if not values.get("activities_country_id"):
                if company.default_country_id:
                    # company.default_country_id.id
                    values["activities_country_id"] = "68"
                else:
                    values["activities_country_id"] = "68"
            if not values.get("lang"):
                if company.default_lang_id:
                    values["lang"] = company.default_lang_id.code

            values.update(
                {
                    "display_data_policy": company.display_data_policy_approval,
                    "data_policy_required": company.data_policy_approval_required,
                    "data_policy_text": company.data_policy_approval_text,
                    "display_internal_rules": company.display_internal_rules_approval,
                    "internal_rules_required": company.internal_rules_approval_required,
                    "internal_rules_text": company.internal_rules_approval_text,
                    "display_financial_risk": company.display_financial_risk_approval,
                    "financial_risk_required": company.financial_risk_approval_required,
                    "financial_risk_text": company.financial_risk_approval_text,
                    "display_generic_rules": company.display_generic_rules_approval,
                    "generic_rules_required": company.generic_rules_approval_required,
                    "generic_rules_text": company.generic_rules_approval_text,
                }
            )

        return values

