from odoo import fields, models


class UtmCampaign(models.Model):
    _name = "utm.campaign"
    _inherit = "utm.campaign"

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    # TODO: The creation of this field only used for inherited view being able to be rendered. Not used at all. Why do we need it on the view??
    state = fields.Char()


class UtmStage(models.Model):
    _name = "utm.stage"
    _inherit = "utm.stage"

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )


class UtmTag(models.Model):
    _name = "utm.tag"
    _inherit = "utm.tag"

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
