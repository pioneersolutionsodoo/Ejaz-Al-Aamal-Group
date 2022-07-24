
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, date


class BusinessCardType(models.Model):
    _name = 'business.card.type'
    _description = 'Business Card Type'
    _order = "sequence, id"

    name = fields.Char('Name', required=True, copy=False)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=1)
    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "Class name must be unique",
        ),
    ]


class BusinessCardCategory(models.Model):
    _name = 'business.card.category'
    _description = 'Business Card Category'
    _order = "sequence, id"

    name = fields.Char('Name', required=True, copy=False)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=1)
    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "Class name must be unique",
        ),
    ]

class BusinessCard(models.Model):
    _name = 'business.card'
    _description = 'Business Card Request'
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
    document_type = fields.Many2one('business.card.type', string='Document Type', required=True)
    category_id = fields.Many2one('business.card.category', string='Category', required=True)
    description = fields.Text(string='Description')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=_get_default_employee)
    emp_arabic_name = fields.Char(string='Employee AR Name', related='employee_id.arabic_name', readonly=True,)
    employee_code = fields.Char(string='Employee Name', related='employee_id.emp_code', readonly=True,)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', readonly=True, string='Job')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', readonly=True, string='Department')
    mobile = fields.Char(related='employee_id.mobile', readonly=True, string='Mobile')
    work_email = fields.Char(related='employee_id.work_email', readonly=True, string='Email')
    number_of_cards = fields.Integer(string='Number of Cards', required=True)

    note = fields.Text(string='Note')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('business.card') or _('New')
        return super(BusinessCard, self).create(vals)


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You cannot delete record which is not in Draft.'))
        return super(BusinessCard, self).unlink()




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
        subject = str(self._description)+ ' ' + self.name
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
