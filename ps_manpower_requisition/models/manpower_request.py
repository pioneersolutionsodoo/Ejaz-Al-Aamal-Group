
from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError


class QualificationLine(models.Model):
    _name = 'qualification.line'
    _description = 'Qualification'

    name = fields.Char(string="Title", required=True,)
    type = fields.Selection([('degree', 'Degree'), ('diploma', 'Diploma')], string="Type", required=True)
    description = fields.Text(string="Description")
    manpower_request_id = fields.Many2one('manpower.request', string="Manpower Request", required=True)


class ManpowerRequest(models.Model):
    _name = 'manpower.request'
    _description = 'Manpower Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", required=True, copy=False, readonly=True,index=True, default=lambda self:_('New'))
    state = fields.Selection([('draft', 'Draft'), ('wait_4_hr_mgr', 'Waiting HRM Approval'), ('approve', 'Approved'), ('refuse', 'Refused'), ('cancel', 'Canceled')],
                             string="Status", tracking=True, readonly=True, default="draft")

    position_id = fields.Many2one('hr.job', string='Position Title', required=True)
    position_number = fields.Integer(string='Position Number')
    date = fields.Date(string='Date')
    section = fields.Char(string='Section')
    dept_id = fields.Many2one('hr.department', related='position_id.department_id', readonly=True, string='Division / Department')
    within_budget = fields.Selection([('y', 'Yes'), ('n', 'No')], string="Within Budget")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cost Center')
    reporting_to = fields.Many2one('hr.employee', string='Reporting To')
    total_required = fields.Integer(string='Total Required', required=True)
    work_location = fields.Char(string='Work Location')
    replacement = fields.Selection([('y', 'Yes'), ('n', 'No')], string="Replacement")
    employee_id = fields.Many2one('hr.employee', string='Employee Name')
    employee_code = fields.Char(related='employee_id.emp_code', readonly=True, string='Employee Code')
    date_required_by = fields.Date(string='Date Required by')

    years_of_experience = fields.Char(string='Years of Experience')
    justification_if_not_in_budget = fields.Text(string='Justification if not in budget')
    comments_additional_requirements = fields.Text(string='Comments / Additional Requirements')

    qualification_line_ids = fields.One2many('qualification.line', 'manpower_request_id', string="Qualifications")

    approved_by = fields.Many2one('res.users', string='Approved By')
    approve_date = fields.Datetime(string='Approve Date')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('manpower.request') or _('New')
        return super(ManpowerRequest, self).create(vals)


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You cannot delete record which is not in Draft.'))
        return super(ManpowerRequest, self).unlink()


    def action_send_request(self):
        self.state = 'wait_4_hr_mgr'
        users = self.env['res.users'].search([])
        hrm_users = [user for user in users if user.has_group('hr.group_hr_manager')]
        UID_ROOT = 1
        email_from = self.env['res.users'].sudo().browse(UID_ROOT).login
        subject = str(self._description) + ' ' + self.name
        for manager in hrm_users:
            body = _("Hello, %s \n\n" % manager.name)
            body += _("A new %s %s waiting for your approval,\n") % (self._description, self.name)
            body += _("Please take necessary steps.\n\n")
            self.send_email(email_from, manager.work_email, subject, body)

        self.send_notification(self._description, self._name, self.id, self.name, 'hr.group_hr_manager')


    def action_approve(self):
        self.state = 'approve'
        self.approved_by = self.env.uid
        self.approve_date = fields.Datetime.now()
        UID_ROOT = 1
        email_from = self.env['res.users'].sudo().browse(UID_ROOT).login
        subject = str(self._description) + ' ' + self.name
        body = _("Hello, %s\n\n" % self.create_uid.name)
        body += _("Your %s %s has been Approved by HR Manager.\n\nBest Regards.") % (self._description, self.name)
        self.send_email(email_from, self.create_uid.partner_id.email, subject, body)

        mail_channel = self.env['mail.channel']
        mail_channel.sudo().notify_user_by_approval(self.create_uid, self._description, self._name, self.id, self.name)


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


    @api.model
    def is_curr_user_line_mgr_or_dept_mgr(self):
        departments = self.env['hr.department'].search_count([('manager_id', '=', self.env.uid)])
        employees = self.env['hr.employee'].search_count([('parent_id.user_id.id', '=', self.env.uid)])
        if departments > 0 or employees > 0 or self.env.user.has_group('hr.group_hr_manager'):
            return True
        else:
            return False


    @api.model
    def open_views(self):
        allow = self.is_curr_user_line_mgr_or_dept_mgr()
        if not allow:
            raise AccessError(_("You don\'t have the permission to access Manpower Requisition Model, Only Department/Line Managers have access."))
        # return self.env.ref('ps_manpower_requisition.action_manpower_request').read()[0]
        return {
            'name': _('Manpower Request'),
            'res_model': 'manpower.request',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'help': '<p class="o_view_nocontent_smiling_face">Create a new Manpower Request</p>',
        }
