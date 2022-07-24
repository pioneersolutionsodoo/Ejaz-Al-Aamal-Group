from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil import relativedelta


def _get_employee(obj):
    ids = obj.env['hr.employee'].search([('user_id', '=', obj.env.uid)])
    if ids:
        return ids[0]
    else:
        raise ValidationError(_('The user is not an employee.'))
    return False


class EmployeeMemo(models.Model):
    _name = 'employee.memo'
    _rec_name = 'name'
    _inherit = ['mail.thread']
    _description = 'Employee Memo'

    name = fields.Char(string='Number', required=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('employee.memo'))
    employee_no = fields.Char(related='employee_id.emp_code')
    job_title = fields.Char(related='employee_id.job_title')
    reason = fields.Html()
    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('hr_manager', _('HR Manger')),
                                        ('approved', 'Approved'), ], default='draft')

    # Date fields
    date = fields.Datetime(default=datetime.now())

    # Relational fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    employee_id = fields.Many2one('hr.employee', default=_get_employee)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    hr_manager_id = fields.Many2one('res.users', string='HR Manager')
    hr_manager_note = fields.Text(string="HR Manager Note", )

    def send_request(self):
        self.state = 'hr_manager'
        self.sending_notification(self._description, self._name, self.id, self.name, 'hr.group_hr_manager')


    def hr_manager(self):
        self.state = 'approved'
        return self.write({'hr_manager_id': self.env.uid})

    @api.model
    def create(self, values):
        # Add code here
        result = super(EmployeeMemo, self).create(values)
        if result.employee_id:
            # Restrict that selected employee should has direct manager
            # if not result.employee_id.parent_id:
            #     raise UserError(_('Employee "%s" has no direct manager !') % result.employee_id.name)

            # Only employee him self and his direct manager can create the leave
            # elif result.employee_id.parent_id:
            parent_id = result.employee_id.parent_id.user_id.id
            current_id = self.env.user.id

            if current_id != parent_id:
                if current_id != result.employee_id.user_id.id:
                    raise UserError(
                        _('Only employee him self and his direct manager can create the Employee Memo Request'))

        return result


    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)