from odoo import api, fields, models, _
from odoo.exceptions import UserError


class hrcontracthistory(models.Model):
    _inherit = 'hr.contract.history'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Cost Center')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    air_ticket_allowance = fields.Float(string="Air Ticket Allowance")

    @api.onchange('air_ticket_allowance')
    def check_air_ticket_allowance(self):
        if self.air_ticket_allowance > 2000:
            raise UserError(_('The maximum limit of Air Ticket Allowance is 2000 SAR!'))
