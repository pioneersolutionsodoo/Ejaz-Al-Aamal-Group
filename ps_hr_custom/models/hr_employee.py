from datetime import timedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    emp_code = fields.Char(readonly=False)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if 'emp_code' not in val or val['emp_code'] == 'New':
                next_emp_code = self.env['ir.sequence'].next_by_code('hr.employee')
                while self.search_count([('emp_code', '=', next_emp_code)]) > 0:
                    print(next_emp_code, 'existed!')
                    next_emp_code = self.env['ir.sequence'].next_by_code('hr.employee')
                print(next_emp_code, 'not existed')
                val['emp_code'] = next_emp_code or 'New'
            else:
                if self.search_count([('emp_code', '=', val['emp_code'])]) > 0:
                    raise UserError(_('Employee Code Must be Unique!\nSet its value to ( New ) to let the system generates its sequence!'))

            # Create Partner and assign it to address_home_id
            if 'address_home_id' not in val:
                partner_id = self.env['res.partner'].create({
                    'name': val['name'],
                })
                val['address_home_id'] = partner_id.id
        res = super(HrEmployee, self).create(vals)
        return res

    def write(self, vals):
        if self.search_count([('emp_code', '=', vals.get('emp_code')), ('id', '!=', self.id)]) > 0:
            raise UserError(_('Employee Code Must be Unique!'))
        return super(HrEmployee, self).write(vals)

    @api.model
    def absence_compute(self, employee, date_from, date_to, wage):
        domain = [('employee_id', '=', employee), ('check_in_date', '>=', date_from), ('check_out_date', '<=', date_to)]
        attendance_ids = self.env['hr.attendance'].sudo().search(domain)
        days = self.holidays_number(date_from, date_to)
        # print(f'days: {days}')
        required_hours_month = days['workdays'] * 8
        worked_hours = sum(attendance_ids.mapped('worked_hours'))
        absence = required_hours_month - worked_hours
        day_salary = wage/30
        hour_salary = day_salary/8
        ded = round(absence * hour_salary, 2)
        # print(f'worked_hours: {worked_hours} \nabsence: {absence} '
        #       f'\nday_salary: {day_salary} \nhour_salary: {hour_salary} \nded: {ded}')
        return ded if ded > 0 else 0

    def holidays_number(self, date_from, date_to):
        day_to_check = date_from
        holidays = 0
        workdays = 0
        while day_to_check <= date_to:
            # print(f"day_to_check: {day_to_check.strftime('%a')} - {day_to_check.strftime('%w')} --- {day_to_check}")
            if day_to_check.strftime('%w') in ['5', '6']:
                holidays += 1
            else:
                workdays += 1
            day_to_check += timedelta(days=1)
        return {'holidays': holidays, 'workdays': workdays}


