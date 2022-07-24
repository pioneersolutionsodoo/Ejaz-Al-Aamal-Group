# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_amount_to_deduct(self, employee_id, date_from, date_to):

        visa_request = self.env['visa.request'].search(
            [('employee_id', '=', employee_id), ('state', '=', 'approved'), ('visa_start_date', '>=', date_from),
             ('visa_start_date', '<=', date_to)])
        amount = 0.0
        if visa_request:
            for visa in visa_request:
                amount += visa.amount_to_deduct
        return amount
