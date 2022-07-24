
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class MedicalInsuranceUpgrade(models.Model):
    _name = 'medical.insurance.upgrade'
    _description = 'Medical Insurance Upgrade Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_employee(self):
        result = False
        employee_ids = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)])
        if employee_ids:
            result = employee_ids[0]
        return result

    state = fields.Selection([('draft', 'Draft'), ('wait_4_hr_mgr', 'Waiting HRM Approval'), ('approve', 'Approved'), ('refuse', 'Refused'), ('cancel', 'Canceled')],
                             string="Status", tracking=True, readonly=True, default="draft")
    name = fields.Char(string="Name", required=True, copy=False, readonly=True,index=True, default=lambda self:_('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=_get_default_employee)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', readonly=True, string='Department')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', readonly=True, string='Job')

    active_insurance_id = fields.Many2one('medical.insurance', readonly=True, store=True, string='Current Active Insurance')
    insurance_provider_id = fields.Many2one('medical.insurance.provider', readonly=True, store=True, string='Current Provider')
    insurance_class_id = fields.Many2one('medical.insurance.class', readonly=True, store=True, string='Current Class')
    insurance_expiry_date = fields.Date(string='Insurance Expiry Date', readonly=True, store=True)

    reason = fields.Text(string='Reason', required=True)

    new_insurance_provider_id = fields.Many2one('medical.insurance.provider', string='New Provider', required=True)
    new_insurance_class_id = fields.Many2one('medical.insurance.class', string='New Class', required=True)



    @api.onchange('employee_id')
    def get_insurance_date(self):
        self.active_insurance_id = self.employee_id.active_insurance_id
        self.insurance_provider_id = self.active_insurance_id.insurance_provider_id
        self.insurance_class_id = self.active_insurance_id.insurance_class_id
        self.insurance_expiry_date = self.active_insurance_id.insurance_expiry_date


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('medical.insurance.upgrade') or _('New')
        return super(MedicalInsuranceUpgrade, self).create(vals)


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You cannot delete record which is not in Draft.'))
        return super(MedicalInsuranceUpgrade, self).unlink()


    def action_send_request(self):
        if not self.active_insurance_id:
            raise UserError(_('The selected employee doesn\'t have an active medical insurance to upgrade'))

        self.state = 'wait_4_hr_mgr'
        users = self.env['res.users'].search([])
        hrm_users = [user for user in users if user.has_group('hr.group_hr_manager')]
        UID_ROOT = 1
        email_from = self.env['res.users'].sudo().browse(UID_ROOT).login
        subject = str(self._description) + ' ' + self.name
        for manager in hrm_users:
            body = _("Hello, %s \n\n" % manager.name)
            body += _("Employee %s has a new %s waiting for your approval,\n") % (self.employee_id.name, self._description)
            body += _("Please take necessary steps.\n\n")
            self.send_email(email_from, manager.work_email, subject, body)

        self.send_notification(self._description, self._name, self.id, self.name, 'hr.group_hr_manager')

    # def push_popup(self):
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {'title': 'Done',
    #                    'message': 'Request sent Successfully',
    #                    'sticky': False,
    #                    'type': 'success', },
    #     }


    def action_approve(self):
        if not self.active_insurance_id:
            raise UserError(_('The selected employee doesn\'t have an active medical insurance to upgrade'))
        if self.insurance_provider_id:
            self.active_insurance_id.insurance_provider_id = self.new_insurance_provider_id.id
        if self.insurance_class_id:
            self.active_insurance_id.insurance_class_id = self.new_insurance_class_id.id

        self.state = 'approve'
        UID_ROOT = 1
        email_from = self.env['res.users'].sudo().browse(UID_ROOT).login
        subject = str(self._description) + ' ' + self.name
        body = _("Hello, %s\n\n" % self.employee_id.name)
        body += _("Your %s %s has been Approved by HR Manager.\n\nBest Regards.") % (self._description, self.name)
        self.send_email(email_from, self.employee_id.work_email, subject, body)

        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.employee_id.user_id, self._description, self._name, self.id, self.name)


    def action_refuse(self):
        self.state = 'refuse'


    def action_cancel(self):
        self.state = 'cancel'


    def action_draft(self):
        self.state = 'draft'


    def send_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)


    def send_email(self, email_from, email_to, subject, body):
        mail_mail = self.env['mail.mail']
        mail_ids = []
        mail_ids.append(mail_mail.sudo().create({
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': '<pre>%s</pre>' % body}))
        mail_mail.send(mail_ids)
        return True
