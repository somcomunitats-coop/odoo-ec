from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from ...energy_communities.utils import get_successful_popup_message
from ..config import COOP_SHARE_INVITED_PRODUCT_CATEG_REF, COOP_SHARE_PRODUCT_CATEG_REF_ASSOCIATIONS, COOP_SHARE_PRODUCT_CATEG_REF, COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF

class ModifyCoopGenericFormSettingsWizard(models.TransientModel):
    _name = "modify.coop.generic.form.settings.wizard"
    _description = "Modify cooperator generic form settings wizard"
    
    def _get_active_id(self):
        response = self.env['product.category'].browse(self.env.context["active_id"]) or None
        return response
    
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    
    product_website = fields.Boolean(
        string="Product Website",
        default=lambda self: self._get_active_id() and self._get_active_id().product_website or False,
        help="If checked, the group of fields in the generic form will be hidden so that you can choose the product from the list of those included. The product that will be linked to the form by default will be the one marked in the ‘Default product in the generic form’ field.",
    )
    
    product_qty_must_be_read_only = fields.Boolean(
        string="Product Qty Must Be Read Only",
        default=lambda self: self._get_active_id() and self._get_active_id().product_qty_must_be_read_only or False,
        help="If checked, the generic and specific web forms for products in this category are configured to allow the product quantity field to the right of the drop-down menu for selecting the product to be modified.",
    )
    
    cooperator_share_form_header_text = fields.Html(
        string="Cooperator share form header text (Cooperatives)",
        translate=True,
        related="company_id.cooperator_share_form_header_text",
        readonly=False,
    )
    
    cooperator_association_share_form_header_text = fields.Html(
        string="Cooperator share form header text (Associations)",
        translate=True,
        related="company_id.cooperator_association_share_form_header_text",
        readonly=False,
    )
    
    voluntary_share_form_header_text = fields.Html(
        string="Voluntary share form header text",
        translate=True,
        related="company_id.voluntary_share_form_header_text",
        readonly=False,
    )
    
    invited_share_form_header_text = fields.Html(
        string="Invited share form header text",
        translate=True,
        related="company_id.invited_share_form_header_text",
        readonly=False,
    )
    
    show_cooperator = fields.Boolean(
        string="Show mandatory (Cooperatives)",
        default=lambda self: self._get_active_id() and self._get_active_id().data_xml_id == COOP_SHARE_PRODUCT_CATEG_REF or False,
    )
    
    show_cooperator_associations = fields.Boolean(
        string="Show mandatory (Associations)",
        default=lambda self: self._get_active_id() and self._get_active_id().data_xml_id == COOP_SHARE_PRODUCT_CATEG_REF_ASSOCIATIONS or False,
    )
    
    show_voluntary = fields.Boolean(
        string="Show voluntary",
        default=lambda self: self._get_active_id() and self._get_active_id().data_xml_id == COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF or False,
    )
    
    show_invited = fields.Boolean(
        string="Show invited",
        default=lambda self: self._get_active_id() and self._get_active_id().data_xml_id == COOP_SHARE_INVITED_PRODUCT_CATEG_REF or False,
    )

    def execute(self):
        self.ensure_one()
        model = self.env.context.get("active_model")
        impacted_record = self.env[model].browse(self.env.context["active_id"])
        if not impacted_record.type_url:
           raise ValidationError(_("This wizard cannot be executed on Product Categories that are not related to Cooperative share products."))
        impacted_record.sudo().product_website = self.product_website
        impacted_record.sudo().product_qty_must_be_read_only = self.product_qty_must_be_read_only          
        return get_successful_popup_message(
            _("Modify generic form settings"), _("Settings already modified.")
        )
