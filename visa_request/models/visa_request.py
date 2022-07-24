# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


def _get_employee(obj):
    ids = obj.env['hr.employee'].search([('user_id', '=', obj.env.uid)])
    if ids:
        return ids[0]
    else:
        raise UserError(_('The user is not an employee.'))
    return False


class VisaRequest(models.Model):
    _name = 'visa.request'
    _rec_name = 'name'
    _inherit = ['mail.thread']
    _description = 'Visa Request'

    name = fields.Char(string='Number', required=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('visa.request'))
    employee_no = fields.Char(related='employee_id.emp_code')
    visa_duration = fields.Char()
    beneficiary = fields.Boolean()
    quantity = fields.Integer()
    total_amount = fields.Float()
    visa_allowed_allowance = fields.Float(related='employee_id.contract_id.rentry_allowance')
    visa_already_taken = fields.Boolean(compute='get_visa_already_taken')
    is_direct_manager = fields.Boolean(compute='check_if_direct_manager')
    show_direct_manager_button = fields.Boolean(compute='get_show_direct_manager_button')
    amount_to_deduct = fields.Float()
    difference = fields.Float(compute='get_difference_from_total_amount')
    note = fields.Text()
    type = fields.Selection(selection=[('single', _('Single')),
                                       ('multiple', _('Multiple')), ], default='single')
    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('direct_manager', 'Direct Manager'),
                                        ('hr_manager', _('HR Manager')),
                                        ('approved', 'Approved'), ], default='draft')

    # Date fields
    date = fields.Datetime(default=datetime.now())
    vacation_start_date = fields.Date()
    vacation_end_date = fields.Date()
    visa_start_date = fields.Date()

    # Relational fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    employee_id = fields.Many2one('hr.employee', default=_get_employee)
    project_id = fields.Many2one('project.project')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    department_id = fields.Many2one('hr.department')
    # ================================================================
    d_manager = fields.Many2one('res.users', string="Direct Manager")
    hr_manager_id = fields.Many2one('res.users', string='HR Manager')
    d_manager_note = fields.Text(string="Direct Manager Note", )
    hr_manager_note = fields.Text(string="HR Manager Note", )

    @api.model
    def create(self, values):
        # Add code here
        result = super(VisaRequest, self).create(values)
        if result.employee_id:
            # Restrict that selected employee should has direct manager
            if not result.employee_id.parent_id:
                raise UserError(_('Employee "%s" has no direct manager !') % result.employee_id.name)

            # Only employee him self and his direct manager can create the leave
            elif result.employee_id.parent_id:
                parent_id = result.employee_id.parent_id.user_id.id
                current_id = self.env.user.id

                if current_id != parent_id:
                    if current_id != result.employee_id.user_id.id:
                        raise UserError(
                            _('Only employee him self and his direct manager can create the Visa Request'))

        return result

    @api.onchange('vacation_start_date', 'vacation_end_date')
    def onchange_vacation_dates(self):
        if self.vacation_start_date and self.vacation_end_date:
            if self.vacation_end_date < self.vacation_start_date:
                raise UserError(
                    _('Vacation Start Date Should be less than Vacation End Date'))

    @api.depends('employee_id')
    def check_if_direct_manager(self):
        self.is_direct_manager = False

        if self.employee_id:
            if self.employee_id.parent_id:
                if self.env.user.id == self.employee_id.parent_id.user_id.id:
                    self.is_direct_manager = True

    @api.depends('employee_id')
    def get_show_direct_manager_button(self):
        self.show_direct_manager_button = False

        if self.state == 'direct_manager' and self.is_direct_manager == True:
            self.show_direct_manager_button = True

    @api.depends('employee_id')
    def get_visa_already_taken(self):
        for item in self:
            if item.visa_allowed_allowance == 0:
                item.visa_already_taken = True
            else:
                item.visa_already_taken = False

    @api.depends('total_amount')
    def get_difference_from_total_amount(self):
        for item in self:
            if item.tota_amount and item.allowed_allowance:
                item.difference = item.tota_amount - item.allowed_allowance
            else:
                item.difference = 0.0

    def send_request(self):
        self.state = 'direct_manager'
        # Send Notification To Direct Manager
        self.sending_notification(self._description, self._name, self.id, self.name, 'direct_manager')

    def direct_manager(self):
        self.write({'d_manager': self.env.uid, 'state': 'hr_manager'})
        # Send Notification To Account Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'account.group_account_manager')

    def hr_manager(self):
        self.write({'hr_manager_id': self.env.uid, 'state': 'approved'})

    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)
