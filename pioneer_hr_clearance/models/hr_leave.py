from odoo import api, fields, models

class HrLeaves(models.Model):
    _inherit = 'hr.leave'

    check_clearance = fields.Integer(compute='_get_clearance_number')

    # Relational fields
    hr_clearance_id = fields.Many2one('hr.employee.clearance')

    
    def create_clearance(self):
        hr_clearance_id = self.env['hr.employee.clearance'].create({
            'employee_id': self.employee_id.id,
        })
        self.hr_clearance_id = hr_clearance_id

    @api.depends('hr_clearance_id')
    def _get_clearance_number(self):
        if self.hr_clearance_id or self.state != 'validate':
            self.check_clearance = 1
        else:
            if self.leave_type_id:
                if self.leave_type_id.is_annual:
                    self.check_clearance = 0.0
                else:
                    self.check_clearance = 1
            else:
                self.check_clearance = 1