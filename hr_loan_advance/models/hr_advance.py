# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


def _get_employee(obj):
    ids = obj.env['hr.employee'].search([('user_id', '=', obj.env.uid)])
    if ids:
        return ids[0]
    else:
        raise UserError(_('The user is not an employee.'))
    return False

class AccountJournalInh(models.Model):
    _inherit = 'account.journal'
    default_account_id = fields.Many2one(
        comodel_name='account.account', check_company=True, copy=False, ondelete='restrict',
        string='Default Account',
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]")


class hr_employee_advance_ps(models.Model):
    _name = 'hr.employee.advance.ps'
    _description = 'Advance'
    _inherit = ['mail.thread', 'resource.mixin']

    def _get_currency(self):
        user = self.env['res.users'].browse([self.env.uid])[0]
        return user.company_id.currency_id.id

    def _old_advance_remaining(self):
        advance_obj = self.env['hr.employee.advance.ps']
        advance_line_obj = self.env['hr.employee.advance.line.ps']
        amount = 0
        if self.employee_id:
            advance_ids = advance_obj.search(
                [('employee_id', '=', self.employee_id.id), ('state', '=', 'approve'), ('id', '!=', self.id)])
            for advance in advance_ids:
                advance_line_ids = advance_line_obj.search(
                    [('hr_employee_advance_ps', '=', advance.id), ('state', '=', 'notdeducted')])
                for advance_line in advance_line_ids: amount += advance_line.amount
        self.old_advance_remaining = amount

    def _warning(self):
        self.warning = ''
        amount_to_ins, ins_per_month, remaining_value, advance_month_ins, y, installment_value = self.compute_installment_value(
            False)
        contract_ids = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)], limit=1,
                                                      order='date_start desc')
        if self.contract_id:
            if ins_per_month >= self.contract_id.wage: self.warning = 'Warning! Current Installment is greater or equal to employee contract wage.'

        else:
            self.warning = 'Warning! Please choose contract.'
        if not contract_ids: self.warning = 'Warning! There is no contract for this employee.'

    def _get_ins_amount(self):
        total_amount = paid_amount = total_installment = paid_installment = 0
        for line in self.hr_employee_advance_line_ps:
            if line.state == 'deducted':
                paid_amount += line.amount
                paid_installment += 1
            total_amount += line.amount
            total_installment += 1
        self.total_amount = total_amount
        self.paid_amount = paid_amount
        self.balance_amount = total_amount - paid_amount
        self.paid_installment = paid_installment
        self.unpaid_installment = total_installment - paid_installment

    @api.depends('write_date', 'employee_id')
    def _get_current_user(self):
        for case in self:
            current_user = False
            state = case.state
            is_direct_manager = False
            is_coach = False
            is_show_dm_approve = False
            is_show_hrm_approve = False
            is_show_fm_approve = False
            is_show_admin_approve = False
            employee = case.employee_id.sudo()
            parent = employee.parent_id.sudo()
            group_hr_manager = case.env.user.has_group('hr.group_hr_manager')
            group_account_manager = case.env.user.has_group('account.group_account_manager')
            if (employee and parent and parent.user_id) and parent.user_id.id == case.env.uid:
                is_direct_manager = True
                if state == 'request':
                    is_show_dm_approve = True
            if (employee and employee.coach_id and employee.coach_id.user_id) \
                    and employee.coach_id.user_id.id == case.env.uid:
                is_coach = True
                if state == 'request':
                    is_show_dm_approve = True
            if state == 'request' and (is_coach or is_direct_manager):
                is_show_dm_approve = True
            # if state == 'request':
            #     if group_hr_manager:
            #         is_show_hrm_approve = True
            elif state == 'progress':
                if group_hr_manager:
                    is_show_hrm_approve = True
            elif state == 'progress2':
                if group_account_manager:
                    is_show_fm_approve = True
            elif state == 'progress3':
                if case.env.user.has_group('hr_loan_advance.group_admin_fd_user'):
                    is_show_admin_approve = True
            if current_user and ((current_user.guarantor_id) and (current_user.guarantor_id.user_id)) \
                    and current_user.guarantor_id.user_id.id == case.env.uid:
                current_user = True
            case.current_user = current_user
            case.is_direct_manager = is_direct_manager
            case.is_coach = is_coach
            case.is_show_dm_approve = is_show_dm_approve
            case.is_show_admin_approve = is_show_admin_approve
            case.is_show_hrm_approve = is_show_hrm_approve
            case.is_show_fm_approve = is_show_fm_approve

    name = fields.Char(string='Advance Reference', default=lambda self: _('New'))
    request_date = fields.Date(string='Request Date')
    advance_amount_required = fields.Float(string='Advance Amount Required')
    advance_amount = fields.Float(string='Advance Amount Approved')
    advance_month_ins = fields.Integer(string='Number of Installments')
    advance_ins_start_date = fields.Date(string='Installment Start Date')
    advance_open = fields.Boolean(string='Advance Open')
    warning = fields.Text(string='Warning', compute='_warning')
    old_advance_remaining = fields.Float(string='Old Advance Remianing Amount', compute='_old_advance_remaining')
    total_amount = fields.Float(string='Total Amount', compute='_get_ins_amount')
    paid_amount = fields.Float(string='Paid Amount', compute='_get_ins_amount')
    balance_amount = fields.Float(string='Balance Amount', compute='_get_ins_amount')
    paid_installment = fields.Integer(string='Paid Installment', compute='_get_ins_amount')
    unpaid_installment = fields.Integer(string='Unpaid Installment', compute='_get_ins_amount')
    current_user = fields.Boolean(string='Current User', compute='_get_current_user')
    allow_another_advance = fields.Boolean(string='Allow Another Advance')
    direct_manager_date = fields.Datetime(string='DM Confirmed Date')
    hr_manager_date = fields.Datetime(string='HR Confirmed Date')
    account_manager_date = fields.Datetime(string='AC Confirmed Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Waiting for Direct Manager approval'),
        ('progress', 'Waiting for HR Manager approval'),
        ('progress2', 'Waiting for Finance Manager approval'),
        ('progress3', 'Waiting for Admin & Financial Director approval'),
        ('approve', 'Approved'),
        ('refused', 'Refused'),
    ], 'Status', tracking=True, default="draft",
        help='Status : User in 1.Draft(default) state Requesting to 2.DM Approval and processed by 3.HRM and Finalized by 4.FM')
    is_direct_manager = fields.Boolean(string='Is Direct Manager', compute='_get_current_user')
    is_coach = fields.Boolean(string='Is Coach', default=False, compute='_get_current_user')
    is_show_dm_approve = fields.Boolean(string='Is Show DM Button', compute='_get_current_user')
    is_show_hrm_approve = fields.Boolean(string='Is Show HR-Manager Approval Button', compute='_get_current_user')
    is_show_fm_approve = fields.Boolean(string='Is Show FM Approval Button', compute='_get_current_user')
    is_show_admin_approve = fields.Boolean(string='Is Show Admin & Financial Director Approval Button',
                                           compute='_get_current_user')
    advance_manual_closing = fields.Boolean(string='Manual Closing', compute='_get_advance_manual_closing')

    # ==============================================================================================
    #       Relation Fields
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=_get_employee)
    contract_id = fields.Many2one('hr.contract', string='Contract')
    type_id = fields.Many2one('hr.employee.advance.type.ps', string='Advance Type')
    move_id = fields.Many2one('account.move', string='Journal Entry')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'hr.employee.advance.ps'))
    hr_employee_advance_line_ps = fields.One2many('hr.employee.advance.line.ps', 'hr_employee_advance_ps',
                                                  string='Advance Line')
    currency_id = fields.Many2one('res.currency', string='Currency', default=_get_currency)
    direct_manager_id = fields.Many2one('res.users', string='Direct Manager')
    hr_manager_id = fields.Many2one('res.users', string='HR Manager')
    account_manager_id = fields.Many2one('res.users', string='Account Manager')
    admin_manager_id = fields.Many2one('res.users', string='Admin & Finance Manager')
    advance_manual_closing_id = fields.Many2one('account.move')
    # ==============================================================================================
    #       Responsible Notes
    d_manager_note = fields.Text(string="Direct Manager Note", )
    hr_manage_note = fields.Text(string="HR Manager Note", )
    account_manage_note = fields.Text(string="Accounting Manager Note", )
    admin_manager_note = fields.Text(string="Admin & Finance Manager Note", )

    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New':
            values['name'] = self.env['ir.sequence'].next_by_code('hr.employee.advance.ps') or 'New'
        result = super(hr_employee_advance_ps, self).create(values)
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
                        raise UserError(_('Only employee him self and his direct manager can create the Advance Request'))

        return result

    def unlink(self):
        if self.state not in ('draft', False):
            raise UserError(_('You cannot delete record which is not in Draft.'))
        return models.Model.unlink(self)

    @api.onchange('employee_id')
    def _onchange_employee(self):
        self.contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)], limit=1,
                                                          order='date_start desc').id

    def action_request(self):
        if self.advance_amount_required <= 0: raise UserError(_('Advance Amount Required must be greater than Zero!'))
        config = self.env['hr.config.settings']._get_limit_of_loan_advance()
        if config:
            if config.limit_of_advance == 'amount':
                if self.advance_amount_required > config.advance_amount: raise UserError(
                    _('Over limit advance amount required!'))
            elif config.limit_of_advance == 'basic':
                if not self.contract_id:
                    contract = self.env['hr.contract'].search(['employee_id', '=', self.employee_id.id], limit=1,
                                                              order='date_start desc')
                    if not contract:
                        raise UserError(_('There is no contract for this employee.Please contact administrator!'))
                    else:
                        raise UserError(_('Please choose contract!'))
                amount = self.contract_id.wage * config.advance_months
                if self.advance_amount_required > amount: raise UserError(_('Over limit advance amount required!'))
        self.write(
            {'state': 'request', 'advance_amount': self.advance_amount_required, 'request_date': fields.date.today()})
        # Send Notification To Direct Manager
        self.sending_notification(self._description, self._name, self.id, self.name, 'direct_manager')

    # # DM, HRM, FM

    def action_progress(self):
        self.write({'state': 'progress', 'direct_manager_id': self.env.uid
                       , 'direct_manager_date': fields.date.today()})
        # Send Notification To HR Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr.group_hr_manager')

    def action_progress2(self):
        self.write({'state': 'progress2', 'hr_manager_id': self.env.uid
                       , 'hr_manager_date': fields.date.today()})
        self.write({'hr_manager_id': self.env.uid, 'state': 'progress2'})
        # Send Notification To Account Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'account.group_account_manager')

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_approve(self):
        if not self.allow_another_advance and self.old_advance_remaining > 0: raise UserError(
            _('The Employee has already advance with balance.Please allow another advance or refuse!'))
        self.compute_installment_board()
        self.write({'state': 'progress3', 'account_manager_id': self.env.uid,
                    'account_manager_date': fields.date.today()})
        # Send Notification To Admin and financial director
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr_loan_advance.group_admin_fd_user')

    def action_progress3(self):
        move_id = self.generate_entry()
        self.write({'state': 'approve', 'move_id': move_id, 'account_manager_id': self.env.uid,
                    'admin_manager_id': self.env.uid, 'account_manager_date': fields.date.today()})

    def action_refuse(self):
        self.write({'state': 'refuse'})

    def check_detucted(self):
        result = False
        for record in self.hr_employee_advance_line_ps:
            if record.state == 'deducted': result = True
        return result

    def update_detucted(self, update):
        installment_value = tot_current_value = rem_value = t = 0
        for installment_lin_deducted in self.hr_employee_advance_line_ps:
            if installment_lin_deducted.state == 'deducted':
                tot_current_value = tot_current_value + installment_lin_deducted.amount
                rem_value = self.advance_amount - tot_current_value
                t += 1
                name_temp = str(self.name) + ' - ' + str(t) + '/' + str(self.advance_month_ins)
                if update: self.env.cr.execute(
                    "update hr_employee_advance_line_ps set installment_value = %s,remaining_value = %s,name = '%s' where id = %s" % (
                        installment_value, rem_value, name_temp, installment_lin_deducted.id))
                installment_value = installment_value + installment_lin_deducted.amount
        return tot_current_value, t, installment_value

    def compute_installment_value(self, update):
        amount_to_ins = ins_per_month = installment_value = remaining_value = advance_month_ins = t = 0
        if self.check_detucted():
            tot_current_value, t, installment_value = self.update_detucted(update)
            amount_to_ins = self.advance_amount - tot_current_value
            if (self.advance_month_ins - t) > 0: ins_per_month = amount_to_ins / (self.advance_month_ins - t)
            remaining_value = amount_to_ins - ins_per_month
            advance_month_ins = (self.advance_month_ins - t)
        else:
            amount_to_ins = self.advance_amount
            if self.advance_month_ins > 0: ins_per_month = amount_to_ins / self.advance_month_ins
            remaining_value = amount_to_ins - ins_per_month
            advance_month_ins = self.advance_month_ins
        return amount_to_ins, ins_per_month, remaining_value, advance_month_ins, t, installment_value

    def compute_installment_board(self):
        if self.advance_amount <= 0: raise UserError(_('Advance Amount must be greater than Zero!'))
        if self.advance_month_ins <= 0: raise UserError(_('Number of Installments must be greater than Zero!'))
        if not self.advance_ins_start_date: raise UserError(_('Choose Installment Start Date'))
        advance_ins_start_date = self.advance_ins_start_date
        for record in self.hr_employee_advance_line_ps:
            if record.state == 'notdeducted': record.unlink()
        amount_to_ins, ins_per_month, remaining_value, advance_month_ins, t, installment_value = self.compute_installment_value(
            True)
        for x in range(0, advance_month_ins):
            installment_date = (advance_ins_start_date + relativedelta(months=+x))
            i = x + 1 + t
            vals = {
                'amount': ins_per_month,
                'hr_employee_advance_ps': self.id,
                'sequence': i,
                'name': str(self.name) + ' - ' + str(i) + '/' + str(self.advance_month_ins),
                'remaining_value': remaining_value,
                'installment_value': installment_value,
                'installment_date': installment_date.strftime('%Y-%m-%d'),
                'confirm': True,
            }
            self.env['hr.employee.advance.line.ps'].create(vals)
            installment_value = installment_value + ins_per_month
            remaining_value = remaining_value - ins_per_month
        return True

    def generate_entry(self):
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        # nazar_obj = self.env['account.nazar']
        company_currency = self.company_id.currency_id.id
        diff_currency_p = self.currency_id.id != company_currency
        if not self.employee_id.address_home_id: raise UserError(_('Please set the home address for employee'))
        ref = self.employee_id.name + '/' + self.name
        # config = self.env['hr.accounting.config']._get_hr_accounting_config()
        if not self.company_id.advance_journal_id:
            raise UserError(_('Journal is not configured. Select Journal in Company Configuration'))
        journal_id = self.company_id.advance_journal_id
        if not journal_id.default_account_id:
            raise UserError(
                _('Missing credit or debit account for journal. Please set credit and debit account for journal.'))
        # move_id = move_obj.create(nazar_obj.account_move_get(self, journal_id, date=fields.datetime.today(), ref=ref,
        #                                                      company_id=self.company_id.id))

        vals = {
            'journal_id': journal_id.id,
            'date': fields.datetime.today(),
            # 'period_id': period_obj.find(date)[0],
            'ref': '',
            'company_id': self.company_id.id,
        }
        line1 = [(0, 0, {
            # 'move_id': move_id.id,
            'journal_id': journal_id.id,
            'partner_id': self.employee_id.address_home_id.id,
            'credit': 0,
            'debit': self.advance_amount,
            # 'centralisation': 'normal',
            'company_id': self.company_id.id,
            # 'state': 'valid',
            'blocked': False,
            'account_id': journal_id.default_account_id.id,
            # 'period_id': move_id.period_id.id,
            'name': 'Advance',
            'amount_currency': diff_currency_p and self.currency_id.id or False,
            'quantity': 1,

        })]
        line1.append((0, 0, {
            # 'move_id': move_id.id,
            'journal_id': journal_id.id,
            'partner_id': self.employee_id.address_home_id.id,
            'credit': self.advance_amount,
            'debit': 0,
            # 'centralisation': 'normal',
            'company_id': self.company_id.id,
            # 'state': 'valid',
            'blocked': False,
            'account_id': self.employee_id.address_home_id.property_account_payable_id.id,
            # 'period_id': move_id.period_id.id,
            'name': '/',
            'amount_currency': diff_currency_p and self.currency_id.id or False,
            'quantity': 1,

        }))

        vals.update({'line_ids': line1})

        move_id = move_obj.create(vals)

        return move_id.id

    def _get_advance_manual_closing(self):
        for item in self:
            if item.advance_manual_closing_id or item.state != 'approve':
                item.advance_manual_closing = True
            else:
                item.advance_manual_closing = False

    def manual_closing_advance(self):
        if not self.env.company.manual_close_advance_journal_id:
            raise UserError(_('Please configure the closing Advance journal'))

        # Get amount of all not deducted installments
        not_deducted = self.env['hr.employee.advance.line.ps'].search_read(
            [('hr_employee_advance_ps', '=', self.id), ('state', '=', 'notdeducted')], ['amount'])

        total_amount = 0.0
        if not_deducted:
            for line in not_deducted:
                total_amount += line['amount']
        credit_id = self.env.company.manual_close_advance_journal_id.default_account_id.id
        debit_id = self.env.company.manual_close_advance_journal_id.default_account_id.id

        line_ids = [(0, 0, {'account_id': credit_id, 'credit': total_amount}),
                    (0, 0, {'account_id': debit_id, 'debit': total_amount})]

        account_move_id = self.env['account.move'].create({
            'line_ids': line_ids,
            'closed_advance_id': self.id,
        })
        self.advance_manual_closing_id = account_move_id.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Close Advance'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': account_move_id.id,
            'context': {'active_id': self.id, 'not_deducted': not_deducted},
            'views': [[False, 'form']]
        }

    # Sending Notification with to users has "group_name"
    def sending_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)
