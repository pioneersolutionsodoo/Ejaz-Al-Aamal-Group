from odoo import fields, models, api


class EmployeeMemo(models.Model):
    _inherit = 'employee.memo'

    to = fields.Char(string='To')
    bank = fields.Char(string='Bank')
    country_id = fields.Many2one(comodel_name='res.country', string='Country', related="employee_id.country_id")
    identification_id = fields.Char(string='Identification ID', related="employee_id.identification_id")
    iqama_national_id = fields.Char(string='Iqama Number', related="employee_id.identification_id")
    # job_title = fields.Char(string='Job Title', related="employee_id.job_title")
    aj_date = fields.Date(string='Date of Join', related="employee_id.aj_date")
    total = fields.Float(string='Total Salary', related="employee_id.contract_id.total")
