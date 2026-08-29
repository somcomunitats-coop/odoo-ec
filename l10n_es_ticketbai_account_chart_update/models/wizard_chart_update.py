from odoo import models


class WizardUpdateChartsAccounts(models.TransientModel):
    """Extend wizard to handle TicketBAI fiscal position fields."""

    _inherit = "wizard.update.charts.accounts"

    def _get_tbai_exemption_commands(self, template_lines, company):
        """Build ORM commands to instantiate TicketBAI exemptions.

        Args:
            template_lines (recordset): account.fp.tbai.tax_template lines.
            company (res.company): Target company.

        Returns:
            list: ORM commands to create exemptions.
        """
        commands = []
        company = company[:1] if company else self.company_id
        for template_line in template_lines:
            taxes = company.get_taxes_from_templates(template_line.tax_id)
            if len(taxes) != 1:
                continue
            commands.append(
                (
                    0,
                    0,
                    {
                        "tax_id": taxes.id,
                        "tbai_vat_exemption_key": template_line.tbai_vat_exemption_key.id,
                    },
                )
            )
        return commands

    def find_fp_tbai_tax_by_templates(self, templates, real_objs, company=None):
        """Return ORM commands for TicketBAI tax exemptions."""
        company = company or real_objs[:1].position_id.company_id or self.company_id
        expected_commands = self._get_tbai_exemption_commands(templates, company)

        if not templates and real_objs:
            return [(5, 0, 0)]

        if not expected_commands:
            return []

        expected_pairs = sorted(
            (vals[2]["tax_id"], vals[2]["tbai_vat_exemption_key"])
            for vals in expected_commands
        )
        real_pairs = sorted(
            (line.tax_id.id, line.tbai_vat_exemption_key.id) for line in real_objs
        )

        if expected_pairs == real_pairs:
            return []

        return [(5, 0, 0)] + expected_commands

    def diff_fields(self, template, real):
        """Extend to handle TicketBAI fiscal position fields.

        Override to add support for account.fp.tbai.tax_template conversion.

        Args:
            template: Template record (e.g., account.fiscal.position.template)
            real: Real record (e.g., account.fiscal.position)

        Returns:
            dict: Fields that differ between template and real record
        """
        result = super().diff_fields(template, real)

        # Handle TicketBAI exemptions for fiscal positions
        if (
            template._name == "account.fiscal.position.template"
            and hasattr(template, "tbai_vat_exemption_ids")
            and hasattr(real, "tbai_vat_exemption_ids")
        ):
            # Get the relation type
            field = template._fields.get("tbai_vat_exemption_ids")
            if field:
                relation = field.get_description(self.env).get("relation", "")
                if relation == "account.fp.tbai.tax_template":
                    # Convert templates to real records
                    expected = self.find_fp_tbai_tax_by_templates(
                        template.tbai_vat_exemption_ids,
                        real.tbai_vat_exemption_ids,
                        company=real.company_id,
                    )
                    # Only update if there are changes
                    if expected:
                        result["tbai_vat_exemption_ids"] = expected
                    elif "tbai_vat_exemption_ids" in result:
                        result.pop("tbai_vat_exemption_ids")

        return result

    def _prepare_fp_vals(self, fp_template):
        """Extend to include TicketBAI exemptions when creating fiscal positions.

        Args:
            fp_template: Fiscal position template record

        Returns:
            dict: Values to create the fiscal position
        """
        vals = super()._prepare_fp_vals(fp_template)

        # Add TicketBAI exemptions if present
        if hasattr(fp_template, "tbai_vat_exemption_ids"):
            tbai_exemptions = self._get_tbai_exemption_commands(
                fp_template.tbai_vat_exemption_ids, self.company_id
            )
            if tbai_exemptions:
                vals["tbai_vat_exemption_ids"] = tbai_exemptions

        return vals
