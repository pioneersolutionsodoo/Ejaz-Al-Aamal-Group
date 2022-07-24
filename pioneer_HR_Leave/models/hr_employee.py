# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    # ~ def _compute_date(self, date_from, date_to, DATETIME_FORMAT):
    # ~ days = months = years = 0
    # ~ date_to = datetime.strptime(str(date_to),  DATETIME_FORMAT)
    # ~ differents = relativedelta(date_to, date_from, DATETIME_FORMAT)
    # ~ print("########################",date_to,date_from)
    # ~ years = differents.years
    # ~ months = (years * 12) + differents.months
    # ~ #        days = differents.days
    # ~ timedelta = date_to - date_from
    # ~ diff_day = timedelta.days + float(timedelta.seconds) / 86400
    # ~ days = round(math.floor(diff_day))
    # ~ return days, months, years

    #  models.Model._get_external_ids(self)
    # SALAY RULES FUNCTIONALLITY START
    def _get_leave_data(self, aj_date, contract_date, contract_type, basic_contract_type):
        print('aj_date, contract_date, contract_type, basic_contract_type', aj_date, contract_date, contract_type,
              basic_contract_type)
        # 2017-01-01 False employee employee
        leave_earn = 0
        yearly_leave = 0
        now = datetime.now()
        if not aj_date:
            leave_earn = 0
            yearly_leave = 0
            return leave_earn, yearly_leave
        # aj_date = datetime.strptime(aj_date,'%Y-%m-%d') #2017-01-01
        months = (12 * now.year + now.month) - (12 * aj_date.year + aj_date.month)  # (12 * 2019 + 2) - (12*2017+1) = 25
        if not basic_contract_type:
            leave_earn = 0
            yearly_leave = 0
            return leave_earn, yearly_leave
        if not contract_type:
            leave_earn = 0
            yearly_leave = 0
            return leave_earn, yearly_leave
        if basic_contract_type == contract_type:
            if basic_contract_type == 'employee':
                leave_earn = abs(months * 2.50)  # 62.5
                yearly_leave = 30
            elif basic_contract_type == 'worker':
                if months >= 60:
                    remonths = months - 60
                    fsec = abs(60 * 1.75)
                    ssec = abs(remonths * 2.50)
                    leave_earn = abs(fsec + ssec)
                    yearly_leave = 30
                else:
                    leave_earn = abs(months * 1.75)
                    yearly_leave = 21
            else:
                leave_earn = 0
                yearly_leave = 0
            return leave_earn, yearly_leave
        else:
            if not contract_date:
                if basic_contract_type == 'employee':
                    leave_earn = abs(months * 2.50)
                    yearly_leave = 30
                elif basic_contract_type == 'worker':
                    if months >= 60:
                        remonths = months - 60
                        fsec = abs(60 * 1.75)
                        ssec = abs(remonths * 2.50)
                        leave_earn = abs(fsec + ssec)
                        yearly_leave = 30
                    else:
                        leave_earn = abs(months * 1.75)
                        yearly_leave = 21
                else:
                    leave_earn = 0
                    yearly_leave = 0
            else:
                # contract_date = datetime.strptime(contract_date,'%Y-%m-%d')
                if now <= contract_date:
                    if basic_contract_type == 'employee':
                        leave_earn = abs(months * 2.50)
                        yearly_leave = 30
                    elif basic_contract_type == 'worker':
                        if months >= 60:
                            remonths = months - 60
                            fsec = abs(60 * 1.75)
                            ssec = abs(remonths * 2.50)
                            leave_earn = abs(fsec + ssec)
                            yearly_leave = 30
                        else:
                            leave_earn = abs(months * 1.75)
                            yearly_leave = 21
                    else:
                        leave_earn = 0
                        yearly_leave = 0
                else:
                    v1 = 0
                    v2 = 0
                    months1 = (12 * contract_date.year + contract_date.month) - (12 * aj_date.year + aj_date.month)
                    months2 = (12 * now.year + now.month) - (12 * contract_date.year + contract_date.month)
                    if basic_contract_type == 'employee':
                        v1 = abs(months1 * 2.50)
                    elif basic_contract_type == 'worker':
                        if months1 >= 60:
                            remonths = months1 - 60
                            fsec = abs(60 * 1.75)
                            ssec = abs(remonths * 2.50)
                            v1 = abs(fsec + ssec)
                        else:
                            v1 = abs(months1 * 1.75)
                    else:
                        leave_earn = 0
                    if contract_type == 'employee':
                        v2 = abs(months2 * 2.50)
                        yearly_leave = 30
                    elif contract_type == 'worker':
                        if months2 >= 60:
                            remonths = months2 - 60
                            fsec = abs(60 * 1.75)
                            ssec = abs(remonths * 2.50)
                            v2 = abs(fsec + ssec)
                            yearly_leave = 30
                        else:
                            v2 = abs(months2 * 1.75)
                            yearly_leave = 21
                    else:
                        leave_earn = 0
                        yearly_leave = 0
                    leave_earn = abs(v1 + v2)
            return leave_earn, yearly_leave

    def _compute_date(self, date_from, date_to, DATETIME_FORMAT):
        days = months = years = 0
        differents = relativedelta(date_to, date_from)
        years = differents.years
        months = (years * 12) + differents.months
        #        days = differents.days
        # timedelta = datetime.strptime(date_to, DATETIME_FORMAT) - datetime.strptime(date_from, DATETIME_FORMAT)
        diff_day = differents.days + float(differents.seconds) / 86400
        days = round(math.floor(diff_day))
        return days, months, years

    #    def _compute_year_result(self, employee_id, days, months, years, carryover_month):
    #        result = 0
    #        if carryover_month > 0:
    #            mod = months % carryover_month
    #            if mod <> 0:
    #                a = mod / 12.0
    #                result = int(a) * annual_leave
    #                if a > int(a):
    #                    result += annual_leave
    #            else:
    #                result = employee_id.type_id.leave_carryover_year * annual_leave

    #        else:
    #            result = years * annual_leave
    #            if days > 0:
    #                result += annual_leave
    #        return result

    def _compute_year_result(self, employee_id, days, months, years, carryover_month):
        result = 0
        annual_leave = employee_id.type_id.annual_leave
        if carryover_month > 0:
            diva, moda = divmod(months, carryover_month)
            if moda != 0:
                divb, modb = divmod(moda, 12)
                result = divb * annual_leave
                if modb > 0: result += annual_leave
            else:
                result = employee_id.type_id.leave_carryover_year * annual_leave
        else:
            result = years * annual_leave
            if days > 0:
                result += annual_leave

        check_type = months % 12
        if employee_id.type_id.leave_start_month_type == 'every_year' \
                and employee_id.type_id.leave_start_month > 0 and \
                (check_type < employee_id.type_id.leave_start_month
                 or check_type == employee_id.type_id.leave_start_month and days <= 0):
            result -= annual_leave
        return result

    def _compute_month_result(self, employee_id, days, months, years, carryover_month):
        # 775 25 2 12
        print('carryover_month', carryover_month)
        result = 0
        annual_leave = employee_id.type_id.annual_leave  # 2.5
        if carryover_month > 0:
            diva, moda = divmod(months, carryover_month)  # 25,12
            # print('diva, moda', diva, moda)#2,1
            if moda != 0:
                # print ('moda', moda , annual_leave)# 1, 2.5
                result += moda * annual_leave  # 2.5
            else:
                # print ('lcy_al_days', employee_id.type_id.leave_carryover_year , annual_leave)
                lcy_al_days = employee_id.type_id.leave_carryover_year * annual_leave * 12
                result += lcy_al_days
        else:
            result += months * annual_leave
            if days > 0: result += annual_leave
        divb, modb = divmod(months, 12)
        if employee_id.type_id.leave_start_month_type == 'every_year' and employee_id.type_id.leave_start_month > 0 and (
                modb < employee_id.type_id.leave_start_month or modb == employee_id.type_id.leave_start_month and days <= 0):
            result -= annual_leave * 12

        return result

    def _compute_leave(self, employee_id):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        days = months = years = result = mod = a = 0
        annual_leave_type = employee_id.type_id.annual_leave_type  # Month
        leave_start_month = employee_id.type_id.leave_start_month
        # ~ current_date = (datetime.today()).strftime(DATETIME_FORMAT)
        current_date = datetime.today()
        print('@#@##@$#@$#@$#$#@$#@$#@4', type(current_date), type(employee_id.joined_date))
        if employee_id.aj_date and employee_id.type_id:
            days, months, years = self._compute_date(employee_id.joined_date, current_date,
                                                     DATETIME_FORMAT)  # 2017-01-01
            # print ('days, months, years',days, months, years) # 772 25 2
            if (leave_start_month < months) or (leave_start_month == months and days > 0):
                carryover_month = employee_id.type_id.leave_carryover_year * 12  # 12
                if annual_leave_type == 'year':
                    result += self._compute_year_result(employee_id, days, months, years, carryover_month)
                if annual_leave_type == 'month':
                    result += self._compute_month_result(employee_id, days, months, years, carryover_month)
        return result

    @api.depends('aj_date', 'type_id')
    def _compute_availed_leave(self):
        self.availed_leave = self._compute_leave(self)

    @api.depends('availed_leave', 'used_leave')
    def _compute_balance_leave(self):
        for item in self:
            item.balance_leave = item.accumlate_days - item.used_leave

    def _yearly_vacation_days(self):
        for item in self:
            leave_earn, yearly_leave = self._get_leave_data(item.aj_date, item.contract_date, item.contract_type,
                                                            item.basic_contract_type)

            if yearly_leave:
                # result[r.id] = yearly_leave
                item.yearly_vacation_days = str(yearly_leave)
            else:
                item.yearly_vacation_days  = str(yearly_leave)

    def _compute_holidays_count(self):
        self.holidays_count = self.env['hr.leave'].search_count([('employee_id', '=', self.id)])

    def _compute_accumlate_days(self):
        for r in self:
            leave_earn, yearly_leave = self._get_leave_data(r.aj_date, r.contract_date, r.contract_type,
                                                            r.basic_contract_type)
            r.accumlate_days = leave_earn

    def _compute_leave_status(self):
        # Used SUPERUSER_ID to forcefully get status of other user's leave, to bypass record rule
        holidays = self.env['hr.leave'].sudo().search([
            ('employee_id', 'in', self.ids),
            ('date_from', '<=', fields.Datetime.now()),
            ('date_to', '>=', fields.Datetime.now()),
            ('state', 'not in', ('cancel', 'refuse'))
        ])
        leave_data = {}
        for holiday in holidays:
            leave_data[holiday.employee_id.id] = {}
            leave_data[holiday.employee_id.id]['leave_date_from'] = holiday.date_from.date()
            leave_data[holiday.employee_id.id]['leave_date_to'] = holiday.date_to.date()
            leave_data[holiday.employee_id.id][
                'current_leave_state'] = holiday.state == 'approve' and 'validate' or holiday.state
            leave_data[holiday.employee_id.id]['current_leave_id'] = holiday.holiday_status_id.id

        for employee in self:
            employee.leave_date_from = leave_data.get(employee.id, {}).get('leave_date_from')
            employee.leave_date_to = leave_data.get(employee.id, {}).get('leave_date_to')
            employee.current_leave_state = leave_data.get(employee.id, {}).get('current_leave_state')
            employee.current_leave_id = leave_data.get(employee.id, {}).get('current_leave_id')
            employee.is_absent = leave_data.get(employee.id) and leave_data.get(employee.id, {}).get('current_leave_state') not in ['cancel', 'refuse', 'draft']

    # OVERRIDDEN
    current_leave_state = fields.Selection(compute='_compute_leave_status', string="Current Leave Status",
                                           selection_add=[('draft', 'Draft'),
                                                        ('request', 'DM Approval'),
                                                        ('confirm', 'HR-Manager Approval'),
                                                        ('validate1', 'Accounting Manager'),
                                                        ('admin_fd', 'Admin & Finance Director'),
                                                        ('cancel', 'Cancelled'),
                                                        ('refuse', 'Refused'),
                                                        ('validate', 'Approved')])
    # inheirted
    aj_date = fields.Date(string='Joined Date')

    type_id = fields.Many2one('hr.employee.type', string="Type", groups="hr.group_hr_user")
    accumlate_days = fields.Float(string='Accumulated Leave', compute='_compute_accumlate_days',
                                  digits='Decimal Single', groups="hr.group_hr_user", compute_sudo=True)
    availed_leave = fields.Float(string='Availed Leave', compute='_compute_availed_leave',
                                 digits='Decimal Single', groups="hr.group_hr_user")
    used_leave = fields.Float(string='Used Leave', readonly=True,
                              digits='Decimal Single', groups="hr.group_hr_user")
    balance_leave = fields.Float(string='Balance Leave', compute='_compute_balance_leave',
                                 digits='Decimal Single', groups="hr.group_hr_user")
    holidays_count = fields.Integer(string='Leaves', compute='_compute_holidays_count', groups="hr.group_hr_user")
    contract_type = fields.Selection([('employee', 'Employee'), ('worker', 'Worker')], 'Contract Type',
                                     default="employee", groups="hr.group_hr_user")
    basic_contract_type = fields.Selection([('employee', 'Employee'), ('worker', 'Worker')], 'Basic Contract Type',
                                           default="employee", groups="hr.group_hr_user")
    last_vacation_date = fields.Date('Last Vacation Date', groups="hr.group_hr_user")
    yearly_vacation_days = fields.Char(compute='_yearly_vacation_days', string='Yearly Vacation Days', groups="hr.group_hr_user")
    contract_date = fields.Date(groups="hr.group_hr_user")
    joined_date = fields.Datetime(string='Date of Joined', groups="hr.group_hr_user")

    @api.model
    def leave_compute(self, employee, date_from, date_to, deduction_type):
        total = 0
        deduction_ids = self.env['hr.holidays.deduction.summary.saudi'].search(
            [('employee_id', '=', employee), ('date', '>=', date_from), ('date', '<=', date_to),
             ('deduction_type', 'in', deduction_type), ('state', '=', 'undeducted')])
        for record in deduction_ids:
            total += record.amount
        return total

    @api.model
    def overtime_compute(self, employee, date_from, date_to, wage, deduction_type):
        allowance = super(hr_employee, self).overtime_compute(employee, date_from, date_to, wage, deduction_type)
        deduction = self.leave_compute(employee, date_from, date_to, deduction_type)
        total = allowance - deduction
        return total
