from odoo import fields, models, api, _
from odoo.exceptions import UserError


class VisaRequest(models.Model):
    _inherit = 'visa.request'
    state = fields.Selection(selection_add=[('direct_manager', 'LM Approval')])
    d_manager = fields.Many2one(string='Line Manager')

    def hr_manager(self):
        res = super(VisaRequest, self).hr_manager()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res
