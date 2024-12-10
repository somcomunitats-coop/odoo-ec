import base64
import logging
from io import StringIO

import chardet
import pandas as pd

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..models.selfconsumption import INVOICING_VALUES

logger = logging.getLogger(__name__)


class InvoicingWizard(models.TransientModel):
    _name = "energy_selfconsumption.invoicing.wizard"
    _description = "Service to generate type invoicing"

    power = fields.Float(string="Total Energy Generated (kWh)")
    contract_ids = fields.Many2many("contract.contract", readonly=True)
    next_period_date_start = fields.Date(
        string="Start",
        compute="_compute_next_period_date_start_and_end",
        readonly=True,
    )
    next_period_date_end = fields.Date(
        string="End",
        compute="_compute_next_period_date_start_and_end",
        readonly=True,
    )
    num_contracts = fields.Integer(
        string="Selected contracts",
        default=lambda self: len(self.env.context.get("active_ids", [])),
    )

    def _get_invoicing_mode(self):
        for contract in self.env["contract.contract"].search(
            [("id", "in", self.env.context.get("active_ids", []))]
        ):
            return contract.project_id.selfconsumption_id.invoicing_mode
        return None

    invoicing_mode = fields.Selection(
        INVOICING_VALUES, string="Invoicing Mode", default=_get_invoicing_mode
    )

    import_file = fields.Binary(string="Import File (*.csv)")
    fname = fields.Char(string="File Name")
    delimiter = fields.Char(
        default=",",
        string="File Delimiter",
        help="Delimiter in import CSV file.",
    )
    quotechar = fields.Char(
        default='"',
        string="File Quotechar",
        help="Quotechar in import CSV file.",
    )
    encoding = fields.Char(
        default="utf-8",
        string="File Encoding",
        help="Encoding format in import CSV file.",
    )

    @api.constrains("import_file")
    def _constrains_import_file(self):
        if self.fname:
            format = str(self.fname.split(".")[-1])
            if format != "csv":
                raise ValidationError(_("Only csv format files are accepted."))

    @api.depends("contract_ids")
    def _compute_next_period_date_start_and_end(self):
        for record in self:
            if (
                len(record.contract_ids) > 0
                and len(record.contract_ids[0].contract_line_ids[0]) > 0
            ):
                main_line = record.contract_ids[0].get_main_line()
                record.next_period_date_start = (
                    main_line.next_period_date_start
                    if main_line
                    else record.contract_ids[0]
                    .contract_line_ids[0]
                    .next_period_date_start
                )
                record.next_period_date_end = (
                    main_line.next_period_date_end
                    if main_line
                    else record.contract_ids[0].next_period_date_end
                )

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
Make sure that all the selected contracts have the same invoicing period, from {next_period_date_start} to {next_period_date_end}.
"""
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
                    _("The energy generated must be greater than 0 (kWh).")
                )

    def generate_invoices(self):
        df, exit_df = self.parse_csv_file()
        res = []
        for contract in self.contract_ids:
            invoicing_mode = contract.project_id.selfconsumption_id.invoicing_mode
            template_name = contract.contract_template_id.contract_line_ids[0].name

            if invoicing_mode == "energy_delivered":
                self._process_energy_delivered(contract, template_name, res)
            elif invoicing_mode == "energy_custom":
                if not exit_df:
                    raise ValidationError(_("CSV file could not be loaded"))
                self._process_energy_custom(df, contract, template_name, res)
        return res

    def _process_energy_delivered(self, contract, template_name, res):
        template_name += _("Energy Delivered: {energy_delivered} kWh")
        contract.contract_line_ids.write(
            {
                "name": template_name.format(
                    energy_delivered=self.power,
                    code=contract.supply_point_assignation_id.supply_point_id.code,
                    owner_id=contract.supply_point_assignation_id.supply_point_id.owner_id.display_name,
                )
            }
        )
        res.append(
            contract.with_context(
                {"energy_delivered": self.power}
            )._recurring_create_invoice()
        )

    def _process_energy_custom(self, df, contract, template_name, res):
        if len(self.contract_ids) != df.shape[0]:
            raise ValidationError(
                _(
                    "The number of contracts selected does not match "
                    "the number of contracts loaded by the csv."
                )
            )
        template_name += _("Energy Delivered Custom: {energy_delivered} kWh")
        main_line = contract.get_main_line()
        if len(contract.contract_line_ids) == 0:
            raise ValidationError(_("The contract has no lines"))
        next_period_date_start = (
            main_line.next_period_date_start
            if main_line
            else contract.contract_line_ids[0].next_period_date_start
        )
        next_period_date_end = (
            main_line.next_period_date_end
            if main_line
            else contract.contract_line_ids[0].next_period_date_end
        )
        row = df[
            (df["CUPS"] == contract.supply_point_assignation_id.supply_point_id.code)
            & (df["CAU"] == contract.project_id.selfconsumption_id.code)
            & (
                df["Periode facturat start (dd/mm/aaaa)"]
                == next_period_date_start.strftime("%d/%m/%Y")
            )
            & (
                df["Periode facturat end (dd/mm/aaaa)"]
                == next_period_date_end.strftime("%d/%m/%Y")
            )
        ]
        if row.empty:
            raise ValidationError(
                _(
                    """
Project (CAU) {cau} :
For CUPS {cups} no data found for period
{next_period_date_start} - {next_period_date_end}"""
                ).format(
                    cau=contract.project_id.selfconsumption_id.code,
                    cups=contract.supply_point_assignation_id.supply_point_id.code,
                    next_period_date_start=next_period_date_start.strftime("%d/%m/%Y"),
                    next_period_date_end=next_period_date_end.strftime("%d/%m/%Y"),
                )
            )
        else:
            indice = row.get("CUPS").index[0]
            cups = row.get("CUPS")[indice]
            kwh = round(
                float(row.get("Energia a facturar (kWh)")[indice].replace(",", ".")), 2
            )
            if kwh <= 0:
                raise ValidationError(
                    _("The energy generated must be greater than 0 (kWh).")
                )
            self._update_contract_lines(contract, cups, kwh, template_name)
            res.append(
                contract.with_context(
                    {"energy_delivered": kwh}
                )._recurring_create_invoice()
            )

    def _update_contract_lines(self, contract, cups, kwh, template_name):
        for line in contract.contract_line_ids:
            line.write(
                {
                    "name": template_name.format(
                        energy_delivered=str(kwh),
                        code=cups,
                        owner_id=contract.supply_point_assignation_id.supply_point_id.owner_id.display_name,
                    ),
                    "quantity": kwh,
                }
            )

    def _parse_file(self, data_file):
        self.ensure_one()
        try:
            try:
                decoded_file = data_file.decode(self.encoding)
            except UnicodeDecodeError:
                detected_encoding = chardet.detect(data_file).get("encoding", False)
                if not detected_encoding:
                    logger.warning(
                        "No valid encoding was found for the attached file",
                        exc_info=True,
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
            return False, False

    def parse_csv_file(self):
        if self.import_file:
            file_data = base64.b64decode(self.import_file)
            return self._parse_file(file_data)
        return False, False

    def download_template_button(self):
        self.ensure_one()
        logger.info("\n\n download_template_button")
        doc_ids = self.contract_ids.ids
        return self.env.ref(
            "energy_selfconsumption.contract_contract_csv_report"
        ).report_action(docids=doc_ids)
