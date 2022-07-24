from odoo import api, fields, models ,_
from datetime import datetime
from odoo.exceptions import UserError

class HrLeaves(models.Model):
    _inherit = 'hr.leave'

    check_vacation_resettlement = fields.Integer(compute='_get_vacation_resettlement_number')

    # Relational fields
    vacation_resettlement_id = fields.Many2one('vacation.resettlement')

    def create_vacation_resettlement(self):
        vacation_resettlement_id = self.env['vacation.resettlement'].create({
            'employee_id': self.employee_id.id,
            'vacation_start_date': self.date_from,
            'vacation_end_date': self.date_to,
        })
        self.vacation_resettlement_id = vacation_resettlement_id

    @api.depends('vacation_resettlement_id')
    def _get_vacation_resettlement_number(self):
        if self.vacation_resettlement_id or self.state != 'validate':
            self.check_vacation_resettlement = 1
        else:
            if self.leave_type_id:
                if self.leave_type_id.is_annual:
                    self.check_vacation_resettlement = 0.0
                else:
                    self.check_vacation_resettlement = 1
            else:
                self.check_vacation_resettlement = 1

