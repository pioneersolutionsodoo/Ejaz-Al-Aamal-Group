from odoo import fields, models, api, _
from odoo.exceptions import UserError


class VacationResettlement(models.Model):
    _inherit = 'vacation.resettlement'

    def admin_approve(self):
        res = super(VacationResettlement, self).admin_approve()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res

