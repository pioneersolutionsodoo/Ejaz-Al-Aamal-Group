from odoo import fields, models, api, _
from odoo.exceptions import UserError


class HrClearance(models.Model):
    _inherit = 'hr.employee.clearance'
    state = fields.Selection(selection_add=[('direct_manager', 'Line Manager')])
    # is_direct_hrm_approve = fields.Boolean('HR Manager override the line manager approval')
    d_manager = fields.Many2one(string='Line Manager')

    def admin_approve(self):
        res = super(HrClearance, self).admin_approve()
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)
        return res
