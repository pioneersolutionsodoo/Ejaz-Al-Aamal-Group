# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


def _get_employee(obj):
    ids = obj.env['hr.employee'].search([('user_id', '=', obj.env.uid)])
    if ids:
        return ids[0]
    else:
        raise UserError(_('The user is not an employee.'))
    return False


class HrClearance(models.Model):
    _name = 'hr.employee.clearance'
    _inherit = ['mail.thread']
    _description = 'Employee Clearance'
    _rec_name = 'name'

    name = fields.Char(string='Number', required=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('hr.employee.clearance'))
    employee_no = fields.Char(related='employee_id.emp_code')
    last_working_date = fields.Datetime()
    # equipment_number = fields.Integer(compute='_get_equipment_number')
    # equipment_manager_group = fields.Integer(compute='_get_equipment_number')
    # fleet_number = fields.Integer(compute='_get_fleet_number')
    # fleet_manager_group = fields.Integer(compute='_get_fleet_number')
    loan_number = fields.Integer(compute='_get_loan_number', store=True)
    # stock_number = fields.Integer(compute='_get_stock_number')
    date = fields.Datetime()
    note = fields.Text()
    is_direct_manager = fields.Boolean(compute='check_if_direct_manager')
    show_direct_manager_button = fields.Boolean(compute='get_show_direct_manager_button')
    type = fields.Selection(selection=[
        ('vacation', _('Vacation')),
        ('resignation_exit', _('Resignation / Exit')), ], default='vacation')
    state = fields.Selection(selection=[
        ('draft', _('Draft')),
        ('direct_manager', _('Direct Manager')),
        ('hr_manager', _('Hr Manager')),
        # ('equipment', _('Equipment Manager')),
        # ('fleet', _('Fleet Manager')),
        ('account', _('Accounting Depart')),
        ('admin_fd', 'Admin Finance Director'),
        ('approve', _('Approved'))], default='draft')

    # Relational Fields
    project_id = fields.Many2one(related='employee_id.project_name')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    employee_id = fields.Many2one('hr.employee', default=_get_employee)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    # equipment_ids = fields.One2many('maintenance.equipment', 'inverse_employee_clearance_id')
    # fleet_ids = fields.One2many('fleet.vehicle', 'inverse_employee_clearance_id')
    loan_ids = fields.One2many('hr.employee.loan.ps', 'inverse_employee_clearance_id')
    # stock_ids = fields.One2many('stock.location', 'inverse_employee_clearance_id')
    # ==============================================================================================
    d_manager = fields.Many2one('res.users', string="Direct Manager", readonly=True)
    hr_manager_id = fields.Many2one('res.users', string='HR Manager', readonly=True)
    account_manager_id = fields.Many2one('res.users', string='Accounting Manager', readonly=True)
    admin_manager_id = fields.Many2one('res.users', string='Admin & Finance Manager', readonly=True)
    # ==============================================================================================
    #       Responsible Notes
    d_manager_note = fields.Text(string="Direct Manager Note", )
    hr_manager_note = fields.Text(string="HR Manager Note", )
    account_manager_note = fields.Text(string="Accounting Manager Note", )
    admin_manager_note = fields.Text(string="Admin & Finance Manager Note", )
    d_manager_date = fields.Date()
    hr_manager_date = fields.Date()
    account_manager_date = fields.Date()
    admin_manager_date = fields.Date()

    @api.model
    def create(self, values):
        # Add code here
        result = super(HrClearance, self).create(values)
        if result.employee_id:
            # Restrict that selected employee should has direct manager
            if not result.employee_id.parent_id:
                raise UserError(_('Employee "%s" has no direct manager !') % result.employee_id.name)

            # Only employee him self and his direct manager can create the leave
            elif result.employee_id.parent_id:
                parent_id = result.employee_id.parent_id.user_id.id
                current_id = self.env.user.id

                if current_id != parent_id:
                    if current_id != result.employee_id.user_id.id:
                        raise UserError(
                            _('Only employee him self and his direct manager can create the Clearance Request'))

        return result

    def unlink(self):
        if self.state != 'draft':
            raise UserError(_('You cannot delete record which is not in Draft.'))
        return super(HrClearance, self).unlink()

    def send_request(self):
        self.state = 'direct_manager'
        # Send Notification To Direct Manager
        self.sending_notification(self._description, self._name, self.id, self.name, 'direct_manager')

    def direct_manager(self):
        self.write({'d_manager': self.env.uid, 'state': 'hr_manager', 'd_manager_date': fields.Date.today()})
        # Send Notification To HR Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr.group_hr_manager')

    def hr_manager(self):
        self.write({'hr_manager_id': self.env.uid, 'state': 'account', 'hr_manager_date': fields.Date.today()})
        # Send Notification To Account Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'account.group_account_manager')
        # self.state = 'equipment'

    # def equipment_manager(self):
    #     if self.fleet_number == 0:
    #         self.state = 'account'
    #     else:
    #         self.state = 'fleet'

    # def fleet_manager(self):
    #     self.state = 'account'

    def account_depart(self):
        self.write(
            {'account_manager_id': self.env.uid, 'state': 'admin_fd', 'account_manager_date': fields.Date.today()})
        # Send Notification To Admin and financial director
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr_loan_advance.group_admin_fd_user')

    def admin_approve(self):
        self.write({'admin_manager_id': self.env.uid, 'state': 'approve', 'admin_manager_date': fields.Date.today()})

    # =========================================
    def make_draft(self):
        self.state = 'draft'

    @api.depends('employee_id')
    def check_if_direct_manager(self):
        self.is_direct_manager = False
        self.show_direct_manager_button = False

        if self.employee_id:
            if self.employee_id.parent_id:
                if self.env.user.id == self.employee_id.parent_id.user_id.id:
                    self.is_direct_manager = True

                    if self.state == 'direct_manager':
                        self.show_direct_manager_button = True

    # @api.depends('equipment_ids')
    # def _get_equipment_number(self):
    #     records = self.env['maintenance.equipment'].search([('employee_id', '=', self.employee_id.id)])
    #     self.equipment_number = len(records)

    # @api.depends('fleet_ids')
    # def _get_fleet_number(self):
    #     records = self.env['fleet.vehicle'].search([('driver_id', '=', self.employee_id.address_home_id.id)])
    #     self.fleet_number = len(records)
    #     if self.user_has_groups('fleet.fleet_group_manager'):
    #         if self.state == 'fleet':
    #             self.fleet_manager_group = 1
    #         else:
    #             self.fleet_manager_group = 0
    #     else:
    #         self.fleet_manager_group = 0

    @api.model
    @api.depends('loan_ids')
    def _get_loan_number(self):
        for rec in self:
            records = rec.env['hr.employee.loan.ps'].search([('employee_id', '=', rec.employee_id.id)])
            rec.loan_number = len(records)

    # @api.depends('stock_ids')
    # def _get_stock_number(self):
    #     if self.employee_id.address_home_id:
    #         try:
    #             records = self.env['stock.location'].search([('partner_id', '=', self.employee_id.address_home_id.id)]).ids
    #         except:
    #             raise UserError(_('Please Configure Stock Location'))
    #     else:
    #         raise UserError(_('Employee "%s" has no related partner') % self.employee_id.name)
    #         records = []
    #     self.stock_number = len(records)

    # def maintenance_equipment_records(self):
    #     records = self.env['maintenance.equipment'].search([('employee_id', '=', self.employee_id.id)])
    #     return {
    #         'name': _('Equipment'),
    #         'view_type': 'form',
    #         'view_mode': 'tree',
    #         'res_model': 'maintenance.equipment',
    #         'view_id': self.env.ref('maintenance.hr_equipment_view_tree').id,
    #         'type': 'ir.actions.act_window',
    #         'domain': [('id', 'in', records.ids)], }
    #
    # def fleet_records(self):
    #     records = self.env['fleet.vehicle'].search([('driver_id', '=', self.employee_id.address_home_id.id)])
    #     return {
    #         'name': _('Fleet'),
    #         'view_type': 'form',
    #         'view_mode': 'tree',
    #         'res_model': 'fleet.vehicle',
    #         'view_id': self.env.ref('fleet.fleet_vehicle_view_tree').id,
    #         'type': 'ir.actions.act_window',
    #         'domain': [('id', 'in', records.ids)], }

    def loan_records(self):
        records = self.env['hr.employee.loan.ps'].search([('employee_id', '=', self.employee_id.id)])
        return {
            'name': _('Loans'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'hr.employee.loan.ps',
            'view_id': self.env.ref('hr_loan_advance.view_hr_employee_loan_tree_ps').id,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', records.ids)], }

    #
    # def stock_records(self):
    #     if self.employee_id.address_home_id:
    #         try:
    #             records = self.env['stock.location'].search([('partner_id', '=', self.employee_id.address_home_id.id)]).ids
    #         except:
    #             raise UserError(_('Please Configure Stock Location'))
    #     else:
    #         raise UserError(_('Employee "%s" has no related partner') % self.employee_id.name)
    #         records = []
    #     return {
    #         'name': _('Stock'),
    #         'view_type': 'form',
    #         'view_mode': 'tree',
    #         'res_model': 'stock.location',
    #         'view_id': self.env.ref('stock.view_location_tree2').id,
    #         'type': 'ir.actions.act_window',
    #         'domain': [('id', 'in', records)], }

    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)


class HrLoan(models.Model):
    _inherit = 'hr.employee.loan.ps'
    inverse_employee_clearance_id = fields.Many2one('hr.employee.clearance')

# class MaintenanceEquipment(models.Model):
#     _inherit = 'maintenance.equipment'
#     inverse_employee_clearance_id = fields.Many2one('hr.employee.clearance')
#
#
# class FleetVehicle(models.Model):
#     _inherit = 'fleet.vehicle'
#     inverse_employee_clearance_id = fields.Many2one('hr.employee.clearance')


# class StockLocation(models.Model):
#     _inherit = 'stock.location'
#     inverse_employee_clearance_id = fields.Many2one('hr.employee.clearance')
