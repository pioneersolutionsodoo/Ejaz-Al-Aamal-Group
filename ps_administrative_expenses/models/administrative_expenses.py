from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil import relativedelta


class AdministrativeExpenses(models.Model):
    _name = 'administrative.expenses'
    _rec_name = 'name'
    _inherit = ['mail.thread']
    _description = 'Administrative Expenses'

    name = fields.Char(string='Number', default=lambda self: self.env['ir.sequence'].next_by_code('administrative.expenses'))
    amount = fields.Float(related='type_id.amount')
    job_title = fields.Char(related='employee_id.job_title')
    reason = fields.Html()
    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('approved', 'Approved'), ], default='draft')

    # Date fields
    date = fields.Datetime(default=datetime.now())

    # Relational fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    project_id = fields.Many2one(related='employee_id.project_name')
    type_id = fields.Many2one('administrative.expenses.type')
    # ===========================================================================================
    account_manager_id = fields.Many2one('res.users', string='Accounting Manager')
    account_manager_note = fields.Text(string="Accounting Manager Note", )

    def approved(self):
        self.write({'account_manager_id': self.env.uid,'state': 'approved'})


class AdministrativeExpensesType(models.Model):
    _name = 'administrative.expenses.type'
    _rec_name = 'name'
    _description = 'Administrative Expenses Type'

    name = fields.Char(required=True, string=_('Type Name'))
    amount = fields.Float(required=True, string=_('Amount'))
