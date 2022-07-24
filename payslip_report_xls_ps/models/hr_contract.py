# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrContract(models.Model):
    # _name = 'hr.contract'
    _inherit = 'hr.contract'

    other = fields.Float('Other', help="Specify if the Other.")

    # Relational Fields
    analytic_account_id = fields.Many2one('account.analytic.account',related='employee_id.project_name.analytic_account_id')

