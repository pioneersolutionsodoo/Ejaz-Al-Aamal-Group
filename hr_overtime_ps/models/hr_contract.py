# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp


class hr_overtime_type_ps(models.Model):
    _name = 'hr.overtime.type.ps'
    _description = 'hr.overtime.type.ps'

    name = fields.Char(string='Name', required=True, translate=True)
    payslip_compute_type = fields.Selection([('fixed', _('Fixed')), ('by_day', _('By Day')), ('by_hour', _('By Hour'))],
                                            string='Payslip Compute Type', required=True, default='fixed')
    payslip_compute_value = fields.Float()


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    overtime_type_id = fields.Many2one('hr.overtime.type.ps' )

    def overtime_cal(self, employee, date_from, date_to):
        total = 0
        overtime_obj = self.env['hr.overtime.ps']
        overtime_ids = overtime_obj.search(
            [('employee_id', '=', employee), ('date_from', '>=', date_from), ('date_to', '<=', date_to),
             ('state', 'in', ['approve'])])

        for overtime in overtime_ids:
            per_hour_salary = (overtime.contract_id.wage / 30) / 8
            total += (overtime.approved_hours * per_hour_salary) * overtime.ot_per_hour
        return total
