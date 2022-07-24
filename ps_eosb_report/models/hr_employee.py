from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import except_orm, Warning, RedirectWarning


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    reward_yearly = fields.One2many(comodel_name="reward.yearly", inverse_name="employee_id", string="Yearly Rewards")


class YearlyRewards(models.Model):
    _name = 'reward.yearly'
    _description = 'Reward Yearly Record'

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee")
    year = fields.Integer(string="Year")
    amount = fields.Float(string="Yearly Amount")
