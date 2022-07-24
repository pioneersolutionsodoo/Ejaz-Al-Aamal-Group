# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError, UserError
import dateutil
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class eosb_eosb(models.Model):
    _name = 'eosb.eosb'
    _description = 'End Of Service'
    _inherit = ['mail.thread', 'resource.mixin']

    @api.depends('date')
    def _compute_worked_duration(self):
        for item in self:
            item.no_days = 0
            item.no_months = 0
            item.no_years = 0
            if item.date and item.joined_date:
                start_date = item.joined_date
                end_date = item.date + timedelta(days=1)
                item.worked_days = (end_date - start_date.date()).days
                item.worked_months = (12 * end_date.year + end_date.month) - (12 * start_date.year + start_date.month)
                item.worked_years = relativedelta(end_date, start_date).years
                item.no_days = relativedelta(end_date, start_date).days + 1
                item.no_months = relativedelta(end_date, start_date).months
                item.no_years = relativedelta(end_date, start_date).years
                item.worked_period = str(item.no_years) + ' Years: ' + str(item.no_months) + ' Months: ' + str(
                    item.no_days) + ' Days'
            else:
                item.worked_days = 0
                item.worked_months = 0
                item.worked_years = 0
                item.worked_period = 0
                item.no_days = 0
                item.no_months = 0
                item.no_years = 0
        return

    @api.model
    @api.depends('payslip_line_ids', 'payslip_line_ids.amount', 'eosb_based', 'salary_rules_ids', 'rules_ids',
                 'employee_id', 'contract_id')
    def _compute_salary(self):
        amount = 0
        for item in self:
            if item.eosb_based in ('custom', 'net'):
                amount = sum(
                    line.total for line in item.payslip_line_ids if line.salary_rule_id.category_id.code == 'NET')
            elif item.eosb_based == 'wage':
                amount = item.contract_id.wage + item.contract_id.housing_allowance + item.contract_id.transportation_allowance + item.contract_id.mobile_allowance + item.contract_id.other_allowance
            item.salary = amount

    @api.model
    def _rule_domain(self):
        rule_domain = []
        rule_ids = self.env['hr.salary.rule'].search([])
        rule_domain += [rule.id for rule in rule_ids if rule.category_id.code not in ('BASIC', 'GROSS', 'NET')]
        return [('id', 'in', rule_domain)]

    def _get_default_struct_rule(self, struct_id, rule_domain):
        rule_domain += [rule.id for rule in struct_id.rule_ids if rule.category_id.code in ('BASIC', 'GROSS', 'NET')]
        if struct_id.parent_id: self._get_default_struct_rule(struct_id.parent_id, rule_domain)
        return rule_domain

    @api.depends('rules_ids', 'eosb_based', 'employee_id', 'contract_id')
    def _compute_salary_rules(self):
        self.salary_rules_ids = False
        if self.eosb_based == 'custom':
            rule_domain = []
            #            rule_ids = self.env['hr.salary.rule'].search([])
            if self.contract_id.struct_id:
                rule_domain += self._get_default_struct_rule(self.contract_id.struct_id, rule_domain)
            rule_domain += [rule.id for rule in self.rules_ids]
            self.salary_rules_ids = [(6, 0, [x for x in rule_domain])]

    def _get_eosb_amount(self):
        result = 0
        if (self.employee_id) and self.eosb_emp_type_id:
            eosb_condition = {}
            if self.eosb_type == 'resignation':
                eosb_condition = self.eosb_emp_type_id.eosb_emp_type_resignation
            elif self.eosb_type == 'termination':
                eosb_condition = self.eosb_emp_type_id.eosb_emp_type_termination
            years = self.no_years
            if self.eosb_emp_type_id.period_consider == 'year_month' and self.no_months > 0:
                years += 1
            elif self.eosb_emp_type_id.period_consider == 'year_month_day' and (self.no_months > 0 or self.no_days > 0):
                years += 1

            value = 0
            value2 = []
            temp_year = 0
            for line in eosb_condition:
                if years > temp_year:
                    if line.calculation_type == 'fixed':
                        value = line.value
                        value2 += [(line.year, temp_year, value)]
                    elif line.calculation_type == 'percentage':
                        value = (self.salary * line.value) / 100
                        value2 += [(line.year, temp_year, value)]
                    elif line.calculation_type == 'fraction':
                        value = self.salary / line.value
                        value2 += [(line.year, temp_year, value)]
                    temp_year = line.year
            if self.eosb_emp_type_id.calculate_based == True:
                result = value * years
                if self.eosb_emp_type_id.calculation_consider == 'even_month':
                    if self.no_months > 0: result = (value * (self.no_years)) + ((value / 12) * self.no_months)
                elif self.eosb_emp_type_id.calculation_consider == 'even_day':
                    if self.no_months > 0: result = (value * (self.no_years)) + ((value / 12) * self.no_months)
                    if self.no_days > 0: result += (((value / 12) / 30) * self.no_days)
                elif self.eosb_emp_type_id.calculation_consider == 'actual_year':
                    result = value * (self.no_years)
            else:
                if len(value2) > 0:
                    for i in value2: result += (i[0] - i[1]) * i[2]
                    result = self.currect_eosb_result(i, years, result)
                    if self.eosb_emp_type_id.calculation_consider == 'even_month':
                        if self.eosb_emp_type_id.period_consider in (
                                'year_month', 'year_month_day') and self.no_months > 0:
                            result -= i[2]
                            result += ((i[2] / 12) * self.no_months)
                    if self.eosb_emp_type_id.calculation_consider == 'even_day':
                        if self.eosb_emp_type_id.period_consider in (
                                'year_month', 'year_month_day') and self.no_months > 0:
                            result -= i[2]
                            result += ((i[2] / 12) * self.no_months)
                        if self.no_days > 0: result += (((i[2] / 12) / 30) * self.no_days)
                    if self.eosb_emp_type_id.calculation_consider == 'actual_year':
                        if self.eosb_emp_type_id.period_consider in (
                                'year_month', 'year_month_day') and self.no_months > 0:
                            result -= i[2]
                        elif self.eosb_emp_type_id.period_consider in ('year_month_day') and self.no_days > 0:
                            result -= i[2]
                    #                    print value2[-2][2]
        return result

    def currect_eosb_result(self, i, years, result):
        if years > i[0]: result += (years - i[0]) * i[2]
        if years < i[0]: result -= (i[0] - years) * i[2]
        return result

    def _get_leave_salary_amount(self):
        result = 0
        if self.provide_leave_salary: result = (self.contract_id.wage / 30) * self.employee_id.balance_leave
        return result

    def _get_gross_amount(self):
        result = self._get_eosb_amount() + self.other_allowance
        if self.provide_leave_salary:
            result += self._get_leave_salary_amount()
        return result

    def _get_loan_amount(self):
        loan_ids = self.env['hr.employee.loan.ps'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approve')])
        loan_amount = sum(loan_ids.mapped('balance_amount'))
        return loan_amount or 0

    def _get_advance_amount(self):
        advance_ids = self.env['hr.employee.advance.ps'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approve')])
        advance_amount = sum(advance_ids.mapped('balance_amount'))
        return advance_amount or 0

    def _get_deduction_amount(self):
        result = self.other_deduction
        total_loan = self._get_loan_amount()
        total_advance = self._get_advance_amount()
        return result + total_loan + total_advance

    def _get_net_amount(self):
        result = self._get_gross_amount() - self._get_deduction_amount()
        return result

    @api.depends('salary')
    def _compute_amount(self):
        for item in self:
            item.eosb_amount = item._get_eosb_amount()
            item.leave_salary_amount = item._get_leave_salary_amount()
            item.gross_amount = item._get_gross_amount()
            item.deduction_amount = item._get_deduction_amount()
            item.net_amount = item._get_net_amount()

    def _get_currency(self):
        user = self.env['res.users'].browse([self.env.uid])[0]
        return user.company_id.currency_id

    @api.depends('employee_id')
    def get_employee_details(self):
        for case in self:
            employee = case.employee_id.sudo()
            case.job_id = employee.job_id.id
            case.department_id = employee.department_id.id
            case.eosb_emp_type_id = employee.eosb_emp_type_id.id
            try:
                case.joined_date = employee.aj_date
            except:
                case.joined_date = False  # employee.joined_date
            try:
                case.type_id = employee.type_id.id
            except:
                case.type_id = False  # employee.joined_date
            try:
                case.availed_leave = employee.availed_leave
            except:
                case.availed_leave = 0  # employee.joined_date
            try:
                case.used_leave = employee.used_leave
            except:
                case.used_leave = 0  # employee.joined_date
            try:
                case.balance_leave = employee.balance_leave
            except:
                case.balance_leave = 0  # employee.joined_date

            if not case.leave_type_id:
                case.leave_type_id = False

    name = fields.Char(string='Serial')
    joined_date = fields.Datetime(string='Date of Joined', compute='get_employee_details')
    eosb_type = fields.Selection([('resignation', 'Resignation'), ('termination', 'Termination')], string='EOSB Type')
    eosb_based = fields.Selection([('wage', 'By Wage'), ('net', 'By Net'), ('custom', 'By Custom')],
                                  string='EOSB Based', default='wage')
    type_id = fields.Many2one(comodel_name="hr.employee.type", compute='get_employee_details')
    salary = fields.Float(string="Salary", compute='_compute_salary')
    gen_cur_payslip = fields.Boolean(string='Generate Current month Payslip')
    date = fields.Date(string='Last Worked Date', required=True, default=lambda self: fields.date.today())
    payslip_days = fields.Integer(string='Days', help="Specify if want generate payslip for corresponding days")
    other_allowance = fields.Float(string='Other Allowance')
    other_deduction = fields.Float(string='Other Deduction')
    eosb_amount = fields.Float(string='EOSB Amount', compute='_compute_amount')
    gross_amount = fields.Float(string='Gross Amount', compute='_compute_amount')
    deduction_amount = fields.Float(string='Total Deduction Amount', compute='_compute_amount')
    net_amount = fields.Float(string='Net Amount', compute='_compute_amount')
    provide_leave_salary = fields.Boolean(string='Provide Balance Leave Salary')
    leave_salary_amount = fields.Float(string='Leave Salary Amount', compute='_compute_amount')
    no_days = fields.Integer(string='No of Days Worked', compute='_compute_worked_duration')
    no_months = fields.Integer(string='No of Months Worked', compute='_compute_worked_duration')
    no_years = fields.Integer(string='No of Years Worked', compute='_compute_worked_duration')
    worked_days = fields.Integer(string='No. of Days Worked', compute='_compute_worked_duration')
    worked_months = fields.Integer(string='No. of Months Worked', compute='_compute_worked_duration')
    worked_years = fields.Integer(string='No. of Years Worked', compute='_compute_worked_duration')
    worked_period = fields.Char(string='Worked Period', compute='_compute_worked_duration')
    availed_leave = fields.Float(string='Availed Leave', compute='get_employee_details')
    used_leave = fields.Float(string='Used Leave', compute='get_employee_details')
    balance_leave = fields.Float(string='Balance Leave', compute='get_employee_details')
    hr_manager_date = fields.Datetime(string='HR Confirmed Date', readonly=True)
    admin_manager_date = fields.Datetime(string='Admin Confirmed Date', readonly=True)
    hr_manager_note = fields.Text()
    admin_manager_note = fields.Text()
    note = fields.Text(string='Remarks', readonly=True, states={'draft': [('readonly', False)]})

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('admin_fd', 'Admin And Finance Director'),
        ('validate', 'Validate'),
        ('refuse', 'Refused'),
    ], string='Status', tracking=True, default='draft')

    # Relational Fields
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    job_id = fields.Many2one('hr.job', string="Job", compute='get_employee_details')
    department_id = fields.Many2one('hr.department', string="Department", compute='get_employee_details')
    eosb_emp_type_id = fields.Many2one('eosb.emp.type', string="EOSB Category", compute='get_employee_details')
    contract_id = fields.Many2one('hr.contract', string="Contract", required=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    payslip_id = fields.Many2one('hr.payslip', string="Payslip", readonly=True, states={'draft': [('readonly', False)]})
    payslip_line_ids = fields.One2many(related='payslip_id.line_ids', string="Payslip Lines", readonly=True,
                                       states={'draft': [('readonly', False)]})
    rules_ids = fields.Many2many('hr.salary.rule', string="Payslip Rule", domain=_rule_domain, readonly=True,
                                 states={'draft': [('readonly', False)]})
    salary_rules_ids = fields.Many2many('hr.salary.rule', string="Base Payslip Rule", compute='_compute_salary_rules')
    current_month_payslip_id = fields.Many2one('hr.payslip', string="Current Month Payslip", readonly=True,
                                               states={'draft': [('readonly', False)]})
    current_month_payslip_line_ids = fields.One2many(related='current_month_payslip_id.line_ids',
                                                     string="Current Month Payslip Lines")
    leave_type_id = fields.Many2one('hr.leave', string='Leave Type', compute='get_employee_details')
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True,
                              states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', string="Force Journal", readonly=True,
                                 states={'confirm': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=_get_currency,
                                  readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    hr_manager_id = fields.Many2one('res.users', string='HR Manager', readonly=True)
    admin_manager_id = fields.Many2one('res.users', string='Admin Manager', readonly=True)
    refused_by = fields.Many2one("res.users", readonly=True)

    _sql_constraints = [
        ('employee_id_uniq', 'unique(employee_id,eosb_type)',
         'You cannot create EOSB more than once for each Employee!')]

    @api.constrains('employee_id')
    def _employee_constrains(self):
        if (self.employee_id) and (
                not self.employee_id.address_home_id) and not self.employee_id.address_home_id.property_account_payable_id:
            raise UserError(
                _('The employee must be have a Home Address and Home Address must be have a Account Payable.'))

    @api.constrains('payslip_days')
    def _payslip_days_constrains(self):
        if self.gen_cur_payslip and self.payslip_days >= 0:
            month = self.date.month
            monthdays = [(1, 31), (2, 29), (3, 31), (4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30), (10, 31),
                         (11, 30), (12, 31)]
            day = [val for id, val in monthdays if id == month]
            if self.payslip_days > day[0]:
                raise UserError(_('Invalid Days'))

    @api.model
    def create(self, values):
        print('values', values)
        if values.get('name', 'New') == 'New':
            values['name'] = self.env['ir.sequence'].next_by_code('eosb.eosb') or 'New'
        result = super(eosb_eosb, self).create(values)
        return result

    def unlink(self):
        if self.state not in ('draft', False):
            raise UserError(_('You cannot delete record which is not in Draft.'))
        return models.Model.unlink(self)

    @api.onchange('employee_id', 'eosb_based')
    def _onchange_employee(self):
        self.rules_ids = False
        self.contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)], limit=1,
                                                          order='date_start desc').id

    def compute_sheet(self):
        if not self.employee_id.eosb_emp_type_id: raise UserError(_("Please assign 'EOSB Category' for this employee"))
        if self.eosb_based == 'wage': self.payslip_id.unlink()
        if self.eosb_based in ('net', 'custom') and not self.payslip_id:
            vals = {
                'employee_id': self.employee_id.id,
                'date_from': self.date,  # datetime.strptime(self.date, '%Y-%m-%d').strftime('%Y-%m-01'),
                'date_to': self.date,
                # str(datetime.strptime(self.date, '%Y-%m-%d') + relativedelta(months=+1, day=1, days=-1))[:10],
                'contract_id': self.contract_id.id,
                'struct_id': self.contract_id.struct_id.id,
                'name': ('Salary Slip of %s for EOSB') % (self.employee_id.name),
                'eosb': True,
            }
            if self.eosb_based == 'custom':
                vals.update({'eosb_rules_ids': [(6, 0, [x.id for x in self.salary_rules_ids])]})
            payslip_id = self.env['hr.payslip'].create(vals)
            payslip_id.compute_sheet()
            self.payslip_id = payslip_id.id
            payslip_id.write({'state': 'cancel'})
        elif self.eosb_based in ('net', 'custom') and self.payslip_id:
            self.payslip_id.employee_id = self.employee_id.id
            self.payslip_id.date_from = self.date  # datetime.strptime(self.date, '%Y-%m-%d').strftime('%Y-%m-01')
            self.payslip_id.date_to = self.date  # str(datetime.strptime(self.date, '%Y-%m-%d') + relativedelta(months=+1, day=1, days=-1))[:10]
            self.payslip_id.contract_id = self.contract_id.id
            self.payslip_id.struct_id = self.contract_id.struct_id.id
            self.payslip_id.name = ('Salary Slip of %s for EOSB') % (self.employee_id.name)
            self.payslip_id.eosb = True
            self.payslip_id.eosb_rules_ids = self.salary_rules_ids
            self.payslip_id.compute_sheet()

        return True

    def action_confirm(self):
        self.compute_sheet()
        self.write({'state': 'confirm', 'hr_manager_id': self.env.uid, 'hr_manager_date': fields.date.today()})
        # Send Notification To HR Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr.group_hr_manager')

    def action_admin_fd(self):
        self.write({'state': 'admin_fd', 'admin_manager_id': self.env.uid, 'admin_manager_date': fields.date.today()})
        # Send Notification To Admin and financial director
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr_loan_advance.group_admin_fd_user')

    def action_reset(self):
        self.compute_sheet()
        return self.write({'state': 'draft'})

    def action_validate(self):
        self.compute_sheet()
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        # nazar_obj = self.env['account.nazar']
        company_currency = self.company_id.currency_id.id
        diff_currency_p = self.currency_id.id != company_currency
        if not self.employee_id.address_home_id: raise UserError(_('Please set the home address for employee'))
        ref = self.employee_id.name + '/' + 'EOSB'
        # config = self.env['hr.accounting.config']._get_hr_accounting_config()
        journal_id = self.journal_id
        company_id = self.company_id
        if not journal_id:
            #            raise UserError(_(config_id))
            if company_id.eosb_eosb_journal_id:
                journal_id = company_id.eosb_eosb_journal_id
        if not journal_id:
            msg = 'Set a journal in company - ' + str(company_id.name) + ' or set a force journal.'
            raise UserError(_(msg))
        # move_id = move_obj.create(nazar_obj.account_move_get(self, journal_id, date=fields.datetime.today(), ref=ref, company_id=self.company_id.id))

        vals = {
            'journal_id': journal_id.id,
            'date': fields.datetime.today(),
            # 'period_id': period_obj.find(date)[0],
            'ref': '',
            'company_id': self.company_id.id,
        }

        line1 = [(0, 0, {
            # 'move_id':move_id.id,
            'journal_id': journal_id.id,
            'partner_id': self.employee_id.address_home_id.id,
            'credit': 0,
            'debit': self.net_amount,
            # 'centralisation': 'normal',
            'company_id': self.company_id.id,
            # 'state': 'valid',
            'blocked': False,
            'account_id': journal_id.default_account_id.id,
            # 'period_id':move_id.period_id.id,
            'name': 'Loan',
            'amount_currency': diff_currency_p and self.currency_id.id or False,
            'quantity': 1,

        })]
        line1.append((0, 0, {
            # 'move_id':move_id.id,
            'journal_id': journal_id.id,
            'partner_id': self.employee_id.address_home_id.id,
            'credit': self.net_amount,
            'debit': 0,
            # 'centralisation': 'normal',
            'company_id': self.company_id.id,
            # 'state': 'valid',
            'blocked': False,
            'account_id': self.employee_id.address_home_id.property_account_payable_id.id,
            # 'period_id':move_id.period_id.id,
            'name': '/',
            'amount_currency': diff_currency_p and self.currency_id.id or False,
            'quantity': 1,

        }))
        vals.update({'line_ids': line1})

        move_id = move_obj.create(vals)

        if self.gen_cur_payslip and not self.current_month_payslip_id:
            vals = {
                'employee_id': self.employee_id.id,
                'date_from': self.date,  # datetime.strptime(self.date, '%Y-%m-%d').strftime('%Y-%m-01'),
                'date_to': self.date,
                # str(datetime.strptime(self.date, '%Y-%m-%d') + relativedelta(months=+1, day=1, days=-1))[:10],
                'contract_id': self.contract_id.id,
                'struct_id': self.contract_id.struct_id.id,
                'name': ('Salary Slip of %s') % (self.employee_id.name),
                'eosb_days': self.payslip_days,
            }

            current_month_payslip_id = self.env['hr.payslip'].create(vals)
            current_month_payslip_id.compute_sheet()
            self.current_month_payslip_id = current_month_payslip_id
        elif self.gen_cur_payslip and self.current_month_payslip_id:
            self.current_month_payslip_id.compute_sheet()
        return self.write({'state': 'validate', 'move_id': move_id.id})

    def action_refuse(self):
        return self.write({'state': 'refuse', 'refused_by': self.env.uid})

    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)


