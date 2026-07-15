from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hierarchy_level = fields.Selection(
        related="company_id.hierarchy_level",
        readonly=True,
    )
    comercial_name = fields.Char(
        related="company_id.comercial_name",
        readonly=False,
    )
    ce_status = fields.Selection(
        related="company_id.ce_status",
        readonly=False,
    )
    community_energy_action_ids = fields.One2many(
        related="company_id.community_energy_action_ids",
        readonly=False,
    )
    foundation_date = fields.Date(
        related="company_id.foundation_date",
        readonly=False,
    )
    allow_new_members = fields.Boolean(
        related="company_id.allow_new_members",
        readonly=False,
    )
    social_twitter = fields.Char(
        related="company_id.social_twitter",
        readonly=False,
    )
    social_facebook = fields.Char(
        related="company_id.social_facebook",
        readonly=False,
    )
    social_github = fields.Char(
        related="company_id.social_github",
        readonly=False,
    )
    social_linkedin = fields.Char(
        related="company_id.social_linkedin",
        readonly=False,
    )
    social_youtube = fields.Char(
        related="company_id.social_youtube",
        readonly=False,
    )
    social_instagram = fields.Char(
        related="company_id.social_instagram",
        readonly=False,
    )
    social_telegram = fields.Char(
        related="company_id.social_telegram",
        readonly=False,
    )
    social_mastodon = fields.Char(
        related="company_id.social_mastodon",
        readonly=False,
    )
    social_bluesky = fields.Char(
        related="company_id.social_bluesky",
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
