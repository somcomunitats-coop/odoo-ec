from odoo.addons.component.core import AbstractComponent

from ..schemas import PaginationLimits


class PaginatedApiService(AbstractComponent):
    _name = "paginated.api.service"

    def _get_pagination_limits(self, paging_param):
        if paging_param:
            page = paging_param.page or 1
            page_size = paging_param.page_size or DEFAULT_PAGE_SIZE
            return PaginationLimits(
                limit=page_size, offset=(page - 1) * page_size, page=page
            )
        return None
