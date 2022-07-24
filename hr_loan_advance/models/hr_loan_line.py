# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT



def _get_employee(obj):
    ids = obj.env['hr.employee'].search([('user_id', '=', obj.env.uid)])
    if ids:
        return ids[0]
    else:
        raise ValidationError(_('The user is not an employee.'))
    return False

class hr_employee_loan_line_ps(models.Model):
    _name = 'hr.employee.loan.line.ps'
    _description = 'Loan Lines'

    hr_employee_loan_ps = fields.Many2one('hr.employee.loan.ps', string='HR Employee Loan', required=True,
                                          ondelete='cascade', index=True, )
    name = fields.Char(string='Installment Name', size=64, required=True, index=1, readonly=False,
                       states={'deducted': [('readonly', True)], })
    sequence = fields.Integer(string='Sequence', required=True, readonly=False,
                              states={'deducted': [('readonly', True)], })
    amount = fields.Monetary(string='Current Installment',  required=True,
                          readonly=False, states={'deducted': [('readonly', True)], })
    remaining_value = fields.Monetary(string='Next Period Installment',
                                   required=True, readonly=False, states={'deducted': [('readonly', True)], })
    installment_value = fields.Monetary(string='Amount Already Paid',
                                     required=True, readonly=False, states={'deducted': [('readonly', True)], })
    installment_date = fields.Date(string='Installment Date', index=1, readonly=False,
                                   states={'deducted': [('readonly', True)], })
    confirm = fields.Boolean(string='Confirm', readonly=False, states={'deducted': [('readonly', True)], },
                             default=False)
    state = fields.Selection([('deducted', 'Deducted'), ('notdeducted', 'Not Deducted')], string='Status',
                             readonly=True, default='notdeducted')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)


    def unlink(self):
        if self.state not in ('notdeducted', False):
            raise ValidationError(_('You cannot delete record which is Deducted.'))
        return models.Model.unlink(self)
