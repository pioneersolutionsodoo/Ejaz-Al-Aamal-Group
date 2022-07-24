# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime, timedelta
from dateutil import relativedelta
import math
from lxml import etree
from odoo.exceptions import UserError, ValidationError


def _get_employee(obj):
    ids = obj.env['hr.employee'].search([('user_id', '=', obj.env.uid)])
    if ids:
        return ids[0]
    # else:
        # raise ValidationError(_('The user is not an employee.'))
        # return False


class hr_business_trip(models.Model):
    _name = 'hr.business.trip'
    _description = 'Business Trip'
    _inherit = ['mail.thread', 'resource.mixin']

    def _get_current_user(self):
        self.current_user = False
        self.is_direct_manager = False
        employee = self.employee_id.sudo()
        if (employee and employee.parent_id and employee.parent_id.user_id) \
                and employee.parent_id.user_id.id == self.env.uid:
            self.is_direct_manager = True
        if (employee and employee.user_id) and employee.user_id.id == self.env.uid:
            self.current_user = True

    def _compute_date(self, date_from, date_to, DATETIME_FORMAT):
        days = months = years = 0
        differents = relativedelta.relativedelta(date_to, date_from)
        years = differents.years
        months = (years * 12) + differents.months
        #        days = differents.days
        timedelta = date_to - date_from
        diff_day = timedelta.days + float(timedelta.seconds) / 86400
        days = round(math.floor(diff_day))
        return days, months, years

    @api.model
    @api.depends('travel_date_from', 'travel_date_to', 'actual_travel_date_from', 'actual_travel_date_to')
    def _compute_days(self):
        for rec in self:
            days = 0
            DATETIME_FORMAT = "%Y-%m-%d"
            if rec.travel_date_from and rec.travel_date_to:
                days, months, years = rec._compute_date(rec.travel_date_from, rec.travel_date_to, DATETIME_FORMAT)
                rec.request_travel_days = days + 1
            else:
                rec.request_travel_days = 0

            if rec.actual_travel_date_from and rec.actual_travel_date_to:
                days, months, years = rec._compute_date(rec.actual_travel_date_from, rec.actual_travel_date_to,
                                                        DATETIME_FORMAT)
                rec.actual_travel_days = days + 1
            else:
                rec.actual_travel_days = 0

    def _get_currency(self):
        user = self.env['res.users'].browse([self.env.uid])[0]
        return user.company_id.currency_id

    @api.model
    @api.depends('employee_id', 'travel_date_from', 'travel_date_to')
    def _get_employee_details(self):
        for rec in self:
            rec.employee_id = rec.employee_id.sudo()
            rec.department_id = rec.employee_id.department_id.id or False
            rec.job_id = rec.employee_id.job_id.id or False
            rec.company_id = rec.employee_id.company_id.id or False

    name = fields.Char(string='Serial', default=lambda self: _('New'))
    date = fields.Date(string='Request Date', default=fields.date.today())
    city = fields.Char(string='City')
    visa_required = fields.Boolean(string='VISA Required')
    travel_date_from = fields.Date(string='Travel Date From')
    travel_date_to = fields.Date(string='Travel Date To')
    request_travel_days = fields.Integer(string='Request Days', compute='_compute_days', store=True, compute_sudo=True)
    actual_travel_date_from = fields.Date(string='Actual Travel Date From')
    actual_travel_date_to = fields.Date(string='Actual Travel Date To')
    actual_travel_days = fields.Integer(string='Actual Days', compute='_compute_days', compute_sudo=True)
    recruitment = fields.Boolean(string='Recruitment')
    employee_recruited = fields.Integer(string='No. of Employees Recruited')
    expense_amount = fields.Float(string='Expense Amount')
    note = fields.Text(string='Description')
    current_user = fields.Boolean(string='Current User', compute='_get_current_user')
    direct_manager_date = fields.Datetime(string='DM Confirmed Date')
    direct_manager_note = fields.Text(string='DR Comments')
    hr_manager_date = fields.Datetime(string='HR Confirmed Date')
    hr_manager_note = fields.Text(string='HR Comments')
    account_manager_date = fields.Datetime(string='AC Confirmed Date')
    account_manager_note = fields.Text(string='AM Comments')
    is_direct_manager = fields.Boolean(string='Is Direct Manager', compute='_get_current_user')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Sent Request'),
        ('confirm', 'Confirm'),
        ('approve', 'Approve'),
        ('refuse', 'Refuse'),
        ('close', 'Close'),
        ('cancel', 'Cancelled'),
        ('fm_approve', 'Financial Manager Approve'),
    ], string='Status', index=True, default='draft',
        tracking=True, copy=False,
        help="Status")
    # =============================================================
    # relation fields
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True,
                                  states={'draft': [('readonly', False)]}, default=_get_employee)
    job_id = fields.Many2one('hr.job', compute='_get_employee_details', string="Job Title", store=True)
    department_id = fields.Many2one('hr.department', compute='_get_employee_details', string="Department",
                                    store=True)
    company_id = fields.Many2one('res.company', compute='_get_employee_details', string="Company",
                                 store=True)
    country_id = fields.Many2one('res.country', string="Country")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=_get_currency)
    move_id = fields.Many2one('account.move', string='Journal Entry')
    direct_manager_id = fields.Many2one('res.users', string='Direct Manager')
    hr_manager_id = fields.Many2one('res.users', string='HR Manager')
    account_manager_id = fields.Many2one('res.users', string='Account Manager')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(hr_business_trip, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                            submenu=submenu)
        doc = etree.XML(res['arch'])
        group_user = self.env.user.has_group('base.group_user')
        group_hr_user = self.env.user.has_group('hr.group_hr_user')
        group_hr_manager = self.env.user.has_group('hr.group_hr_manager')
        group_hr_general_manager = self.env.user.has_group('base.group_hr_general_manager')
        emp_obj = self.env['hr.employee']
        dm_emp_ids = emp_obj.search(
            [('parent_id.user_id', '=', self._uid)])  # to check in employee list where he is direct manager
        for node in doc.xpath("//form") + doc.xpath("//tree"):
            if group_user and not dm_emp_ids and not group_hr_user and not group_hr_manager and not group_hr_general_manager:
                node.set('create', _('false'))
                node.set('edit', _('false'))
                node.set('delete', _('false'))
        res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New':
            values['name'] = self.env['ir.sequence'].next_by_code('hr.business.trip') or 'New'
        model = super(hr_business_trip, self).create(values)
        # Restrict create business trip only by direct manager of the employee
        if model.employee_id.parent_id:
            if not self.env.user.id == model.employee_id.parent_id.user_id.id:
                raise UserError(_(
                    'Only direct manager "%s" of employee "%s" can create this business trip') % (
                                    model.employee_id.parent_id.user_id.name, model.employee_id.name))

        return model

    def unlink(self):
        if self.state not in ('draft', False):
            raise ValidationError(_('You cannot delete record which is not in Draft.'))
        return models.Model.unlink(self)

    def action_request(self):
        return self.write({'state': 'request'})
        # Send Notification To Direct Manager
        self.sending_notification(self._description, self._name, self.id, self.name, 'direct_manager')

    def action_confirm(self):
        self.write({'state': 'confirm', 'direct_manager_id': self.env.uid, 'direct_manager_date': fields.date.today()})
        # Send Notification To Account Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'account.group_account_manager')

    def action_approve(self):
        self.write({'state': 'approve', 'hr_manager_id': self.env.uid, 'hr_manager_date': fields.date.today()})

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_close(self):
        if not self.actual_travel_date_from or not self.actual_travel_date_to: raise ValidationError(
            _('Please choose actual travel from and to Date.'))
        return self.write({'state': 'close'})

    def action_fm_approve(self):
        if self.expense_amount <= 0: return self.write({'state': 'fm_approve', 'account_manager_id': self.env.uid})
        move_obj = self.env['account.move']
        employee = self.employee_id.sudo()
        move_line_obj = self.env['account.move.line']
        # nazar_obj = self.env['account.nazar']
        company = self.company_id
        company_currency = company.currency_id.id
        diff_currency_p = self.currency_id.id != company_currency
        if not employee.address_home_id: raise ValidationError(_('Please set the home address for employee'))
        ref = employee.name + '/' + self.name
        # config = self.env['hr.accounting.config'].sudo()._get_hr_accounting_config()

        if not company.business_trip_journal_id:
            raise UserError(_('Journal is not configured. '
                              'Select Journal from Company'))
        journal_id = company.business_trip_journal_id
        if not journal_id.default_account_id:
            raise UserError(
                _('Missing credit or debit account for journal.Please set credit and debit account for journal.'))
        vals = {
            'journal_id': journal_id.id,
            'date': fields.datetime.today(),
            'ref': '',
            'company_id': self.company_id.id,
        }

        line1 = [(0, 0, {
            'journal_id': journal_id.id,
            'partner_id': employee.address_home_id.id,
            'credit': 0,
            'debit': self.expense_amount,
            'company_id': self.company_id.id,
            'blocked': False,
            'account_id': journal_id.default_account_id.id,
            'name': _('Business Trip') + self.name,
            'amount_currency': diff_currency_p and self.currency_id.id or False,
            'quantity': 1,

        })]
        line1.append((0, 0, {
            'journal_id': journal_id.id,
            'partner_id': employee.address_home_id.id,
            'credit': self.expense_amount,
            'debit': 0,
            'company_id': self.company_id.id,
            'blocked': False,
            'account_id': employee.address_home_id.property_account_payable_id.id,
            'name': _('Business Trip : ') + self.name,
            'amount_currency': diff_currency_p and self.currency_id.id or False,
            'quantity': 1,

        }))
        vals.update({'line_ids': line1})

        move_id = move_obj.create(vals)
        self.write({'state': 'fm_approve', 'move_id': move_id.id, 'account_manager_id': self.env.uid,
                    'account_manager_date': fields.date.today()})
        return move_id.id

    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)

    def action_cancel(self):
        self.move_id.button_draft()
        self.move_id.with_context(force_delete=True).unlink()
        return self.write({'state': 'cancel'})