class eosb_emp_type(models.Model):
    _name = 'eosb.emp.type'
    _description = 'EOSB EMP Type'

    @api.depends('calculate_based')
    def _get_info(self):
        if self.calculate_based:
            self.calculate_info = 'Calculation Example:\nEmployee Total Worked Years = 10\n2 Years = 1000\n5 Years = 1500\n10 Years = 2000\nCalculated Amount: 2000 * 10 = 20000'
        else:
            self.calculate_info = 'Calculation Example:\nEmployee Total Worked Years = 10\n2 Years = 1000\n5 Years = 1500\n10 Years = 2000\nCalculated Amount: (1000 * 2) + (1500 * 3) + (2000 * 5) = 16500'

        #    name = fields.Char(string='Name', required=True, readonly=True, states={'draft': [('readonly', False)]})
        #    eosb_emp_type_resignation = fields.One2many('eosb.emp.type.resignation', 'eosb_emp_type_resignation_id', string='Employee Resignation Type', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
        #    eosb_emp_type_termination = fields.One2many('eosb.emp.type.termination', 'eosb_emp_type_termination_id', string='Employee Termination Type', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
        #    calculate_based = fields.Boolean(string='Calculation Consider By Bulk of Year', default=False, readonly=True, states={'draft': [('readonly', False)]})
        #    calculate_info = fields.Text(string='Info', compute='_get_info')
        #    period_consider = fields.Selection([('year_only','Years Only'),('year_month','Even Months'),('year_month_day','Even Days')], string='Period Consider for Case Selection', required=True, default='year_only', readonly=True, states={'draft': [('readonly', False)]})
        #    calculation_consider = fields.Selection([('period_year','Period Consider Year'),('actual_year','Actual Year'),('even_month','Even Months'),('even_day','Even Days')], string='Calculation Consider', required=True, default='period_year', readonly=True, states={'draft': [('readonly', False)]})

    name = fields.Char(string='Name', required=True)
    eosb_emp_type_resignation = fields.One2many('eosb.emp.type.resignation', 'eosb_emp_type_resignation_id',
                                                string='Employee Resignation Type', copy=True)
    eosb_emp_type_termination = fields.One2many('eosb.emp.type.termination', 'eosb_emp_type_termination_id',
                                                string='Employee Termination Type', copy=True)
    calculate_based = fields.Boolean(string='Calculation Consider By Bulk of Year', default=False, )
    calculate_info = fields.Text(string='Info', compute='_get_info')
    period_consider = fields.Selection(
        [('year_only', 'Years Only'), ('year_month', 'Even Months'), ('year_month_day', 'Even Days')],
        string='Period Consider for Case Selection', required=True, default='year_only')
    calculation_consider = fields.Selection(
        [('period_year', 'Period Consider Year'), ('actual_year', 'Actual Year'), ('even_month', 'Even Months'),
         ('even_day', 'Even Days')], string='Calculation Consider', required=True, default='period_year')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ],
        'Status', readonly=True, default='draft')

    def validate_lines(self, records, categ):
        temp = 0
        for line in records:
            if categ == 'resignation':
                msg = 'Resignation Year should be ascending'
            else:
                msg = 'Termination Year should be ascending'
            if temp != 0 and temp >= line.year: raise ValidationError(_('Invalid Value %s !' % msg))
            temp = line.year
        return True

    def action_active(self):
        self.validate_lines(self.eosb_emp_type_resignation, 'resignation')
        self.validate_lines(self.eosb_emp_type_termination, 'termination')
        return self.write({'state': 'active'})

    def action_inactive(self):
        return self.write({'state': 'inactive'})

    def action_reactive(self):
        return self.write({'state': 'active'})

    def unlink(self):
        self.ensure_one()
        if self.state not in ('draft', False):
            raise UserError(_('You cannot delete record which is not in Draft.'))
        return models.Model.unlink(self)


