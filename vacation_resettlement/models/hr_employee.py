from odoo import api, fields, models ,_

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    no_payroll = fields.Boolean('No Payroll', help="Specify if the No Payroll.", groups="hr.group_hr_user")
