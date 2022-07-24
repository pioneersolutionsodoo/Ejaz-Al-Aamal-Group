from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class HrLeaves(models.Model):
    _inherit = 'hr.leave'

    out_side_saudi_arabia = fields.Boolean()
    check_visa_request = fields.Integer(compute='_get_visa_request_number')

    # Relational fields
    visa_request_id = fields.Many2one('visa.request')

    def create_visa_request(self):
        visa_request_id = self.env['visa.request'].create({
            'employee_id': self.employee_id.id,
            'vacation_start_date': self.date_from,
            'vacation_end_date': self.date_to,
        })
        self.visa_request_id = visa_request_id

    @api.depends('visa_request_id')
    def _get_visa_request_number(self):
        if self.visa_request_id or self.state != 'validate' or self.out_side_saudi_arabia == False:
            self.check_visa_request = 1
        else:
            if self.leave_type_id and self.out_side_saudi_arabia:
                if self.leave_type_id.is_annual:
                    self.check_visa_request = 0.0
                else:
                    self.check_visa_request = 1
            else:
                self.check_visa_request = 1