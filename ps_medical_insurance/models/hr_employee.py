from odoo import fields, models, api, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ###   Medical Insurance   ###
    def get_medical_insurance_count(self):
        count = self.env['medical.insurance'].search_count([('employee_id','=',self.id)])
        self.medical_insurance_count = count

    medical_insurance_count = fields.Integer(string="Medical Insurance", compute="get_medical_insurance_count")

    def action_medical_insurance(self):
        return {
            'name': _('Medical Insurance'),
            'view_mode': 'tree,form',
            'res_model': 'medical.insurance',
            'type': 'ir.actions.act_window',
            'domain': [('employee_id', '=', self.id)],
        }

    def get_active_insurance(self):
        insurances = self.env['medical.insurance']
        for rec in self:
            active_insurance = insurances.search([('employee_id', '=', rec.id), ('state', '=', 'active')], limit=1)
            if len(active_insurance) > 0:
                rec.active_insurance_id = active_insurance[0].id
            else:
                rec.active_insurance_id = False
    active_insurance_id = fields.Many2one('medical.insurance', compute='get_active_insurance', string='Active Insurance')
