# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from pprint import pprint


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Relational Fields
    closed_loan_id = fields.Many2one('hr.employee.loan.ps')
    closed_advance_id = fields.Many2one('hr.employee.advance.ps')

    def action_post(self):
        # Close Loan Manually
        if self.closed_loan_id:
            for line in self.closed_loan_id.hr_employee_loan_line_ps:
                if line.state == 'notdeducted':
                    line.state = 'deducted'
        # Close Advance Manually
        if self.closed_advance_id:
            for line in self.closed_advance_id.hr_employee_advance_line_ps:
                if line.state == 'notdeducted':
                    line.state = 'deducted'

        return super(AccountMove, self).action_post()

    # def button_draft(self):
    #     if self.closed_loan_id:
    #         for line in self.closed_loan_id.hr_employee_loan_line_ps:
    #             if line.state == 'notdeducted':
    #                 line.state = 'deducted'
