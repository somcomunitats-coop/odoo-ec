from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class OperationRequest(models.Model):
    _inherit = "operation.request"

    def execute_operation(self):
        """CAUTION: we are full overriding here this function in order to
        be able to get sequences (sequence_register_operation & sequence_subscription)
        from a multicompany scenario"""

        self.ensure_one()

        if self.effective_date:
            effective_date = self.effective_date
        else:
            effective_date = self.get_date_now()
            self.effective_date = effective_date
        sub_request = self.env["subscription.request"]

        self.validate()

        if self.state != "approved":
            raise ValidationError(
                _("This operation must be approved" " before to be executed")
            )

        values = self.get_subscription_register_vals(effective_date)

        if self.operation_type == "sell_back":
            self.hand_share_over(self.partner_id, self.share_product_id, self.quantity)
        elif self.operation_type == "convert":
            amount_to_convert = self.share_unit_price * self.quantity
            convert_quant = int(amount_to_convert / self.share_to_product_id.list_price)
            remainder = amount_to_convert % self.share_to_product_id.list_price

            if convert_quant > 0 and remainder == 0:
                share_ids = self.partner_id.share_ids
                line = share_ids[0]
                if len(share_ids) > 1:
                    share_ids[1 : len(share_ids)].unlink()
                line.write(
                    {
                        "share_number": convert_quant,
                        "share_product_id": self.share_to_product_id.id,
                        "share_unit_price": self.share_to_unit_price,
                        "share_short_name": self.share_to_short_name,
                    }
                )
                values["share_to_product_id"] = self.share_to_product_id.id
                values["quantity_to"] = convert_quant
            else:
                raise ValidationError(
                    _("Converting just part of the" " shares is not yet implemented")
                )
        elif self.operation_type == "transfer":
            # sequence_id = self.env.ref("cooperator.sequence_subscription", False)
            sequence_id = self.env["account.move"].get_sequence_register()

            partner_vals = {"member": True}
            if self.receiver_not_member:
                partner = self.subscription_request.create_coop_partner()
                # get cooperator number
                sub_reg_num = int(sequence_id.next_by_id())
                partner_vals.update(
                    sub_request.get_eater_vals(partner, self.share_product_id)
                )
                partner_vals["cooperator_register_number"] = sub_reg_num
                partner.write(partner_vals)
                self.partner_id_to = partner
            else:
                # means an old member or cooperator candidate
                if not self.partner_id_to.member:
                    if self.partner_id_to.cooperator_register_number == 0:
                        sub_reg_num = int(sequence_id.next_by_id())
                        partner_vals["cooperator_register_number"] = sub_reg_num
                    partner_vals.update(
                        sub_request.get_eater_vals(
                            self.partner_id_to, self.share_product_id
                        )
                    )
                    partner_vals["old_member"] = False
                    self.partner_id_to.write(partner_vals)
            # remove the parts to the giver
            self.hand_share_over(self.partner_id, self.share_product_id, self.quantity)
            # give the share to the receiver
            self.env["share.line"].create(
                {
                    "share_number": self.quantity,
                    "partner_id": self.partner_id_to.id,
                    "share_product_id": self.share_product_id.id,
                    "share_unit_price": self.share_unit_price,
                    "effective_date": effective_date,
                }
            )
            values["partner_id_to"] = self.partner_id_to.id
        else:
            raise ValidationError(_("This operation is not yet" " implemented."))

        # sequence_operation = self.env.ref(
        #    "cooperator.sequence_register_operation", False
        # )  # noqa
        sequence_operation = self.env["account.move"].get_sequence_operation()

        sub_reg_operation = sequence_operation.next_by_id()

        values["name"] = sub_reg_operation
        values["register_number_operation"] = int(sub_reg_operation)

        self.write({"state": "done"})

        sub_register_line = self.env["subscription.register"].create(values)

        # send mail to the receiver
        if self.operation_type == "transfer":
            self._send_share_transfer_mail(sub_register_line)

        self._send_share_update_mail(sub_register_line)
