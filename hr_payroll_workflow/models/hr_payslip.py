# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_from_cancel_to_draft(self):
        invalid_payslips = self.filtered(lambda p: p.state not in ["draft", "cancel"])
        print(f"self: {self}\ninvalid_payslips: {invalid_payslips}")
        if invalid_payslips:
            raise UserError("You can set only canceled payslips to draft.")
        else:
            self.write({'state': 'draft'})

