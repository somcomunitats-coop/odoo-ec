from odoo import fields


class CooperatorType(fields.Selection):
    """Share-type selection that can store a code outside the dropdown.

    The dropdown lists the shares of the active company. Paying an invoice of
    another community stores that community's share code. ``validate=False``
    only skips the check while flushing to SQL. Assigning the value still goes
    through ``convert_to_cache``, which rejects any code missing from the
    active company's list.
    """

    def convert_to_cache(self, value, record, validate=True):
        if not self.validate:
            return value or None
        return super().convert_to_cache(value, record, validate)
