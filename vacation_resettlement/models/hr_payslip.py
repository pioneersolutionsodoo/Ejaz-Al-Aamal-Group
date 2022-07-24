from odoo import api, fields, models

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # Add domain on employee
    employee_id = fields.Many2one('hr.employee', domain=[('no_payroll','=',False)])


