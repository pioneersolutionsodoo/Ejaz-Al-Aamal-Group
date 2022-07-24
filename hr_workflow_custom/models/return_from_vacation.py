from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ReturnFromVacation(models.Model):
    _inherit = 'return.from.vacation'
    state = fields.Selection(selection_add=[('direct_manager', 'Line Manager')])
    d_manager = fields.Many2one(string='Line Manager')


    def hr_manager(self):
        res = super(ReturnFromVacation, self).hr_manager()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res

