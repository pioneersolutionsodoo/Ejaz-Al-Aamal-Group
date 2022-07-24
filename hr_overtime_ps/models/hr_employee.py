from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_overtime_to_alw(self, employee_id, date_from, date_to):

        overtime_request = self.env['hr.overtime.ps'].search(
            [('employee_id', '=', employee_id), ('state', '=', 'approve'), ('date_from', '>=', date_from),
             ('date_to', '<=', date_to)])
        hours = 0.0
        wage = 0.0
        ot_per_hour = 0.0
        worked_days = 1.0
        worked_hours = 1.0
        if overtime_request:
            for overtime in overtime_request:
                if overtime.contract_id.wage:
                    wage = overtime.contract_id.wage
                    worked_days = overtime.worked_days
                    worked_hours = overtime.worked_hours
                    ot_per_hour = overtime.ot_per_hour
                    hours += overtime.approved_hours

        amount = ((wage / worked_days) / worked_hours) * hours * ot_per_hour
        return amount
