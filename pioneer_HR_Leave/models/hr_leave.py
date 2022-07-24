# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime, timedelta
from lxml import etree, html

import math
import collections
from odoo import SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.addons.pioneer_HR_Leave.models import ps_br_hr_config_global as hg
from pytz import timezone, UTC
from pprint import pprint

import dateutil


class hr_leave(models.Model):
    _inherit = 'hr.leave'

    def name_get(self):
        res = []
        for leave in self:
            res.append((
                leave.id,
                _("%(person)s on %(name)s on %(date)s",
                  person=leave.employee_id.name,
                  name=leave.name,
                  date=fields.Date.to_string(leave.date_from),
                  )
            ))
        return res

    @api.depends('date_from', 'date_to')
    def _total_minutes(self):
        for rec in self:
            rec.request_leave_days = 0
            rec.deductable_days = 0
            if rec.date_from and rec.date_from:
                start_dt = dateutil.parser.parse(str(rec.date_from)).date()
                finish_dt = dateutil.parser.parse(str(rec.date_to)).date()
                print(start_dt, finish_dt)
                date_format = '%Y-%m-%d'
                a = datetime.strptime(str(start_dt), date_format)
                b = datetime.strptime(str(finish_dt), date_format)
                delta = b - a
                print(delta.days)
                rec.deductable_days = delta.days
                rec.request_leave_days = delta.days

    def write(self, values):
        is_officer = self.env.user.has_group(
            'hr_holidays.group_hr_holidays_user') or self.env.is_superuser() or self.env.user.has_group(
            'base.group_user')
        print(is_officer)
        if not is_officer:
            if any(hol.date_from.date() < fields.Date.today() and hol.employee_id.leave_manager_id != self.env.user for
                   hol in self):
                raise UserError(_('You must have manager rights to modify/validate a time off that already begun'))

        employee_id = values.get('employee_id', False)
        if not self.env.context.get('leave_fast_create'):
            if values.get('state'):
                self._check_approval_update(values['state'])
                if any(holiday.validation_type == 'both' for holiday in self):
                    if values.get('employee_id'):
                        employees = self.env['hr.employee'].browse(values.get('employee_id'))
                    else:
                        employees = self.mapped('employee_id')
                    self._check_double_validation_rules(employees, values['state'])
            if 'date_from' in values:
                values['request_date_from'] = values['date_from']
            if 'date_to' in values:
                values['request_date_to'] = values['date_to']
        result = models.BaseModel.write(self, vals=values)
        if not self.env.context.get('leave_fast_create'):
            for holiday in self:
                if employee_id:
                    holiday.add_follower(employee_id)
        return result

    @api.model
    def _get_employee(self):
        result = False
        employee_ids = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)])
        if employee_ids:
            result = employee_ids[0]
        return result

    @api.depends('write_date', 'employee_id', 'is_direct_hrm_approve', 'leave_type_id')
    def _get_current_user(self):
        for case in self:
            state = case.state
            is_show_dm_request = True
            is_show_behalf_employee = False
            is_direct_manager = False
            is_coach = False
            is_show_confirm = False
            is_show_hrm_approve = False
            employee = case.employee_id.sudo()
            parent = employee.parent_id.sudo()
            group_hr_manager = case.env.user.has_group('hr.group_hr_manager')
            # is_annual= case.leave_type_id.sudo().is_annual

            # if state == 'draft':
            #     if is_annual:
            #         is_show_behalf_employee = True
            #     if not is_annual:
            #         is_show_dm_request = True

            if (employee and parent and parent.user_id) \
                    and parent.user_id.id == case.env.uid:
                is_direct_manager = True
                if state == 'request':
                    is_show_confirm = True
            if (employee and employee.coach_id and employee.coach_id.user_id) \
                    and employee.coach_id.user_id.id == case.env.uid:
                is_coach = True
                if state == 'request':
                    is_show_confirm = True
            if state == 'request' and (is_coach or is_direct_manager):
                is_show_confirm = True

            if case.is_direct_hrm_approve:
                if state == 'request':
                    if group_hr_manager:
                        is_show_hrm_approve = True
            if state == 'confirm':
                if group_hr_manager:
                    is_show_hrm_approve = True

            case.is_show_dm_request = is_show_dm_request
            case.is_show_behalf_employee = is_show_behalf_employee
            case.is_direct_manager = is_direct_manager
            case.is_coach = is_coach
            case.is_show_confirm = is_show_confirm
            case.is_show_hrm_approve = is_show_hrm_approve
            # http://stackoverflow.com/questions/14288498/creating-a-loop-for-two-dates
            # http://stackoverflow.com/questions/2161752/how-to-count-the-frequency-of-the-elements-in-a-list

    def date_range(self, start, end):
        r = (end + timedelta(days=1) - start).days
        return [start + timedelta(days=i) for i in range(r)]

    def make_unique(self, original_list):
        unique_list = []
        # map(lambda x: unique_list.append(x) if (x not in unique_list) else False, original_list)
        for x in original_list:
            if x not in unique_list:
                unique_list.append(x)
        return unique_list

    def _get_official_leave_dates(self):
        DATE_FORMAT = "%Y-%m-%d"
        array_date = []
        official_leave_ids = self.env['hr.official.holidays.saudi'].search([('state', '=', 'approve')])
        for official_leave_id in official_leave_ids:
            date_from_official_leave = official_leave_id.date_from.date()
            date_to_official_leave = official_leave_id.date_to.date()
            array_date += self.date_range(date_from_official_leave.date(), date_to_official_leave.date())
        return self.make_unique(array_date)

    def _get_official_leave(self, date_from, date_to, DATETIME_FORMAT):
        request_leave_dates = self.date_range(date_from, date_to)
        result = [item for item in request_leave_dates if item in self._get_official_leave_dates()]
        return len(result) or 0, result

    def _compute_official_leave(self, date_from, date_to, DATETIME_FORMAT):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        lenresult, result = self._get_official_leave(date_from, date_to, DATETIME_FORMAT)
        return lenresult

    def _compute_weekend_leave(self, contract_id, date_from, date_to, DATETIME_FORMAT):
        attendance_id = []
        attendance_id_unique = []
        result_array = []
        result = 0
        req_off_remianing_dates = []
        if contract_id:
            lenofficial_leave, official_leave = self._get_official_leave(date_from, date_to, DATETIME_FORMAT)
            request_leave_dates = self.date_range(date_from, date_to)
            req_off_remianing_dates = [item for item in request_leave_dates if item not in official_leave]

            if contract_id.resource_calendar_id:
                attendance_ids = self.env['resource.calendar.attendance'].search(
                    [('calendar_id', '=', contract_id.resource_calendar_id.id)])
                for attendance in attendance_ids:
                    attendance_id += attendance.dayofweek
                for i in req_off_remianing_dates:
                    weekday = i.weekday()
                    uattendance_id = self.make_unique(attendance_id)
                    if str(weekday) not in uattendance_id:
                        result += 1
        return result

    @api.depends('date_from', 'date_to', 'employee_id', 'contract_id', 'leave_type_id')
    def _compute_leave_days(self):
        for item in self:
            days = weekend_leave_days = 0
            # item.request_leave_days = 0
            item.request_leave_hours = 0.0
            item.official_leave_days = 0
            item.weekend_leave_days = 0
            item.actual_leave_days = 0
            item.cancel_leave_days = 0
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            if item.date_from and item.date_to:
                days, months, years = item.env['hr.employee']._compute_date(item.date_from, item.date_to,
                                                                            DATETIME_FORMAT)
                # print(days, months, years)
                # item.request_leave_days = days + 1
                date_difference = item.date_to - item.date_from
                # if date_difference.days == 0:
                #     item.request_leave_days = 0
                hours = math.floor(((date_difference).seconds) / 3600)

                item.request_leave_hours = hours

                item.official_leave_days = item._compute_official_leave(item.date_from, item.date_to, DATETIME_FORMAT)
                # if item.contract_id:
                #     weekend_leave_days = item._compute_weekend_leave(item.contract_id, item.date_from, item.date_to,
                #                                                      DATETIME_FORMAT)
                #     item.weekend_leave_days = weekend_leave_days
                # else:
                #     item.weekend_leave_days = 0.0
                # official_leaves = item._compute_official_leave(item.date_from, item.date_to, DATETIME_FORMAT)

                item.actual_leave_days = item.request_leave_days
                item.cancel_leave_days = 0
            else:
                item.weekend_leave_days = 0.0
                item.actual_leave_days = 0.0
                item.cancel_leave_days = 0.0

    @api.depends('employee_id', 'leave_type_id')
    def _get_employee_details(self):
        for item in self:
            employee = item.employee_id.sudo()
            item.department_id = employee.department_id.id or False
            item.job_id = employee.job_id.id or False
            item.aj_date = employee.aj_date
            item.accumlate_days = employee.accumlate_days
            item.used_leave = employee.used_leave
            item.deduction_type = item.leave_type_id.deduction_type
            # deduction = employee.leave_compute(employee.id, self.date_from, self.date_to, ['deduct_salary', 'deduct_salary_leave'])
            item.balance_leave = employee.balance_leave

    @api.depends('leave_type_id')
    def _compute_exceeded_leave_days(self):
        self.exceeded_leave_days = 0
        if self.leave_type_id.max_days_limit > 0:
            self.exceeded_leave_days = self.actual_leave_days - self.leave_type_id.max_days_limit

    def _get_deduct_values(self, deduction_type, records, key_value):
        vals, temp = 0, 0
        percentage = 1
        temp_leave = key_value
        for line in records:
            if temp_leave > 0:
                if temp_leave > (line.days - temp):
                    vals += (line.days - temp) * line.percentage
                else:
                    vals += temp_leave * line.percentage
                temp_leave = temp_leave - (line.days - temp)
                temp += (line.days - temp)
                percentage = line.percentage
        return vals, temp_leave, percentage

    @api.depends('employee_id', 'contract_id', 'leave_type_id', 'date_from', 'date_to', 'deductable_hours')
    def _compute_deduct_values(self):
        vals = 0
        if self.leave_type_id and self.contract_id:
            if self.leave_type_id.deduction_type == 'deduct_salary':
                vals, temp_leave, percentage = self._get_deduct_values('deduct_salary',
                                                                       self.leave_type_id.salary_rule_line,
                                                                       self.actual_leave_days)
                self.deductable_amount = (vals + (temp_leave * percentage)) * (self.contract_id.wage / 30)
                # self.deductable_days = 0.0
                self.deductable_hours = 0.0
            elif self.leave_type_id.deduction_type == 'deduct_leave':
                vals, temp_leave, percentage = self._get_deduct_values('deduct_leave',
                                                                       self.leave_type_id.leave_rule_line,
                                                                       self.actual_leave_days)
                # self.deductable_days = vals + (temp_leave * percentage)
                self.deductable_amount = 0.0
                self.deductable_hours = 0.0
            elif self.leave_type_id.deduction_type == 'deduct_ot':
                vals, temp_leave, percentage = self._get_deduct_values('deduct_ot', self.leave_type_id.ot_rule_line,
                                                                       self.ot_hours)
                self.deductable_hours = vals + (temp_leave * percentage)
                self.deductable_amount = 0.0
                # self.deductable_days = 0.0
            elif self.leave_type_id.deduction_type == 'deduct_salary_leave':
                vals, temp_leave, percentage = self._get_deduct_values('deduct_salary',
                                                                       self.leave_type_id.salary_rule_line,
                                                                       self.actual_leave_days)
                self.deductable_amount = (vals + (temp_leave * percentage)) * (self.contract_id.wage / 30)
                vals, temp_leave, percentage = self._get_deduct_values('deduct_leave',
                                                                       self.leave_type_id.leave_rule_line,
                                                                       self.actual_leave_days)
                # self.deductable_days = vals + (temp_leave * percentage)
                self.deductable_hours = 0.0
            else:
                # To Avoid the "None value Error"
                self.deductable_amount = 0.0
                # self.deductable_days = 0.0
                self.deductable_hours = 0.0
        else:
            # To Avoid the "None value Error"
            self.deductable_amount = 0.0
            # self.deductable_days = 0.0
            self.deductable_hours = 0.0

    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('request', 'DM Approval'),
        ('confirm', 'HR-Manager Approval'),
        ('validate1', 'Accounting Manager'),
        ('admin_fd', 'Admin & Finance Director'),
        ('cancel', 'Cancelled'),
        ('refuse', 'Refused'),
        ('validate', 'Approved')
    ])
    name = fields.Char(string='Description')
    request_leave_days = fields.Integer(compute='_total_minutes')
    request_leave_hours = fields.Float(compute='_compute_leave_days')
    official_leave_days = fields.Integer(string='Official Leave Days', compute='_compute_leave_days')
    weekend_leave_days = fields.Integer(string='Weekend Leave Days', compute='_compute_leave_days')
    actual_leave_days = fields.Integer(string='Actual Leave Days', compute='_compute_leave_days')
    cancel_leave_days = fields.Integer(string='Cancel Leave Days', compute='_compute_leave_days')
    allow_one_time_leave = fields.Boolean(string='Allow One Time Leave Again', default=False)
    allow_max_days_limit = fields.Boolean(string='Allow Exceeding Maximum Days Limit', default=False, )
    excuse_salary_deduction = fields.Boolean(string='Excuse Salary Deduction', default=False)
    excuse_leave_deduction = fields.Boolean(string='Excuse Leave Deduction', default=False)
    excuse_ot_deduction = fields.Boolean(string='Excuse OverTime Deduction', default=False)
    execute_with_negative_leave = fields.Boolean(string='Execute With Negative Leave', default=False)
    exceeded_leave_days = fields.Integer(
        string='Warning !: Exceeded the maximum leave limit of the leave type with days of ',
        compute='_compute_exceeded_leave_days')
    accumlate_days = fields.Float(compute="_get_employee_details", string='Accumulated Leave', compute_sudo=True)
    used_leave = fields.Float(compute="_get_employee_details", string='Used Leave', compute_sudo=True)
    deduction_type = fields.Selection(
        [('full_paid', 'Full Paid'), ('deduct_salary', 'Deduct From Salary'), ('deduct_leave', 'Deduct From Leave'),
         ('deduct_ot', 'Deduct From OT'), ('deduct_salary_leave', 'Deduct From Salary and Leave'), ],
        compute="_get_employee_details", compute_sudo=True)
    deductable_amount = fields.Float(string='Deductable Amount', compute='_compute_deduct_values')
    # deductable_days = fields.Float(string='Deductable Days', readonly=True, compute='_compute_deduct_values')
    deductable_days = fields.Integer(string='Deductable Days', compute='_total_minutes')
    deductable_hours = fields.Float(string='Deductable Hours', compute='_compute_deduct_values')
    balance_leave = fields.Float('Balance Leaves', compute="_get_employee_details", compute_sudo=True)
    ot_hours = fields.Float(string='OverTime Hours')
    contact = fields.Char(string='Contact During Vacation')
    eremployee = fields.Selection([('exit', 'Exit'), ('reentry', 'Re-Entry')], 'Employee state')
    erfamily = fields.Selection([('exit', 'Exit'), ('reentry', 'Re-Entry')], 'Family')

    is_direct_manager = fields.Boolean(string='Is Direct Manager', compute='_get_current_user')
    is_coach = fields.Boolean(string='Is Coach', default=False, compute='_get_current_user')
    is_show_dm_request = fields.Boolean(string='Is Show Request For DM Approval Button', compute='_get_current_user')
    is_show_behalf_employee = fields.Boolean(string='Is Show Approve By Responsible Employee Button',
                                             compute='_get_current_user')
    is_show_confirm = fields.Boolean(string='Is Show Confirm Button', compute='_get_current_user')
    is_show_hrm_approve = fields.Boolean(string='Is Show HR-Manager Approval Button', compute='_get_current_user')
    is_direct_hrm_approve = fields.Boolean('HR Manager override the direct manager approval', copy=False
                                           , default=False)
    direct_manager_note = fields.Text()
    hr_manager_note = fields.Text()
    account_manager_note = fields.Text()
    admin_manager_note = fields.Text()
    gm_manager_note = fields.Text()
    note = fields.Html(string='Note')

    # Date Fields
    date_from = fields.Datetime()
    date_to = fields.Datetime()
    request_date = fields.Datetime(string='Request Date')
    cancel_date = fields.Datetime(string='Cancel Date')
    refused_date = fields.Datetime(string='Refused Date')
    direct_manager_date = fields.Datetime(string='DR. Confirmed Date')
    hr_manager_date = fields.Datetime(string='HR Confirmed Date')
    account_manager_date = fields.Datetime(string='AM Confirmed Date')
    admin_manager_date = fields.Datetime(string='Admin Confirmed Date')
    gm_manager_date = fields.Datetime(string='GM Confirmed Date')
    aj_date = fields.Date(compute="_get_employee_details", string='Actual Date of Joined', compute_sudo=True)

    # Relational Fields
    holiday_status_id = fields.Many2one("hr.leave.type")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=False,
                                  states={'validate': [('readonly', True)], 'cancel': [('readonly', True)],
                                          'refuse': [('readonly', True)]}, default=_get_employee)
    contract_id = fields.Many2one('hr.contract', string='Contract')
    department_id = fields.Many2one('hr.department', string='Department', store=True, compute='_get_employee_details',
                                    compute_sudo=True)
    job_id = fields.Many2one('hr.job', string='Job', store=True, compute='_get_employee_details', compute_sudo=True)
    leave_type_id = fields.Many2one('hr.holidays.type.saudi', string='Leave Type')
    direct_manager_id = fields.Many2one('res.users', string='Direct Manager')
    account_manager_id = fields.Many2one('res.users', string='Account Manager')
    admin_manager_id = fields.Many2one('res.users', string='Admin Manager')
    hr_manager_id = fields.Many2one('res.users', string='HR Manager')
    refused_by = fields.Many2one('res.users', string='Refused By')
    cancel_by = fields.Many2one('res.users', string='Cancelled By')
    behalf_employee_id = fields.Many2one('hr.employee', 'Responsile Employee')
    remp_ids = fields.Many2one('hr.employee', string='Replacement Employee', readonly=False,
                               states={'validate': [('readonly', True)], 'cancel': [('readonly', True)], })
    gm_manager_id = fields.Many2one('res.users', string='GM Manager', readonly=True)
    company_id = fields.Many2one('res.company', string='Employee Company', change_default=True,
                                 required=True, readonly=False,
                                 states={'validate': [('readonly', True)], 'cancel': [('readonly', True)], },
                                 default=lambda self: self.env.company)

    @api.constrains('holiday_allocation_id')
    def _check_allocation_id(self):
        for leave in self:
            if leave.holiday_type == 'employee' and not leave.multi_employee and \
                    leave.holiday_status_id.requires_allocation == 'yes' and not leave.holiday_allocation_id:
                # raise ValidationError(_(
                #     'Could not find an allocation of type %(leave_type)s for the requested time period.',
                #     leave_type=leave.holiday_status_id.display_name,
                # ) + '\n- %s' % (leave.employee_id.name))
                pass

    # default=lambda self: self.env['res.company']._company_default_get('hr.leave'))
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(hr_leave, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        context = dict(self._context or {})
        doc = etree.XML(res['arch'])
        emp_obj = self.env['hr.employee']
        employee_ids = emp_obj.sudo().search([('user_id', '=', self.env.uid)])
        employee = employee_ids and employee_ids[0]
        for node in doc.xpath("//field[@name='employee_id']"):
            domain = hg.return_employee_domain(self, context, [])
            node.set('domain', str(domain))
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    # OVERRIDEED
    def _check_approval_update(self, state):
        pass

    @api.onchange('request_date_from_period', 'request_hour_from', 'request_hour_to',
                  'request_date_from', 'request_date_to',
                  'employee_id')
    def _onchange_request_parameters(self):
        if not self.request_date_from:
            self.date_from = False

        if self.request_unit_half or self.request_unit_hours:
            self.request_date_to = self.request_date_from

        if not self.request_date_to:
            self.date_to = False
        for case in self:
            today = fields.Datetime.today()
            if not case.date_from:
                case.date_from = today
            if not case.date_to:
                case.date_to = today
        return

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        employee = False
        for case in self:
            employee = case.employee_id.sudo()
        if not employee:
            return {'value': {'contract_id': False}}
        contract_ids = self.env['hr.contract'].sudo().search([('employee_id', '=', employee.id)], limit=1,
                                                             order='date_start desc')
        # get the default unpaid time off type
        type_id = self.env['hr.leave.type'].search([], limit=1)
        self.holiday_status_id = type_id and type_id.id or False

        return {'value': {'contract_id': contract_ids and contract_ids.id or False}}

    def get_one_time_leave(self, employee_id, leave_type_id):
        return self.env['hr.leave'].sudo().search(
            [('employee_id', '=', employee_id.id), ('leave_type_id', '=', leave_type_id.id),
             ('state', 'in', ('validate', 'cancel'))])

    def action_approve_behalf(self):
        for case in self:
            behalf_employee_id = case.behalf_employee_id.sudo()
            behalf_employee_user_id = behalf_employee_id.user_id.sudo()
            is_annual = self.leave_type_id.sudo().is_annual
            if not is_annual:
                raise UserError(_('This Approval Is Only For Leave Type : Annual'))

            if is_annual:
                if not behalf_employee_id:
                    raise UserError(_('Add Responsible Employee.'))
                if not behalf_employee_user_id:
                    raise UserError(_('Add Related User To Responsible Employee.'))
                if behalf_employee_user_id.id != self._uid:
                    raise UserError(_('Only Responsible Employee Can Able To Approve.'))
                case.action_request()

    def action_request(self):
        context = dict(self._context or {})
        is_annual = self.leave_type_id.sudo().is_annual
        config = self.env['hr.leave.config.settings'].sudo()._get_values()
        employee = self.employee_id.sudo()
        parent = employee.parent_id.sudo()
        if config and employee and self.leave_type_id:

            if is_annual and config.annual_leave_doj:
                year_bef = datetime.now() - relativedelta(years=1)

                if employee.joined_date and employee.joined_datez > year_bef:
                    raise Warning(_('You are not eligible to apply for Annual Leave!'))
                if not employee.aj_date:
                    raise Warning(_('You are not eligible to apply for Annual Leave!. Please enter joining date'))

            # for checking the validation for annual 5 days leave.
            # todo : how to check for one year
            if self.leave_type_id.is_annual and config.annual_leave:
                rec_ids = self.sudo().search([('leave_type_id.is_annual', '=', True),
                                              ('employee_id', '=', employee.id),
                                              ('id', '!=', self.id)])
                total = sum([r.deductable_days for r in rec_ids])

                if total > 5 and self.deductable_days < 5:
                    raise Warning(_('Annual Vacation should be minimum 5 days'))

        if (employee and self.leave_type_id) and employee.gender != 'female' \
                and self.leave_type_id.female_only:
            raise except_orm(_('Warining!'), _('This leave type strictly applicable only for female.'))
        if ((employee) and parent) and parent.work_email:
            email_from = hg.get_email_from(self)
            if email_from:
                try:
                    subject = ("Leave request from employee of : '%s' ") % (employee.name)
                    body = _("Hello,\n\n")
                    body += _("Employee %s sent leave request at Date from %s to %s, Please take necessary steps..") % (
                        employee.name, self.date_from, self.date_from)
                    body += "--\n"
                    hg.mail_create(self, email_from, parent.work_email, subject, body)
                except Exception:
                    pass
        self.write({'state': 'request', 'request_date': datetime.now()})
        # Send Notification To Direct Manager
        self.sending_notification(self._description, self._name, self.id, self.name, 'direct_manager')

    def action_confirm(self):
        config = hg.get_config(self)
        email_from = hg.get_email_from(self)
        employee = self.employee_id.sudo()
        if email_from:
            if config:
                for manager in config['managers_ids']:
                    subject = ("Leave request from Employee: '%s' ") % (employee.name)
                    body = _("Hello,\n\n")
                    body += _(
                        "Employee %s leave request was confirmed by his direct manager, And its waiting for your approval,Please take necessary steps..") % (
                                employee.name)
                    body += "--\n"
                    if manager.work_email: hg.mail_create(self, email_from, manager.work_email, subject, body)
            if self.env.user.id == employee.user_id.id:
                raise UserError(_('You Cannot Confirm Your Own Request.'))
            if self.user_has_groups('base.group_user') and not (self.is_coach or self.is_direct_manager):
                raise UserError(_('Either Assigned Direct Manager or HR Manager Are Allowed To Confirm'))

            if employee.work_email:
                try:
                    subject = ("Your leave request is waiting for HR Approval")
                    body = _("Hello,\n\n")
                    body += _("Your leave request was confirmed, And its waiting for Officer Approval..")
                    body += "--\n"
                    hg.mail_create(self, email_from, employee.work_email, subject, body)
                except Exception:
                    pass

        self.write({'state': 'confirm', 'direct_manager_id': self.env.uid, 'direct_manager_date': fields.date.today()})
        # Send Notification To HR Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr.group_hr_manager')

    def action_refuse(self):
        email_from = hg.get_email_from(self)
        employee = self.employee_id.sudo()
        parent = employee.parent_id.sudo()
        state = ''
        if self.state == 'request':
            state = 'by Direct Manager'
        elif self.state == 'confirm':
            state = 'by HR Manager'
        if email_from:
            try:
                if employee.work_email:
                    subject = ("Your leave request was refused")
                    body = _("Hello,\n\n")
                    body += _("Your leave request was refused %s") % (state)
                    body += "--\n"
                    hg.mail_create(self, email_from, employee.work_email, subject, body)

                if ((employee) and parent) and parent.work_email and self.state == 'confirm':
                    subject = ("Leave request was refused for employee : '%s' ") % (employee.name)
                    body = _("Hello,\n\n")
                    body += _("Leave request was refused for employee : '%s' %s") % (employee.name, state)
                    body += "--\n"
                    hg.mail_create(self, email_from, parent.work_email, subject, body)
            except Exception:
                pass
        self.write({'state': 'refuse', 'refused_by': self.env.uid, 'refused_date': fields.date.today()})

    def action_cancel(self):
        email_from = hg.get_email_from(self)
        employee = self.employee_id.sudo()
        parent = employee.parent_id.sudo()
        state = ''
        if self.state == 'request':
            state = 'by Direct Manager'
        elif self.state == 'confirm':
            state = 'by HR Manager'
        if email_from:
            try:
                if employee.work_email:
                    subject = ("Your leave request was cancelled")
                    body = _("Hello,\n\n")
                    body += _("Your leave request was cancelled %s") % (state)
                    body += "--\n"
                    hg.mail_create(self, email_from, employee.work_email, subject, body)

                if ((employee) and parent) and parent.work_email and self.state == 'confirm':
                    subject = ("Leave request was cancelled for employee : '%s' ") % (employee.name)
                    body = _("Hello,\n\n")
                    body += _("Leave request was cancelled for employee : '%s' %s") % (employee.name, state)
                    body += "--\n"
                    hg.mail_create(self, email_from, parent.work_email, subject, body)
            except Exception:
                pass
        self.write({'state': 'cancel', 'cancel_by': self.env.uid, 'cancel_date': fields.date.today()})

    # def hr_manager_action_approve(self):
    #     self.write({'state': 'validate1', 'hr_manager_id': self.env.uid, 'hr_manager_date': fields.date.today()})
    #     # Send Notification To Account Manager
    #     self.sending_notification(self._description, self._name, self.id, self.name,
    #                               'account.group_account_manager')

    # def account_manager_action_approve(self):
    #     self.write(
    #         {'state': 'admin_fd', 'account_manager_id': self.env.uid, 'account_manager_date': fields.date.today()})
    #     # Send Notification To Admin and financial director
    #     self.sending_notification(self._description, self._name, self.id, self.name,
    #                               'hr_loan_advance.group_admin_fd_user')

    def action_approve(self):
        employee = self.employee_id.sudo()
        parent = employee.parent_id.sudo()
        amount = 0
        if not self.allow_one_time_leave and self.leave_type_id.one_time_leave and self.get_one_time_leave(employee,
                                                                                                           self.leave_type_id):
            raise except_orm(_('Warining!'), _(
                'The Employee was already utilized the one time leave,Please Allow One Time Leave Again in HR Setting or Refuse.'))

        if not self.allow_max_days_limit and self.exceeded_leave_days > 0:
            raise except_orm(_('Warining!'), _(
                'The Leave is exceeding the maximum limit leave type,Please Allow Exceeding Maximum Days Limit in HR Setting or Refuse.'))

        if self.leave_type_id.female_only and employee.gender != 'female':
            raise except_orm(_('Warining!'), _('This leave type strictly applicable only for female.'))
        #
        # if not self.execute_with_negative_leave and self.leave_type_id.deduction_type in ('deduct_salary',
        #                                                                                   'deduct_salary_leave') and self.deductable_days > employee.balance_leave and not self.excuse_leave_deduction:
        #     raise except_orm(_('Warining!'), _(
        #         'Balance leave is not enough,Please Execute With Negative Leave in HR Setting or Refuse.'))

        if self.leave_type_id.deduction_type in (
                'deduct_salary',
                'deduct_salary_leave') and not self.excuse_salary_deduction and self.deductable_amount > 0:
            amount = self.deductable_amount
        deduction_type = self.leave_type_id.deduction_type or ''
        if deduction_type == 'deduct_ot' \
                and not self.excuse_ot_deduction and self.deductable_hours > 0:
            amount = ((self.contract_id.wage / 30) / 8) * self.deductable_hours

        if amount > 0:
            self.env['hr.holidays.deduction.summary.saudi'].create({
                'employee_id': employee.id,
                'leave_id': self.id,
                'date': self.date_from,
                'amount': amount,
                'state': 'undeducted',
            })

        if self.leave_type_id.deduction_type in ('deduct_leave', 'deduct_salary_leave') \
                and not self.excuse_leave_deduction and self.deductable_days > 0:
            leave = employee.used_leave + self.deductable_days
            employee.write({'used_leave': leave})

        email_from = hg.get_email_from(self)
        if email_from:
            try:
                if ((employee) and parent) and parent.work_email:
                    subject = ("Leave request was approved for employee : '%s' ") % (employee.name)
                    body = _("Hello,\n\n")
                    body += _("Leave request was approved for employee : '%s' by HR Manager") % (employee.name)
                    body += "--\n"
                    hg.mail_create(self, email_from, parent.work_email, subject, body)
                if (employee) and employee.work_email:
                    subject = ("Your leave request was approved")
                    body = _("Hello,\n\n")
                    body += _("Your leave request was approved by HR Manager . Waiting for GM Approval")
                    body += "--\n"
                    hg.mail_create(self, email_from, employee.work_email, subject, body)
            except Exception:
                pass
        self.write({'state': 'validate', 'admin_manager_id': self.env.uid, 'admin_manager_date': fields.date.today()})

    # Override Create Function
    @api.model
    def create(self, values):
        values['state'] = 'draft'
        model = models.BaseModel.create(self,values)

        if model.employee_id:
            # Restrict that selected employee should has direct manager
            if not model.employee_id.parent_id:
                raise UserError(_('Employee "%s" has no direct manager !') % model.employee_id.name)

            # Only employee him self and his direct manager can create the leave
            elif model.employee_id.parent_id:
                parent_id = model.employee_id.parent_id.user_id.id
                current_id = self.env.user.id

                if current_id != parent_id:
                    if current_id != model.employee_id.user_id.id:
                        raise UserError(_('Only employee him self and his direct manager can create the leave'))

        return model

    # Override _onchange_holiday_status_id from odoo standard module hr_holidays
    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        self.request_unit_half = False
        self.request_unit_hours = False
        self.request_unit_custom = False

    # Override _check_holidays from odoo standard module hr_holidays
    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        pass
        # for holiday in self:
        #     holiday.holiday_status_id = False
        #     if holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.holiday_status_id.allocation_type == 'no':
        #         continue
        #     leave_days = holiday.holiday_status_id.get_days(holiday.employee_id.id)[holiday.holiday_status_id.id]
        #     if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or float_compare(
        #             leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
        #         raise ValidationError(
        #             _('The number of remaining time off is not sufficient for this time off type.\n'
        #               'Please also check the time off waiting for validation.'))
        # self.state = 'confirm' if self.validation_type != 'no_validation' else 'draft'

    @api.model
    def default_get(self, fields):
        res = super(hr_leave, self).default_get(fields)
        res['state'] = 'draft'
        type_id = self.env['hr.leave.type'].search([], limit=1)
        res['holiday_status_id'] = type_id and type_id.id or False
        return res

    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)

    @api.depends('direct_manager_id')
    def _compute_state(self):
        for rec in self:
            if not rec.direct_manager_id:
                rec.state = 'draft'
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
