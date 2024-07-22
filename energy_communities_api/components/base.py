from odoo import models

from odoo.addons.component.core import AbstractComponent, Component


class ApiInfoBackend(models.Model):
    _name = "api.info.backend"
    _inherit = "collection.base"


class RecordsetComponent(AbstractComponent):
    _name = "recordset.component"
    _collection = "api.info.backend"

    def __init__(self, *args):
        super().__init__(*args)
        self.recordset = self.model.browse(self.work.rec_ids)


class ApiInfo(Component):
    _name = "api.info"
    _usage = "api.info"
    _inherit = "recordset.component"

    def __init__(self, *args):
        super().__init__(*args)
        self.info_schema = self.work.info_schema

    def get(self):
        if len(self.recordset) > 1:
            return self._info_list()
        return self._info()

    def _info(self):
        return self.info_schema.from_orm(self.recordset[0])

    def _info_list(self):
        return list(
            map(lambda record: self.info_schema.from_orm(record), self.recordset)
        )
