from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    openupgrade.rename_fields(
        cr,
        [
            (
                "energy_selfconsumption",
                "energy_selfconsumption.selfconsumption",
                "reseller_id",
                "supplier_id",
            ),
        ],
    )
