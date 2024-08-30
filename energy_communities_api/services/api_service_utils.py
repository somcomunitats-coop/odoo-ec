from datetime import date

from odoo import _
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.component.core import AbstractComponent

from ..schemas import DEFAULT_PAGE_SIZE, PaginationLimits


class ApiServiceUtils(AbstractComponent):
    _name = "api.service.utils"
    THE_START_OF_ALL_TIMES = date(2024, 1, 1)

    def _get_pagination_limits(self, query_params):
        if query_params.page or query_params.page_size:
            page = query_params.page or 1
            page_size = query_params.page_size or DEFAULT_PAGE_SIZE
            return PaginationLimits(
                limit=page_size, offset=(page - 1) * page_size, page=page
            )
        return None

    def _get_dates_range(self, query_params):
        if query_params.from_date or query_params.to_date:
            from_date = query_params.from_date or self.THE_START_OF_ALL_TIMES
            to_date = query_params.to_date or date.today()
            return from_date, to_date
        from_date = self.THE_START_OF_ALL_TIMES
        to_date = date.today()
        return from_date, to_date

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