class eosb_emp_type_resignation(models.Model):
    _name = 'eosb.emp.type.resignation'
    _description = 'EOSB EMP Type Resignation'

    eosb_emp_type_resignation_id = fields.Many2one('eosb.emp.type', string='EOSB Category', ondelete='cascade',
                                                   index=True, copy=False)
    year = fields.Integer(string='Year', required=True)
    calculation_type = fields.Selection([('fixed', 'Fixed'), ('percentage', 'Percentage'), ('fraction', 'Fraction')],
                                        string='Calculation Type', required=True)
    value = fields.Float(string='Value', required=True)

    @api.constrains('value')
    def _value_constrains(self):
        for rec in self:
            if rec.calculation_type == 'percentage' and rec.value > 100:
                raise UserError(_('Percentage value should be less than or equal 100'))


class eosb_emp_type_termination(models.Model):
    _name = 'eosb.emp.type.termination'
    _description = 'ESOB EMP Type Termination'

    eosb_emp_type_termination_id = fields.Many2one('eosb.emp.type', string='EOSB Category', ondelete='cascade',
                                                   index=True, copy=False)
    year = fields.Integer(string='Year', required=True)
    calculation_type = fields.Selection([('fixed', 'Fixed'), ('percentage', 'Percentage'), ('fraction', 'Fraction')],
                                        string='Calculation Type', required=True)
    value = fields.Float(string='Value', required=True)

    @api.constrains('value')
    def _value_constrains(self):
        for record in self:
            if record.calculation_type == 'percentage' and record.value > 100:
                raise UserError(_('Percentage value should be less than or equal 100'))

# @api.model
#    def create(self, values):
#        raise UserError(_(record_ids))
#        return super(eosb_eosb_type_line, self).create(values)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
