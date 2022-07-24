# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrContractEmployeeReport(models.Model):
    _inherit = "hr.contract.employee.report"

    eosb = fields.Float('Total EOSB')

    def _query(self, fields='', from_clause='', outer=''):
        fields += """
            , e.total_eosb as eosb"""

        return super(HrContractEmployeeReport, self)._query(fields, from_clause, outer)
