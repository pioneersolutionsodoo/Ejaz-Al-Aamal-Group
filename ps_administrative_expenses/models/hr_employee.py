from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_administrative_expenses(self, employee_id, date_from, date_to):

        administrative_expenses = self.env['administrative.expenses'].search(
            [('employee_id', '=', employee_id), ('state', '=', 'approved'), ('date', '>=', date_from),
             ('date', '<=', date_to)])
        amount = 0.0
        if administrative_expenses:
            for expenses in administrative_expenses:
                amount += expenses.amount
        return amount
