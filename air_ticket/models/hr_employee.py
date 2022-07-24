from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Relational Fields
    air_ticket_ids = fields.One2many('air.ticket', 'employee_id')

    # @api.model
    # def deduct_ticket_difference(self, employee_id, date_from, date_to):
        # tickets = self.env['air.ticket'].search([('state', '=', 'approved'), ('employee_id', '=', employee_id)])
        # deduct_ticket_difference = 0.0

        # if tickets:
        #     for line in tickets:
        #         deduct_ticket_difference += line.deduct_ticket_difference_in_salary
        #
        # return deduct_ticket_difference
