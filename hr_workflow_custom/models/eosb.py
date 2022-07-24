from odoo import fields, models, api, _
from odoo.exceptions import UserError


class EOSB(models.Model):
    _inherit = 'eosb.eosb'

    def action_validate(self):
        res = super(EOSB, self).action_validate()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res
