# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    eosb = fields.Boolean(string="EOSB", readonly=True,
                          states={'draft': [('readonly', False)]})
    eosb_days = fields.Integer(string="EOSB Days", readonly=True,
                               states={'draft': [('readonly', False)]})

    # Relational Fields
    eosb_rules_ids = fields.Many2many('hr.salary.rule', string="Payslip Rule EOSB", readonly=True,
                                      states={'draft': [('readonly', False)]})

    def action_payslip_done(self):
        for line in self.line_ids:
            if line.salary_rule_id.name == 'EOSB':
                if not line.salary_rule_id.account_debit and not line.salary_rule_id.account_credit:
                    raise UserError(_('Please Fill account debit and credit in EOSB rule'))

        return super(HrPayslip,self).action_payslip_done()
