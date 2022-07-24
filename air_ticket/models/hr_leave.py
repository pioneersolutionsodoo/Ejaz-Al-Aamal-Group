from odoo import api, fields, models ,_
from datetime import datetime
from odoo.exceptions import UserError

class HrLeaves(models.Model):
    _inherit = 'hr.leave'

    check_air_ticket = fields.Integer(compute='_get_air_ticket_number')

    # Relational fields
    air_ticket_id = fields.Many2one('air.ticket')

    
    def create_air_ticket(self):

        air_ticket_id = self.env['air.ticket'].create({
            'employee_id': self.employee_id.id,
            'vacation_start_date': self.date_from,
            'vacation_end_date': self.date_to,
        })
        self.air_ticket_id = air_ticket_id

    @api.depends('air_ticket_id')
    def _get_air_ticket_number(self):
        if self.air_ticket_id or self.state != 'validate':
            self.check_air_ticket = 1
        else:
            if self.leave_type_id:
                if self.leave_type_id.is_annual:
                    self.check_air_ticket = 0.0
                else:
                    self.check_air_ticket = 1
            else:
                self.check_air_ticket = 1