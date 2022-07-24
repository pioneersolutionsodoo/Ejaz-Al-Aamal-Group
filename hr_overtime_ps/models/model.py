# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
import math


class hr_overtime_ps(models.Model):
    _name = 'hr.overtime.ps'
    _description = 'Overtime'
    _inherit = ['mail.thread', 'resource.mixin']

    @api.model
    def _get_employee(self):
        result = False
        employee_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        if employee_ids:
            result = employee_ids[0]
        return result

    @api.onchange('employee_id')
    def _get_employee_details(self):
        self.department_id = self.employee_id.department_id.id or False
        self.job_id = self.employee_id.job_id.id or False

    def _get_current_user(self):
        self.current_user = False
        if (
                self.employee_id and self.employee_id.parent_id and self.employee_id.parent_id.user_id) and self.employee_id.parent_id.user_id.id == self.env.uid:
            self.current_user = True

    @api.depends('overtime_summary.request_hours', 'overtime_summary.approved_hours')
    def _compute_hours(self):
        self.request_hours = sum(line.request_hours for line in self.overtime_summary) or 0.00
        self.approved_hours = sum(line.approved_hours for line in self.overtime_summary) or 0.00

    # @api.depends('employee_id')
    # def _get_employee_details(self):
    #     self.department_id = self.employee_id.department_id.id or False
    #     self.job_id = self.employee_id.job_id.id or False

    name = fields.Char(string='Serial', default=lambda self: _('New'))
    date_from = fields.Date(states={'approve': [('readonly', True)], 'refuse': [('readonly', True)], }, )
    date_to = fields.Date(states={'approve': [('readonly', True)], 'refuse': [('readonly', True)], }, )
    request_hours = fields.Float( store=True, compute='_compute_hours')
    approved_hours = fields.Float( store=True, compute='_compute_hours')
    current_user = fields.Boolean(compute='_get_current_user')
    confirmed_date = fields.Datetime()
    approved_date = fields.Datetime()
    refused_date = fields.Datetime()
    ot_per_hour = fields.Float(default=1.5)
    worked_hours = fields.Float(default=8, string="Worked Hours", readonly=False,
                                states={'approve': [('readonly', True)], 'refuse': [('readonly', True)], }, )
    worked_days = fields.Float(default=26, readonly=False,
                               states={'approve': [('readonly', True)], 'refuse': [('readonly', True)], }, )
    total = fields.Float(string="Amount Due", default=0.0)
    note = fields.Html()
    state = fields.Selection([
        ('draft', _('Draft')),
        ('request', _('Waiting for DM Confirm')),
        ('confirm', _('Waiting for HRM Approval')),
        ('approve', _('Approved')),
        ('refuse', _('Refused')),
    ], tracking=True, default='draft')

    # Relational Fields
    employee_id = fields.Many2one('hr.employee', default=_get_employee)
    contract_id = fields.Many2one('hr.contract', string="Contract", required=False)
    # department_id = fields.Many2one('hr.department', store=True, compute='_get_employee_details')
    department_id = fields.Many2one('hr.department', store=True, compute='_get_employee_details')
    job_id = fields.Many2one('hr.job', store=True, compute='_get_employee_details')
    company_id = fields.Many2one('res.company', change_default=True,
                                 default=lambda self: self.env['res.company']._company_default_get('hr.holidays.saudi'))
    refused_by = fields.Many2one('res.users', string='Refused By')
    overtime_summary = fields.One2many('hr.overtime.summary.ps', 'overtime_id',
                                       states={'approve': [('readonly', True)], 'refuse': [('readonly', True)], })
    # ==============================================================================================
    d_manager = fields.Many2one('res.users', string="Direct Manager")
    hr_manager_id = fields.Many2one('res.users', string='HR Manager')
    # ==============================================================================================
    #       Responsible Notes
    d_manager_note = fields.Text(string="Direct Manager Note", )
    hr_manager_note = fields.Text(string="HR Manager Note", )

    @api.constrains('date_from', 'date_to')
    def _date_check(self):
        if self.date_from > self.date_to:
            raise except_orm(_('Invalid Date!'), _('The Date From should be less than or equal Date To'))

    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New':
            values['name'] = self.env['ir.sequence'].next_by_code('hr.overtime.ps') or 'New'
        result = super(hr_overtime_ps, self).create(values)
        return result

    def onchange_employee_id(self, employee_id):
        contract = False
        if not employee_id:
            return {'value': {'contract_id': False}}
        contract_ids = self.env['hr.contract'].search([('employee_id', '=', employee_id)])
        #        raise except_orm(_('Configuration Error!'), _(contract_ids))
        if contract_ids:
            for record in contract_ids:
                contract = self.env['hr.contract'].browse(record.id).id
        return {'value': {'contract_id': contract}}

    def on_change_date_from_to(self, date_from, date_to):
        if (date_from and date_to) and date_from > date_to:
            raise except_orm(_('Invalid Date!'), _('The Date From should be less than or equal Date To'))

    def action_request(self):
        if not self.overtime_summary:
            raise UserError(_('You cannot send request without work summary.'))
        self.write({'state': 'request'})
        # Send Notification To Direct Manager
        self.sending_notification(self._description, self._name, self.id, self.name, 'direct_manager')

    def action_confirm(self):
        self.write({'state': 'confirm', 'd_manager': self.env.uid, 'confirmed_date': fields.date.today()})
        # Send Notification To HR Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr.group_hr_manager')

    def action_approve(self):
        ammount_due = self.overtime_compute()
        return self.write({'total': ammount_due, 'state': 'approve', 'approved_date': fields.date.today(),
                    'hr_manager_id': self.env.uid})

    def action_refuse(self):
        self.write({'state': 'refuse', 'refused_by': self.env.uid, 'refused_date': fields.date.today()})

    def unlink(self):
        if self.state not in ('draft'):
            raise UserError(_('You cannot delete an OverTime which is not draft.'))
        return super(hr_overtime_ps, self).unlink()

    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)

    @api.onchange('ot_per_hour', 'approved_hours', 'worked_days', 'worked_hours')
    def overtime_compute(self):
        for record in self:
            totally = self.total = self.approved_hours * (
                    (self.contract_id.wage / self.worked_days) / self.worked_hours) * self.ot_per_hour
            return totally


class hr_overtime_summary_ps(models.Model):
    _name = 'hr.overtime.summary.ps'
    _inherit = ['mail.thread', 'resource.mixin']
    _description = 'Overtime Summary'

    overtime_id = fields.Many2one('hr.overtime.ps', string='OverTime', required=True, ondelete='cascade', index=True, )
    name = fields.Char(string='Description', required=True, translate=True)
    date = fields.Date(string='Date', required=True, )
    request_hours = fields.Float(string='Request Hours', required=True, )
    approved_hours = fields.Float(string='Approved Hours', )

    state = fields.Selection([('draft', 'Draft'), ], 'Status', readonly=True, tracking=True,
                             default='draft')

    @api.constrains('date')
    def _date_check(self):
        if self.date < self.overtime_id.date_from or self.date > self.overtime_id.date_to:
            raise except_orm(_('Invalid Date!'), _('The Date should in the range of Date From and Date To'))


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def overtime_compute(self, employee, date_from, date_to, wage, deduction_type):
        approved_hours = total = 0
        overtime_ids = self.env['hr.overtime.ps'].search(
            [('employee_id', '=', employee), ('date_from', '>=', date_from), ('date_to', '>=', date_from),
             ('state', '=', 'approve')])
        for record in overtime_ids: approved_hours += record.approved_hours
        total = approved_hours * ((wage / 30) / 8)
        return total

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
