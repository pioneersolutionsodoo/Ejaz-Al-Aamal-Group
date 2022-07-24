from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


# class HRAttendance(models.Model):
#     _inherit = 'hr.attendance'
#
#     def _default_employee(self):
#         if self.emp_code:
#             return self.env['hr.employee'].search(
#                 [('emp_code', '=', str(self.emp_code))])
#         else:
#             return False
#
#     emp_code = fields.Char(string='Employee Code', )
#
#     employee_id = fields.Many2one(
#         comodel_name='hr.employee',
#         string='Employee', store=True,
#         compute="onchange_emp_code")
#
#     @api.depends('emp_code')
#     def onchange_emp_code(self):
#         for rec in self:
#             if rec.emp_code:
#                 print(rec.emp_code)
#                 rec.employee_id = self.env['hr.employee'].search(
#                     [('emp_code', '=', str(rec.emp_code))])
#                 print(rec.employee_id)
#             else:
#                 rec.employee_id = False


def _get_employee(obj):
    ids = obj.env['hr.employee'].search([('user_id', '=', obj.env.uid)])
    if ids:
        return ids[0]
    else:
        raise UserError(_('The user is not an employee.'))
    return False


class AirTicket(models.Model):
    _name = 'air.ticket'
    _rec_name = 'name'
    _inherit = ['mail.thread']
    _description = 'Air Ticket'

    name = fields.Char(string='Number', required=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('air.ticket'))
    employee_no = fields.Char(related='employee_id.emp_code')
    # contract_state = fields.Many2one(related='employee_id.contract_id.', string="Contract Status")
    contract_id = fields.Many2one('hr.contract', string='Contract')
    contract_state = fields.Selection(string="Contract Status", related="contract_id.state")
    adults = fields.Integer()
    children = fields.Integer()
    city_from = fields.Char()
    city_to = fields.Char()
    airline = fields.Char()
    total_airfare = fields.Float()
    is_direct_manager = fields.Boolean(compute='check_if_direct_manager')
    show_direct_manager_button = fields.Boolean(compute='get_show_direct_manager_button')
    allocated_air_ticket_allowance = fields.Float(related='employee_id.contract_id.air_ticket_allowance')
    air_ticket_difference = fields.Float()
    deduct_ticket_difference_in_salary = fields.Float()
    note = fields.Text()
    type = fields.Selection(selection=[('vacation', _('Vacation')),
                                       ('others', _('Others')), ], default='vacation')
    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('direct_manager', _('Direct Manager')),
                                        ('hr_manager', _('HR Manager')),
                                        ('finance_manager', 'Finance Manager'),
                                        ('admin_fd', 'Admin Finance Director'),
                                        ('approved', 'Approved'), ], default='draft')

    # Date fields
    date = fields.Datetime(default=datetime.now())
    vacation_start_date = fields.Datetime()
    vacation_end_date = fields.Datetime()
    travel_date_from = fields.Datetime()
    travel_date_to = fields.Datetime()

    # Relational fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    employee_id = fields.Many2one('hr.employee', default=_get_employee)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    department_id = fields.Many2one('hr.department')
    country_from_id = fields.Many2one('res.country')
    country_to_id = fields.Many2one('res.country')
    d_manager = fields.Many2one('res.users', string="Direct Manager", )
    hr_manager_id = fields.Many2one('res.users', string='HR Manager', )
    account_manager_id = fields.Many2one('res.users', string='Accounting Manager', )
    admin_manager_id = fields.Many2one('res.users', string='Admin & Finance Manager', )
    d_manager_date = fields.Date()
    hr_manager_date = fields.Date()
    account_manager_date = fields.Date()
    admin_manager_date = fields.Date()
    # ==============================================================================================
    #       Responsible Notes
    d_manager_note = fields.Text(string="Direct Manager Note", )
    hr_manager_note = fields.Text(string="HR Manager Note", )
    account_manager_note = fields.Text(string="Accounting Manager Note", )
    admin_manager_note = fields.Text(string="Admin & Finance Manager Note", )

    @api.onchange('vacation_start_date', 'vacation_end_date')
    def onchange_vacation_dates(self):
        if self.vacation_start_date and self.vacation_end_date:
            if self.vacation_end_date < self.vacation_start_date:
                raise UserError(
                    _('Vacation Start Date Should be less than Vacation End Date'))

    def unlink(self):
        if self.state != 'draft':
            raise UserError(_('You cannot delete record which is not in Draft.'))
        return super(AirTicket, self).unlink()

    # Override Create
    @api.model
    def create(self, values):
        result = super(AirTicket, self).create(values)
        tickets = self.env['air.ticket'].search([('employee_id', '=', result.employee_id.id), ('id', '!=', result.id)])
        if tickets:
            for ticket in tickets:
                if ticket.type == 'vacation' and result.type == 'vacation':
                    ticket_date = ticket.vacation_start_date.year
                    current_date = result.vacation_start_date.year

                    if ticket_date == current_date:
                        raise UserError(_('Employee %s has already Air Ticket in this year %s') % (
                            result.employee_id.name, current_date))
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
                            _('Only employee him self and his direct manager can create the Air Ticket Request'))

        return result

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

    def send_request(self):
        self.state = 'direct_manager'
        # Send Notification To Direct Manager
        self.sending_notification(self._description, self._name, self.id, self.name, 'direct_manager')

    def direct_manager(self):
        self.write({'d_manager': self.env.uid, 'state': 'hr_manager', 'd_manager_date': fields.Date.today()})
        # Send Notification To HR Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr.group_hr_manager')

    def hr_manager(self):
        self.write({'hr_manager_id': self.env.uid, 'state': 'finance_manager', 'hr_manager_date': fields.Date.today()})
        # Send Notification To Account Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'account.group_account_manager')

    def finance_manager(self):
        self.write(
            {'account_manager_id': self.env.uid, 'state': 'admin_fd', 'account_manager_date': fields.Date.today()})
        # Send Notification To Admin and financial director
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr_loan_advance.group_admin_fd_user')

    def admin_approve(self):
        self.write({'admin_manager_id': self.env.uid, 'state': 'approved', 'admin_manager_date': fields.Date.today()})

    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)

    @api.onchange('employee_id')
    def _onchange_employee(self):
        self.contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)], limit=1,
                                                          order='date_start desc').id
