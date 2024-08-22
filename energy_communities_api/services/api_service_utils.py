from odoo import _
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.component.core import AbstractComponent

from ..schemas import DEFAULT_PAGE_SIZE, PaginationLimits


class ApiServiceUtils(AbstractComponent):
    _name = "api.service.utils"

    def _get_pagination_limits(self, paging_param):
        if paging_param.page or paging_param.page_size:
            page = paging_param.page or 1
            page_size = paging_param.page_size or DEFAULT_PAGE_SIZE
            return PaginationLimits(
                limit=page_size, offset=(page - 1) * page_size, page=page
            )
        return None

    def _validate_headers(self):
        community_id = request.httprequest.headers.get("CommunityId")
        if not community_id:
            msg = _("CommunityId header is missing")
            raise ValidationError(msg)
        try:
            int(community_id)
        except Exception:
            msg = _(f"CommunityId header has an incorrect value: {community_id}")
            raise ValidationError(msg)
