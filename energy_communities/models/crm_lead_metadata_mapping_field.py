from ast import literal_eval

from odoo import api, fields, models

MAPPING_BUSINESS_MODELS = ["res.lang", "res.country.state"]


class CrmLeadMetadataMappingField(models.Model):
    _name = "crm.lead.metadata.mapping.field"

    name = fields.Char(string="Name", compute="_compute_name")
    crm_lead_metadata_mapping_id = fields.Many2one("crm.lead.metadata.mapping")
    destination_field_key = fields.Char(string="CRM Lead destination field key")
    type = fields.Selection(
        [
            ("value_field", "Value field"),
            ("many2one_relation_field", "Many2one relation field"),
        ],
        string="Field mapping type",
    )
    metadata_key = fields.Char(string="Metadata key")
    mapping_model_real = fields.Char(
        string="Mapping Real Model", compute="_compute_mapping_model_real"
    )
    mapping_model_id = fields.Many2one(
        "ir.model",
        string="Mapping Model",
        ondelete="cascade",
        required=True,
        domain=[("model", "in", MAPPING_BUSINESS_MODELS)],
        default=lambda self: self.env.ref("mass_mailing.model_mailing_list").id,
    )
    mapping_model_name = fields.Char(
        string="Mapping Model Name",
        related="mapping_model_id.model",
        readonly=True,
        related_sudo=True,
    )
    mapping_domain = fields.Char(string="Mapping Domain", readonly=False, store=True)

    @api.depends("destination_field_key")
    def _compute_name(self):
        for record in self:
            record.name = record.destination_field_key

    @api.depends("mapping_model_id")
    def _compute_mapping_model_real(self):
        for record in self:
            record.mapping_model_real = record.mapping_model_id.model

    def parse_mapping_domain(self):
        self.ensure_one()
        try:
            mapping_domain = literal_eval(self.mapping_domain)
        except Exception:
            mapping_domain = [("id", "in", [])]
        return mapping_domain
