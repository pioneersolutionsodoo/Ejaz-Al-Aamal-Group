
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, date


class CertificatePurpose(models.Model):
    _name = 'certificate.purpose'
    _description = 'Certificate Purpose'

    name = fields.Char('Name', required=True, copy=False)
    description = fields.Text('Description')

    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "Class name must be unique",
        ),
    ]


class CertificateRequest(models.Model):
    _name = 'certificate.request'
    _description = 'Employee Certificate Request'
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
    employee_code = fields.Char(related='employee_id.emp_code', readonly=True, string='Employee Code')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', readonly=True, string='Job')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', readonly=True, string='Department')

    mobile = fields.Char(related='employee_id.mobile', readonly=True, string='Mobile No.')
    work_email = fields.Char(related='employee_id.work_email', readonly=True, string='Work Email')
    join_date = fields.Date(related='employee_id.aj_date', readonly=True, string='Date Of Join')
    identification_id = fields.Char(related='employee_id.identification_id', readonly=True, string='Iqama No.')
    country_id = fields.Many2one('res.country', related='employee_id.country_id', readonly=True, string='Nationality')
    work_location_id = fields.Many2one('hr.work.location', related='employee_id.work_location_id', readonly=True, string='Work Location')

    purpose = fields.Many2one('certificate.purpose', string='Purpose', required=True)

    note = fields.Text(string='Notes')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('certificate.request') or _('New')
        return super(CertificateRequest, self).create(vals)


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You cannot delete record which is not in Draft.'))
        return super(CertificateRequest, self).unlink()


    def action_send_request(self):
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


    def action_approve(self):
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

