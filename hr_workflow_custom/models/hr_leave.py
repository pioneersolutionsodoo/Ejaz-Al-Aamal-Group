from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Hrleave(models.Model):
    _inherit = 'hr.leave'
    state = fields.Selection(selection_add=[('request', 'LM Approval')])
    is_direct_hrm_approve = fields.Boolean('HR Manager override the line manager approval')
    direct_manager_id = fields.Many2one(string='Line Manager')


    def action_approve(self):
        res = super(Hrleave, self).action_approve()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res

