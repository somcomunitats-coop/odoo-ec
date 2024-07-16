from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import chardet
import pandas as pd
import base64
from io import StringIO
import logging
from ..models.selfconsumption import INVOICING_VALUES

logger = logging.getLogger(__name__)

class InvoicingWizard(models.TransientModel):
    _name = "energy_selfconsumption.invoicing.wizard"

    power = fields.Float(string="Total Energy Generated (kWh)")
    contract_ids = fields.Many2many("contract.contract", readonly=True)
    next_period_date_start = fields.Date(
        string="Next Period Start",
        compute="_compute_next_period_date_start_and_end",
        readonly=True,
    )
    next_period_date_end = fields.Date(
        string="Next Period End",
        compute="_compute_next_period_date_start_and_end",
        readonly=True,
    )

    invoicing_mode = fields.Selection(INVOICING_VALUES, string="Invoicing Mode",
                                      default=lambda self: self._get_invoicing_mode)

    import_file = fields.Binary(string="Import File (*.csv)")
    fname = fields.Char(string="File Name")
    delimiter = fields.Char(
        default=",",
        required=True,
        string="File Delimiter",
        help="Delimiter in import CSV file.",
    )
    quotechar = fields.Char(
        default='"',
        required=True,
        string="File Quotechar",
        help="Quotechar in import CSV file.",
    )
    encoding = fields.Char(
        default="utf-8",
        required=True,
        string="File Encoding",
        help="Encoding format in import CSV file.",
    )

    def _get_invoicing_mode(self):
        return self[0].contract_ids[0].project_id.selfconsumption_id.invoicing_mode

    @api.constrains("import_file")
    def _constrains_import_file(self):
        logger.info("\n\n _constrains_import_file")
        if self.fname:
            format = str(self.fname.split(".")[-1])
            if format != "csv":
                raise ValidationError(_("Only csv format files are accepted."))

    @api.depends("contract_ids")
    def _compute_next_period_date_start_and_end(self):
        for record in self:
            if len(record.contract_ids) > 0:
                record.next_period_date_start = record.contract_ids[
                    0
                ].next_period_date_start
                record.next_period_date_end = record.contract_ids[
                    0
                ].next_period_date_end

    @api.constrains("contract_ids")
    def constraint_contract_ids(self):
        for record in self:
            contract_list = record.contract_ids

            all_same_project = all(
                element.project_id == contract_list[0].project_id
                for element in contract_list
            )
            if not all_same_project:
                raise ValidationError(
                    _(
                        """
Some of the contract selected are not of the same self-consumption project.

Please make sure that you are invoicing for only the same self-consumption project {project_name}.
"""
                    ).format(
                        project_name=contract_list[0].project_id.selfconsumption_id.name
                    )
                )

            valid_invoicing_mode = ["energy_delivered", "energy_custom"]

            all_invoicing_mode = all(
                element.project_id.selfconsumption_id.invoicing_mode
                in valid_invoicing_mode
                for element in contract_list
            )
            if not all_invoicing_mode:
                raise ValidationError(
                    _(
                        """
Some of the contract selected are not defined as energy delivered self-consumption projects.

Please make sure that you are invoicing the correct self-consumption project.
"""
                    )
                )

            all_equal_period = all(
                element.next_period_date_start
                == contract_list[0].next_period_date_start
                and element.next_period_date_end
                == contract_list[0].next_period_date_end
                for element in contract_list
            )
            if not all_equal_period:
                raise ValidationError(
                    _(
                        """
Select only contracts with the same period of invoicing.
Make sure that all the selected contracts have the same next period start and end.
Next period start: {next_period_date_start}
Next period end: {next_period_date_end}"""
                    ).format(
                        next_period_date_start=contract_list[0].next_period_date_start,
                        next_period_date_end=contract_list[0].next_period_date_end,
                    )
                )

    @api.constrains("power")
    def constraint_power(self):
        for record in self:
            if not record.power or record.power <= 0:
                raise ValidationError(
                    _("You must enter a valid total energy generated (kWh).")
                )

    def generate_invoices(self):
        res = []
        for contract in self.contract_ids:
            invoicing_mode = contract.project_id.selfconsumption_id.invoicing_mode
            template_name = contract.contract_template_id.contract_line_ids[0].name

            if invoicing_mode == "energy_delivered":
                self._process_energy_delivered(contract, template_name, res)
            elif invoicing_mode == "energy_custom":
                self._process_energy_custom(contract, template_name, res)

        return res

    def _process_energy_delivered(self, contract, template_name, res):
        template_name += _("Energy Delivered: {energy_delivered} kWh")
        contract.contract_line_ids.write({
            "name": template_name.format(
                energy_delivered=self.power,
                code=contract.supply_point_assignation_id.supply_point_id.code,
                owner_id=contract.supply_point_assignation_id.supply_point_id.owner_id.display_name,
            )
        })
        res.append(self.with_context(
            {"energy_delivered": self.power}).contract._recurring_create_invoice())

    def _process_energy_custom(self, contract, template_name, res):
        template_name += _("Energy Delivered Custom: {energy_delivered} kWh")
        df = self.parse_csv_file()

        if df is not None:
            for index, row in df.iterrows():
                cau = row.get("CAU")
                if contract.project_id.selfconsumption_id.code == cau:
                    dates = row.get("Periode facturat (dd/mm/aaaa-dd/mm/aaaaa)",
                                    "").split("-")
                    if len(dates) == 2 and contract.next_period_date_start == dates[
                        0] and contract.next_period_date_end == dates[1]:
                        cups = row.get("CUPS")
                        kwh = row.get("Energia a facturar (kWh)")
                        self._update_contract_lines(contract, cups, kwh, template_name)
            res.append(self.with_context(
                {"energy_delivered": self.power}).contract._recurring_create_invoice())

    def _update_contract_lines(self, contract, cups, kwh, template_name):
        for line in contract.contract_line_ids:
            if line.supply_point_assignation_id.supply_point_id.code == cups:
                line.write({
                    "name": template_name.format(
                        energy_delivered=kwh,
                        code=cups,
                        owner_id=contract.supply_point_assignation_id.supply_point_id.owner_id.display_name,
                    )
                })

    def _parse_file(self, data_file):
        logger.info("\n\n _parse_file")
        self.ensure_one()
        try:
            try:
                decoded_file = data_file.decode(self.encoding)
            except UnicodeDecodeError:
                detected_encoding = chardet.detect(data_file).get("encoding", False)
                if not detected_encoding:
                    self.notification(
                        "Error", _("No valid encoding was found for the attached file")
                    )
                    return False, False
                decoded_file = data_file.decode(detected_encoding)

            df = pd.read_csv(
                StringIO(decoded_file),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )
            return df, True
        except Exception:
            logger.warning("Parser error", exc_info=True)
            self.notification("Error", _("Error parsing the file"))
            return False, False
    def parse_csv_file(self):
        logger.info("\n\n parse_csv_file INICIO")
        file_data = base64.b64decode(self.import_file)
        df, not_error = self._parse_file(file_data)
        if not_error:
            logger.info("\n\n parse_csv_file FIN")
            return df
        return False


