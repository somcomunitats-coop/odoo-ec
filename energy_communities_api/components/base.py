from odoo import models

from odoo.addons.component.core import AbstractComponent


class ApiInfoBackend(models.Model):
    _name = "api.info.backend"
    _inherit = "collection.base"


class ApiInfo(AbstractComponent):
    _name = "api.info"
    _collection = "api.info.backend"

    def __init__(self, *args):
        super().__init__(*args)
        self.schema_class = self.work.schema_class

    def get(self, recordset):
        if len(recordset) > 1:
            return self._info_list(recordset)
        if recordset:
            return self._info(recordset[0])
        return None

    def get_list(self, recordset):
        return self._info_list(recordset)

    def _info(self, record):
        return self.schema_class.model_validate(record)

    def _info_list(self, recordset):
        return [self._info(record) for record in recordset]
