from odoo import api, fields, models 


class PayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    rule_ids = fields.Many2many('hr.salary.rule','payroll_structure','salary_rule')


class SalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=False)
