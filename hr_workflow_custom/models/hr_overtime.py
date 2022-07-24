from odoo import fields, models, api, _
from odoo.exceptions import UserError


class HrOvertime(models.Model):
    _inherit = 'hr.overtime.ps'
    state = fields.Selection(selection_add=[('request', 'Waiting for LM Confirm')])
    d_manager = fields.Many2one(string='Line Manager')

    def action_approve(self):
        res = super(HrOvertime, self).action_approve()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res
