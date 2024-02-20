from odoo.http import request

from odoo.addons.community_maps.controllers import (
    cm_submission_transfer_controller,
)

from ..models.model_mapping_conf import (
    _MAP_COMPANY_MEMBER_STATUS__CUSTOM_FILTER_SLUGIDS,
)


class CmSubmissionTransferController(
    cm_submission_transfer_controller.CmSubmissionTransferController
):
    def _extend_confirm_submission_transfer(self, destination_place_id, submission_id):
        # if destination place is open we'll create partners as potential cooperator for the place.
        open_filter = destination_place_id.filter_mids.filtered(
            lambda filter: filter.slug_id
            == _MAP_COMPANY_MEMBER_STATUS__CUSTOM_FILTER_SLUGIDS["open"]
        )
        if open_filter:
            self._create_partner_for_submission(submission_id)

    # TODO: This method could be done with a mapping. Rethink how to healthy keep all this mappings
    def _create_partner_for_submission(self, submission_id):
        creation_dict = {}
        submission_name_meta = submission_id.form_submission_metadata_ids.filtered(
            lambda meta: meta.key == "name"
        )
        if submission_name_meta:
            creation_dict["firstname"] = submission_name_meta.value
        submission_surname_meta = submission_id.form_submission_metadata_ids.filtered(
            lambda meta: meta.key == "surname"
        )
        if submission_surname_meta:
            creation_dict["lastname"] = submission_surname_meta.value
        submission_email_meta = submission_id.form_submission_metadata_ids.filtered(
            lambda meta: meta.key == "email"
        )
        if submission_email_meta:
            creation_dict["email"] = submission_email_meta.value
        submission_phone_meta = submission_id.form_submission_metadata_ids.filtered(
            lambda meta: meta.key == "phone"
        )
        if submission_phone_meta:
            creation_dict["phone"] = submission_phone_meta.value
        if creation_dict:
            if submission_id.partner_id:
                submission_id.partner_id.write(creation_dict)
            else:
                partner = request.env["res.partner"].create(creation_dict)
                submission_id.write({"partner_id": partner.id})
        # TODO: should we append it to the company??
