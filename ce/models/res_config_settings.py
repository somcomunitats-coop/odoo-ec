from odoo import api, models, fields, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # global parameters (saved on ir.config_parameter):
    ck_server_url = fields.Char(string="KeyCloak Server URL", config_parameter='ce.ck_server_url', placeholder="http://keycloak/")
    ck_server_port = fields.Char(string="KeyCloak Server port", config_parameter='ce.ck_server_port', placeholder="8080")
    ck_platform_oauth_provider_id = fields.Many2one('auth.oauth.provider', string='OAuth provider for Platform admin',
        config_parameter='ce.ck_platform_oauth_provider_id',domain="[('company_id','=',company_id)]")
    ck_user_group_mapped_to_odoo_group_ce_member = fields.Char(string="KeyCloak user group (ce_members)",
    config_parameter='ce.ck_user_group_mapped_to_odoo_group_ce_member')
    ck_user_group_mapped_to_odoo_group_ce_admin = fields.Char(string="KeyCloak user group (ce_admins)",
    config_parameter='ce.ck_user_group_mapped_to_odoo_group_ce_admin')
    ck_user_group_mapped_to_odoo_group_platform_admin = fields.Char(string="KeyCloak user_group (platform_admins)",
    config_parameter='ce.ck_user_group_mapped_to_odoo_group_platform_admin')

    # company dependent parameters (saved on res_company):
    kc_realm = fields.Char(string='KeyCloak realm name', related='company_id.kc_realm', readonly=False)
    ce_admin_key_cloak_provider_id = fields.Many2one('auth.oauth.provider', 
        string='OAuth provider for CCEE admin', readonly=False, related='company_id.ce_admin_key_cloak_provider_id',
        domain="[('company_id','=',company_id)]")
    auth_ce_key_cloak_provider_id = fields.Many2one('auth.oauth.provider', 
        string='OAuth provider for CCEE login', readonly=False, related='company_id.auth_ce_key_cloak_provider_id',
        domain="[('company_id','=',company_id)]")

    def set_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()

        pre_ck_server_url = ICPSudo.get_param('ce.ck_server_url')
        pre_ck_server_port = ICPSudo.get_param('ce.ck_server_port')
        
        super(ResConfigSettings, self).set_values()
        
        ICPSudo.set_param('ce.ck_server_url', self.ck_server_url)
        ICPSudo.set_param('ce.ck_server_port', self.ck_server_port)
        ICPSudo.set_param('ce.ck_platform_oauth_provider_id', self.ck_platform_oauth_provider_id.id)
        ICPSudo.set_param('ce.ck_user_group_mapped_to_odoo_group_ce_member', self.ck_user_group_mapped_to_odoo_group_ce_member)
        ICPSudo.set_param('ce.ck_user_group_mapped_to_odoo_group_ce_admin', self.ck_user_group_mapped_to_odoo_group_ce_admin)
        ICPSudo.set_param('ce.ck_user_group_mapped_to_odoo_group_platform_admin', self.ck_user_group_mapped_to_odoo_group_platform_admin)

        self.env['auth.oauth.provider'].update_ce_oauth_providers(
            pre_ck_server_url != self.ck_server_url and self.ck_server_url or None,
            pre_ck_server_port != self.ck_server_port and  self.ck_server_port or None)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ck_server_url = ICPSudo.get_param('ce.ck_server_url')
        ck_server_port = ICPSudo.get_param('ce.ck_server_port')
        ck_platform_oauth_provider_id = ICPSudo.get_param('ce.ck_platform_oauth_provider_id')
        ck_user_group_mapped_to_odoo_group_ce_member = ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_ce_member')
        ck_user_group_mapped_to_odoo_group_ce_admin = ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_ce_admin')
        ck_user_group_mapped_to_odoo_group_platform_admin = ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_platform_admin')

        res.update(
            ck_server_url=ck_server_url,
            ck_server_port=ck_server_port,
            ck_platform_oauth_provider_id=int(ck_platform_oauth_provider_id),
            ck_user_group_mapped_to_odoo_group_ce_member=ck_user_group_mapped_to_odoo_group_ce_member,
            ck_user_group_mapped_to_odoo_group_ce_admin=ck_user_group_mapped_to_odoo_group_ce_admin,
            ck_user_group_mapped_to_odoo_group_platform_admin=ck_user_group_mapped_to_odoo_group_platform_admin,
        )

        return res