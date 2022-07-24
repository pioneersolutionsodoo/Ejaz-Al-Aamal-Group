from odoo import fields, models, api, _
from odoo.exceptions import UserError


class BusinessTrip(models.Model):
    _inherit = 'hr.business.trip'
    direct_manager_id = fields.Many2one(string='Line Manager')


    def action_approve(self):
        res = super(BusinessTrip, self).action_approve()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res
