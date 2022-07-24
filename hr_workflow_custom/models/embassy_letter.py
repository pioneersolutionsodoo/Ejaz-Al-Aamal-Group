from odoo import fields, models, api, _
from odoo.exceptions import UserError


class EmbassyLetter(models.Model):
    _inherit = 'embassy.letter'

    def hr_manager(self):
        res = super(EmbassyLetter, self).hr_manager()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res

