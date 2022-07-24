
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, date


class MedicalInsuranceClass(models.Model):
    _name = 'medical.insurance.class'
    _description = 'Insurance Class'

    name = fields.Char('Name', required=True, copy=False)
    description = fields.Text('Description')

    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "Class name must be unique",
        ),
    ]


class MedicalInsuranceProvider(models.Model):
    _name = 'medical.insurance.provider'
    _description = 'Medical Insurance Provider'

    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
    # insurance_class_id = fields.Many2one('medical.insurance.class', string='Insurance Class')


class MedicalInsurance(models.Model):
    _name = 'medical.insurance'
    _description = 'Medical Insurance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('expired', 'Expired'), ('cancel', 'Canceled')],
                             string="Status", tracking=True, readonly=True, default="draft")
    name = fields.Char(string="Name", required=True, copy=False, readonly=True,index=True, default=lambda self:_('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', readonly=True, string='Department')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', readonly=True, string='Job')

    insurance_provider_id = fields.Many2one('medical.insurance.provider', string='Insurance Provider')
    adult_number = fields.Integer(string='Adults')
    child_number = fields.Integer(string='Child')
    insurance_amount = fields.Float(string='Insurance Amount', default=0.00)
    insurance_class_id = fields.Many2one('medical.insurance.class', required=True, string='Insurance Class')
    insurance_expiry_date = fields.Date(string='Insurance Expiry Date')

    note = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('medical.insurance') or _('New')
        return super(MedicalInsurance, self).create(vals)


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You cannot delete record which is not in Draft.'))
        return super(MedicalInsurance, self).unlink()

    def action_activate(self):
        active_insurance = self.search_count([('employee_id', '=', self.employee_id.id), ('state', '=', 'active')])
        if active_insurance > 0:
            raise UserError(_('Employee %s already has an active medical insurance! \n'
                              'You can not active two medical insurances for the same employee at the same time.'%self.employee_id.name))
        if not self.insurance_expiry_date:
            raise UserError(_('You have to determine the Expiration Date.'))
        else:
            if self.insurance_expiry_date <= date.today():
                raise UserError(_('You can\'t activate this Medical Insurance.\nExpiration Date Reached!'))
        self.state = 'active'


    def action_cancel(self):
        self.state = 'cancel'


    def action_draft(self):
        self.state = 'draft'


    def check_medical_insurance_expiration(self):
        for rec in self.search([('state', '=', 'active')]):
            if rec.insurance_expiry_date:
                if rec.insurance_expiry_date <= date.today():
                    rec.state = 'expired'

