from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Employee(models.Model):
    _inherit = 'hr.employee'
    parent_id = fields.Many2one(string='Line Manager')


class HrLoan(models.Model):
    _inherit = 'hr.employee.loan.ps'
    state = fields.Selection(selection_add=[('request', 'Waiting for Line Manager approval')])
    direct_manager_id = fields.Many2one(string='Line Manager')


    def action_progress3(self):
        res = super(HrLoan, self).action_progress3()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res





class HrAdvance(models.Model):
    _inherit = 'hr.employee.advance.ps'
    state = fields.Selection(selection_add=[('request', 'Waiting for Line Manager approval')])
    direct_manager_id = fields.Many2one(string='Line Manager')

    def action_progress3(self):
        res = super(HrAdvance, self).action_progress3()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res

