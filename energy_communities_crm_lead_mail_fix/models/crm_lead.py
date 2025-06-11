# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, models, tools

_logger = logging.getLogger(__name__)


class Lead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Override message_new to ensure partner creation and proper body
        handling when creating leads from incoming emails.

        This method addresses the issue where email body content is lost
        when no matching partner exists for the sender email address.
        """
        # Store original email data for later processing
        email_from = msg_dict.get("email_from")
        body = msg_dict.get("body", "")

        if not msg_dict.get("author_id", False):
            # create a partner if not exists
            partner = self._create_partner_from_email(
                self.env.company, email_from, msg_dict
            )
            msg_dict["author_id"] = partner.id

        # Call the original message_new to create the lead
        return super().message_new(msg_dict, custom_values)

    @api.model
    def _create_partner_from_email(self, company, email_from, msg_dict=None):
        """Create a new partner from email address when processing
        incoming emails.

        Args:
            company (res.company): Company to create the partner
            email_from (str): Email address from the incoming message
            msg_dict (dict): Parsed message dictionary (optional)

        Returns:
            res.partner: Created partner record or False if creation failed
        """
        if not email_from:
            return False

        # Check if partner already exists (shouldn't at this point, but
        # let's be safe)
        normalized_email = tools.email_normalize(email_from)
        if normalized_email:
            existing_partner = self.env["res.partner"].search(
                [
                    ("email_normalized", "=", normalized_email),
                    ("company_ids", "in", [False, company.id]),
                ],
                limit=1,
            )
            if existing_partner:
                return existing_partner

        try:
            # Extract name from email if possible
            email_parts = tools.email_split_tuples(email_from)
            if email_parts:
                name, email = email_parts[0]
                if not name:
                    # Use the part before @ as name if no name is provided
                    name = email.split("@")[0] if email else email_from
            else:
                email = email_from
                name = email_from.split("@")[0] if "@" in email_from else email_from

            # Get the tag for marking auto-created partners
            from_crm_tag = self.env.ref(
                "energy_communities_crm_lead_mail_fix.partner_tag_from_crm_lead",
                raise_if_not_found=False,
            )

            # Prepare partner values
            partner_vals = {
                "name": name,
                "email": email,
                "is_company": False,
                "company_ids": [(6, 0, [company.id])],
                "active": True,
            }

            # Add the tag if it exists
            if from_crm_tag:
                partner_vals["category_id"] = [(4, from_crm_tag.id)]

            # Create the partner
            partner = self.env["res.partner"].create(partner_vals)

            _logger.info(
                "Auto-created partner %s (ID: %s) from email %s for CRM lead",
                partner.name,
                partner.id,
                email_from,
            )

            return partner

        except Exception as e:
            _logger.warning(
                "Failed to create partner from email %s: %s", email_from, str(e)
            )
            return False

    @api.model
    def _mail_find_partner_from_emails(
        self, emails, records=None, force_create=False, extra_domain=False
    ):
        """Override to enhance partner finding logic for CRM leads.

        This ensures we look for partners in the correct company context
        when processing emails for leads.
        """
        # Ensure we're looking for partners in the current company context
        if not extra_domain:
            extra_domain = []

        # Add company restriction to search only in current company or
        # global partners
        company_domain = [("company_ids", "in", [False, self.env.company.id])]
        extra_domain = company_domain + extra_domain

        return super()._mail_find_partner_from_emails(
            emails,
            records=records,
            force_create=force_create,
            extra_domain=extra_domain,
        )
