from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hierarchy_level = fields.Selection(
        related="company_id.hierarchy_level",
        readonly=True,
    )
    comercial_name = fields.Char(
        related="company_id.comercial_name",
        string=_("Comercial name"),
        readonly=False,
    )
    ce_status = fields.Selection(
        related="company_id.ce_status",
        string=_("Energy Community state"),
        readonly=False,
    )
    community_energy_action_ids = fields.One2many(
        related="company_id.community_energy_action_ids",
        string=_("Community energy actions"),
        readonly=False,
    )
    foundation_date = fields.Date(
        related="company_id.foundation_date",
        string=_("Foundation date"),
        readonly=False,
    )
    allow_new_members = fields.Boolean(
        related="company_id.allow_new_members",
        string=_("Allow new members"),
        readonly=False,
    )
    social_twitter = fields.Char(
        related="company_id.social_twitter",
        string=_("Twitter Account"),
        readonly=False,
    )
    social_facebook = fields.Char(
        related="company_id.social_facebook",
        string=_("Facebook Account"),
        readonly=False,
    )
    social_github = fields.Char(
        related="company_id.social_github",
        string=_("GitHub Account"),
        readonly=False,
    )
    social_linkedin = fields.Char(
        related="company_id.social_linkedin",
        string=_("LinkedIn Account"),
        readonly=False,
    )
    social_youtube = fields.Char(
        related="company_id.social_youtube",
        string=_("Youtube Account"),
        readonly=False,
    )
    social_instagram = fields.Char(
        related="company_id.social_instagram",
        string=_("Instagram Account"),
        readonly=False,
    )
    social_telegram = fields.Char(
        related="company_id.social_telegram",
        string=_("Telegram Account"),
        readonly=False,
    )
    social_mastodon = fields.Char(
        related="company_id.social_mastodon",
        string=_("Mastodon Account"),
        readonly=False,
    )
    social_bluesky = fields.Char(
        related="company_id.social_bluesky",
        string=_("Bluesky Account"),
        readonly=False,
    )
    wordpress_base_url = fields.Char(
        related="company_id.wordpress_base_url",
        string=_("Wordpress Base URL (JWT auth)"),
        readonly=False,
    )
    wordpress_db_username = fields.Char(
        related="company_id.wordpress_db_username",
        string=_("Wordpress DB Admin Username"),
        readonly=False,
    )
    wordpress_db_password = fields.Char(
        related="company_id.wordpress_db_password",
        string=_("Wordpress DB Admin Password"),
        readonly=False,
    )


class ResConfigSettingsEnergyCommunities(models.TransientModel):
    _name = "res.config.settings.energy_communities"
    _inherit = "res.config.settings"

    recaptcha_public_key = fields.Char(
        "Site Key",
        config_parameter="recaptcha_public_key",
        groups="base.group_system,energy_communities.role_platform_admin_res_groups,energy_communities.role_coord_admin_res_groups,energy_communities.role_ce_admin_res_groups,energy_communities.role_ce_manager_res_groups",
    )
    recaptcha_private_key = fields.Char(
        "Secret Key",
        config_parameter="recaptcha_private_key",
        groups="base.group_system,energy_communities.role_platform_admin_res_groups,energy_communities.role_coord_admin_res_groups,energy_communities.role_ce_admin_res_groups,energy_communities.role_ce_manager_res_groups",
    )
    recaptcha_min_score = fields.Float(
        "Minimum score",
        config_parameter="recaptcha_min_score",
        groups="base.group_system,energy_communities.role_platform_admin_res_groups,energy_communities.role_coord_admin_res_groups,energy_communities.role_ce_admin_res_groups,energy_communities.role_ce_manager_res_groups",
        default="0.7",
    )

    # def execute(self):
    #     self.ensure_one()
    #     if self.env.context.get('source_ir_action') == 'energy_communities_res_config_settings_energy_communities_action' and (self.env.user.has_group('energy_communities.role_platform_admin_res_groups') or self.env.user.has_group('energy_communities.role_coord_admin_res_groups') or self.env.user.has_group('energy_communities.role_ce_admin_res_groups') or self.env.user.has_group('energy_communities.role_ce_manager_res_groups')):
    #         # return super().with_context(ctx).execute()
    #         ctx = self.env.context.copy()
    #         ctx['user_id'] = self.env.ref('base.user_admin').id
    #         return super(ResConfigSettingsEnergyCommunities, self.with_context(ctx)).execute()
    #     return super().execute()
