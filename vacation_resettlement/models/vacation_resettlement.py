from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil import relativedelta


def _get_employee(obj):
    ids = obj.env['hr.employee'].search([('user_id', '=', obj.env.uid)])
    if ids:
        return ids[0]
    else:
        raise UserError(_('The user is not an employee.'))
    return False


class HrContract(models.Model):
    _inherit = 'hr.contract'
    other = fields.Float('Other', help="Specify if the Other.")


class VacationResettlement(models.Model):
    _name = 'vacation.resettlement'
    _rec_name = 'name'
    _inherit = ['mail.thread']
    _description = 'Vacation Resettlement'

    name = fields.Char(string='Number', required=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('vacation.resettlement'))
    employee_no = fields.Char(related='employee_id.emp_code')
    passport_id = fields.Char(related='employee_id.passport_id')
    airline = fields.Char()
    travel_order_no = fields.Char()
    current_salary_status = fields.Char()
    total_services = fields.Char()
    vacation_pay = fields.Char()
    iqama = fields.Char(related='employee_id.identification_id')
    days = fields.Float(compute='_get_vacation_period')
    months = fields.Float(compute='_get_vacation_period')
    years = fields.Float(compute='_get_vacation_period')
    total = fields.Float(compute='_get_vacation_period')
    loan_amount = fields.Float(compute='_get_loan_amount', store=True)
    deduction = fields.Float()
    other_deductions = fields.Float()
    total_deductions = fields.Float(compute='_get_total_deductions', store=True)
    net_pay = fields.Float(compute='_get_net_pay', store=True)
    air_fare_difference = fields.Float()
    note = fields.Text()
    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('hr_manager', _('HR Manager')),
                                        ('finance_manager', 'Finance Manager'),
                                        ('admin_fd', 'Admin Finance Director'),
                                        ('approved', 'Approved'), ], default='draft')

    # Contract Reference fields

    contract_basic = fields.Monetary(related='employee_id.contract_id.wage')
    other_allowance = fields.Float(related='employee_id.contract_id.other')
    house_allowance = fields.Float(related='employee_id.contract_id.housing_allowance')
    transport_allowance = fields.Float(related='employee_id.contract_id.transportation_allowance')
    tel_allowance = fields.Float(related='employee_id.contract_id.mobile_allowance')
    contract_period = fields.Float(related='employee_id.contract_id.contract_period')

    # Date fields
    date = fields.Datetime(default=datetime.now())
    vacation_start_date = fields.Datetime()
    vacation_end_date = fields.Datetime()
    departure_date = fields.Date()
    finish_duty = fields.Date()
    last_date_from_vacation = fields.Date()

    # Relational fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    employee_id = fields.Many2one('hr.employee', default=_get_employee)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    department_id = fields.Many2one('hr.department')
    country_id = fields.Many2one('res.country', related='employee_id.country_id')
    currency_id = fields.Many2one(related='employee_id.contract_id.currency_id')
    vendor_bill_id = fields.Many2one('account.move')
    # ====================================================================================
    hr_manager_id = fields.Many2one('res.users', string='HR Manager')
    account_manager_id = fields.Many2one('res.users', string='Accounting Manager')
    admin_manager_id = fields.Many2one('res.users', string='Admin & Finance Manager')
    # ==============================================================================================
    #       Responsible Notes
    hr_manager_note = fields.Text(string="HR Manager Note", )
    account_manager_note = fields.Text(string="Accounting Manager Note", )
    admin_manager_note = fields.Text(string="Admin & Finance Manager Note", )

    @api.depends('employee_id', 'vacation_start_date', 'vacation_end_date')
    def _get_loan_amount(self):
        loans = self.env['hr.employee.loan.ps'].search(
            [('employee_id', '=', self.employee_id.id), ('state', '=', 'approve')])

        if loans:
            loan_amount = 0.0
            for loan in loans:
                for line in loan.hr_employee_loan_line_ps:

                    if line.state == 'notdeducted':
                        if self.vacation_start_date and line.installment_date and self.vacation_end_date:
                            if self.vacation_start_date.date() <= line.installment_date <= self.vacation_end_date.date():
                                loan_amount += line.amount

            self.loan_amount = loan_amount
        else:
            self.loan_amount = 0

    @api.depends('deduction', 'other_deductions')
    def _get_total_deductions(self):
        self.total_deductions = self.deduction + self.other_deductions

    @api.depends('contract_basic', 'other_allowance', 'house_allowance', 'transport_allowance', 'tel_allowance',
                 'total_deductions', 'loan_amount')
    def _get_net_pay(self):
        allowance = self.contract_basic + self.other_allowance + self.house_allowance + self.transport_allowance + self.tel_allowance
        deduction = self.loan_amount + self.total_deductions
        self.net_pay = allowance - deduction

    @api.depends('vacation_start_date', 'vacation_end_date')
    def _get_vacation_period(self):
        if self.vacation_start_date and self.vacation_end_date:
            date1 = self.vacation_start_date
            date1 = date1.replace(day=1)  # Start from the begging of the month of "vacation_start_date"
            date2 = self.vacation_end_date

            d1 = datetime.strftime(date1, "%m-%d-%Y %H:%M:%S")
            d1 = datetime.strptime(d1, "%m-%d-%Y %H:%M:%S")

            d2 = datetime.strftime(date2, "%m-%d-%Y %H:%M:%S")
            d2 = datetime.strptime(d2, "%m-%d-%Y %H:%M:%S")
            self.total = abs((d2 - d1).days)

            diff = relativedelta.relativedelta(date2, date1)

            self.years = diff.years
            self.months = diff.months
            self.days = diff.days
        else:
            self.total = 0
            self.years = 0
            self.months = 0
            self.days = 0

    def send_request(self):
        self.state = 'hr_manager'
        # Send Notification To HR Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr.group_hr_manager')

    def hr_manager(self):
        self.write({'hr_manager_id': self.env.uid, 'state': 'finance_manager'})
        # Send Notification To Account Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'account.group_account_manager')

    def finance_manager(self):
        self.write({'account_manager_id': self.env.uid, 'state': 'admin_fd'})
        # Send Notification To Admin and financial director
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr_loan_advance.group_admin_fd_user')

    def admin_approve(self):
        if self.employee_id.address_home_id:
            product = self.env['product.product'].search([('barcode', '=', 're20000')])
            if product:

                vendor_bill = self.env['account.move'].create({
                    'partner_id': self.employee_id.address_home_id.id,
                    'move_type': 'in_invoice',
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product.id,
                        'name': product.description,
                        'account_id': product.property_account_expense_id.id,
                        'quantity': 1,
                        'price_unit': self.net_pay,
                    })]
                })
                self.vendor_bill_id = vendor_bill
                self.employee_id.no_payroll = True
                self.write({'admin_manager_id': self.env.uid, 'state': 'approved'})

            else:
                raise UserError(
                    _('You must Create Service Product with Barcode "re20000" for Resettlement'))

        else:
            raise UserError(
                _('Employee %s has no Private Address "Partner" ') % (self.employee_id.name))

    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)

    # # =========================================
    def make_draft(self):
        self.state = 'draft'

    @api.model
    def create(self, values):
        # Add code here
        result = super(VacationResettlement, self).create(values)
        if result.employee_id:
            # Restrict that selected employee should has direct manager
            # if not result.employee_id.parent_id:
            #     raise UserError(_('Employee "%s" has no direct manager !') % result.employee_id.name)

            # Only employee him self and his direct manager can create the leave
            # if result.employee_id.parent_id:
            parent_id = result.employee_id.parent_id.user_id.id
            current_id = self.env.user.id

            if current_id != parent_id:
                if current_id != result.employee_id.user_id.id:
                    raise UserError(
                        _('Only employee him self and his direct manager can create the Vacation Resettlement'))
        return result
