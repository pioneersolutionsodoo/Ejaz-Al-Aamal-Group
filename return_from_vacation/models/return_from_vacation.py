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


class ReturnFromVacation(models.Model):
    _name = 'return.from.vacation'
    _rec_name = 'name'
    _inherit = ['mail.thread']
    _description = 'Return From Vacation'

    name = fields.Char(string='Number', required=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('return.from.vacation'))
    employee_no = fields.Char(related='employee_id.emp_code')
    number_of_delay_days = fields.Float()
    not_returning_from_leave = fields.Boolean()
    is_direct_manager = fields.Boolean(compute='check_if_direct_manager')
    show_direct_manager_button = fields.Boolean(compute='get_show_direct_manager_button')
    note = fields.Text()
    vacation_type = fields.Selection(selection=[('annual', _('Annual')),
                                                ('emergency', _('Emergency Leave')), ], default='annual')
    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('direct_manager', _('Direct Manager')),
                                        ('hr_manager', _('HR Manager')),
                                        ('approved', 'Approved'), ], default='draft')

    # Date fields
    date = fields.Datetime(default=datetime.now())
    return_from_leave = fields.Datetime()

    # Relational fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    employee_id = fields.Many2one('hr.employee', default=_get_employee)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    department_id = fields.Many2one('hr.department')
    project_id = fields.Many2one('project.project')
    hr_leave = fields.Many2one('hr.leave')
    # ==============================================================================================
    d_manager = fields.Many2one('res.users', string="Direct Manager")
    hr_manager_id = fields.Many2one('res.users', string='HR Manager')
    d_manager_note = fields.Text(string="Direct Manager Note", )
    hr_manager_note = fields.Text(string="HR Manager Note", )

    def send_request(self):
        self.state = 'direct_manager'
        # Send Notification To Direct Manager
        self.sending_notification(self._description, self._name, self.id, self.name, 'direct_manager')

    def direct_manager(self):
        self.write({'d_manager': self.env.uid, 'state': 'hr_manager'})
        # Send Notification To HR Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr.group_hr_manager')

    def hr_manager(self):
        self.employee_id.no_payroll = False
        self.write({'hr_manager_id': self.env.uid, 'state': 'approved'})

    @api.depends('employee_id')
    def check_if_direct_manager(self):
        self.is_direct_manager = False
        self.show_direct_manager_button = False

        if self.employee_id:
            if self.employee_id.parent_id:
                if self.env.user.id == self.employee_id.parent_id.user_id.id:
                    self.is_direct_manager = True

                    if self.state == 'direct_manager':
                        self.show_direct_manager_button = True

    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)

    @api.model
    def create(self, values):
        # Add code here
        result = super(ReturnFromVacation, self).create(values)
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
                            _('Only employee him self and his direct manager can create the Return From Vacation Request'))

        return result
