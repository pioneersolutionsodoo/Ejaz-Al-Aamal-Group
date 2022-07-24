# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


def _get_employee(obj):
    ids = obj.env['hr.employee'].search([('user_id', '=', obj.env.uid)])
    if ids:
        return ids[0]
    else:
        raise UserError(_('The user is not an employee.'))
    return False


class hr_employee_loan_ps(models.Model):
    _name = 'hr.employee.loan.ps'
    _description = 'Loan'
    _inherit = ['mail.thread', 'resource.mixin']

    def _get_currency(self):
        user = self.env['res.users'].browse([self.env.uid])[0]
        return user.company_id.currency_id.id

    def _old_loan_remaining(self):
        loan_obj = self.env['hr.employee.loan.ps']
        loan_line_obj = self.env['hr.employee.loan.line.ps']
        amount = 0
        if self.employee_id:
            loan_ids = loan_obj.search(
                [('employee_id', '=', self.employee_id.id), ('state', '=', 'approve'), ('id', '!=', self.id)])
            for loan in loan_ids:
                loan_line_ids = loan_line_obj.search(
                    [('hr_employee_loan_ps', '=', loan.id), ('state', '=', 'notdeducted')])
                for loan_line in loan_line_ids: amount += loan_line.amount
        self.old_loan_remaining = amount

    def _warning(self):
        self.warning = ''
        amount_to_ins, ins_per_month, remaining_value, loan_month_ins, y, installment_value = self.compute_installment_value(
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
        for line in self.hr_employee_loan_line_ps:
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
            is_direct_manager = False
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
            case.is_show_hrm_approve = is_show_hrm_approve
            case.is_show_fm_approve = is_show_fm_approve
            case.is_show_fm_approve = is_show_fm_approve
            case.is_show_admin_approve = is_show_admin_approve

    name = fields.Char(string='Loan Reference', default=lambda self: _('New'))
    request_date = fields.Date(string='Request Date')
    loan_amount_required = fields.Monetary(string='Loan Amount Required',  copy=False)
    loan_amount = fields.Float(string='Loan Amount Approved')
    loan_month_ins = fields.Integer(string='Number of Installments')
    loan_ins_start_date = fields.Date(string='Installment Start Date')
    loan_open = fields.Boolean(string='Loan Open')
    warning = fields.Text(string='Warning', compute='_warning')
    old_loan_remaining = fields.Float(string='Old Loan Remaining Amount', compute='_old_loan_remaining')
    total_amount = fields.Float(string='Total Amount', compute='_get_ins_amount')
    paid_amount = fields.Float(string='Paid Amount', compute='_get_ins_amount')
    balance_amount = fields.Float(string='Balance Amount', compute='_get_ins_amount')
    paid_installment = fields.Integer(string='Paid Installment', compute='_get_ins_amount')
    unpaid_installment = fields.Integer(string='Unpaid Installment', compute='_get_ins_amount')
    current_user = fields.Boolean(string='Current User', compute='_get_current_user')
    allow_another_loan = fields.Boolean(string='Allow Another Loan')
    loan_manual_closing = fields.Boolean(string='Manual Closing', compute='_get_loan_manual_closing')

    guarantor_date = fields.Datetime(string='G Confirmed Date')
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

    # ==============================================================================================
    #       Relation Fields
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_get_employee)
    contract_id = fields.Many2one('hr.contract', string='Contract')
    type_id = fields.Many2one('hr.employee.loan.type.ps', string='Loan Type')
    move_id = fields.Many2one('account.move', string='Journal Entry')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'hr.employee.loan.ps'))
    currency_id = fields.Many2one('res.currency', string='Currency', default=_get_currency)
    guarantor_id = fields.Many2one('hr.employee', string='Guarantor')
    guarantor_user_id = fields.Many2one('res.users', string='Guarantor User')
    hr_employee_loan_line_ps = fields.One2many('hr.employee.loan.line.ps', 'hr_employee_loan_ps', string='Loan Line')
    direct_manager_id = fields.Many2one('res.users', string='Direct Manager')
    hr_manager_id = fields.Many2one('res.users', string='HR Manager')
    account_manager_id = fields.Many2one('res.users', string='Account Manager')
    admin_manager_id = fields.Many2one('res.users', string='Admin & Finance Manager')
    loan_manual_closing_id = fields.Many2one('account.move')
    # ==============================================================================================
    #       Responsible Notes
    d_manager_note = fields.Text(string="Direct Manager Note", )
    hr_manage_note = fields.Text(string="HR Manager Note", )
    account_manage_note = fields.Text(string="Accounting Manager Note", )
    admin_manager_note = fields.Text(string="Admin & Finance Manager Note", )

    @api.constrains('guarantor_id')
    def _guarantor_constrains(self):
        if (self.guarantor_id):
            guarantor_ids = self.env['hr.employee.loan.ps'].search(
                [('employee_id', '=', self.guarantor_id.id), ('balance_amount', '>', 0)])
            if guarantor_ids: raise UserError(_('The Guarantor has already unpaid loan, So he cannot be a Gaurantor'))

    @api.onchange('employee_id')
    def _onchange_employee(self):
        self.contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)], limit=1,
                                                          order='date_start desc').id

    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New':
            values['name'] = self.env['ir.sequence'].next_by_code('hr.employee.loan.ps') or 'New'
        result = super(hr_employee_loan_ps, self).create(values)
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
                        raise UserError(_('Only employee him self and his direct manager can create the Loan Request'))

        return result

    def unlink(self):
        if self.state not in ('draft', False):
            raise UserError(_('You cannot delete record which is not in Draft.'))
        return models.Model.unlink(self)

    def action_request(self):
        if self.loan_amount_required <= 0: raise UserError(_('Loan Amount Required must be greater than Zero!'))
        config = self.env['hr.config.settings']._get_limit_of_loan_advance()
        if self.type_id.is_annual:
            year_bef = datetime.now() - relativedelta(years=1)

            # if self.employee_id.aj_date and self.employee_id.aj_date > year_bef.date():
            #     raise UserError(_('You are not eligible to apply for Annual Loan!'))
            # if not self.employee_id.aj_date:
            #     raise UserError(_('You are not eligible to apply for Annual Loan!'))
        if config:
            if config.limit_of_loan == 'amount':
                if self.loan_amount_required > config.loan_amount:
                    raise UserError(_('Over limit loan amount required!'))
            elif config.limit_of_loan == 'basic':
                if not self.contract_id: raise UserError(_('There is no contract.Please contact administrator!'))
                amount = self.contract_id.wage * config.loan_months
                if self.loan_amount_required > amount: raise UserError(_('Over limit loan amount required!'))
        self.write({'state': 'request', 'loan_amount': self.loan_amount_required, 'request_date': fields.date.today()})
        # Send Notification To Direct Manager
        self.sending_notification(self._description, self._name, self.id, self.name, 'direct_manager')

    def action_guarantor_approve(self):
        return self.write(
            {'state': 'guarantor_approve', 'guarantor_user_id': self.env.uid
                , 'guarantor_date': fields.date.today()})

    # # DM, HRM, FM

    def action_progress(self):
        # Here Update the status and assign and direct manager approval to current user
        self.write({'state': 'progress', 'direct_manager_id': self.env.uid
                       , 'direct_manager_date': fields.date.today()})
        # Send Notification To HR Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr.group_hr_manager')

    def action_progress2(self):
        self.write({'state': 'progress2', 'hr_manager_id': self.env.uid
                       , 'hr_manager_date': fields.date.today()})
        # Send Notification To Account Manager
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'account.group_account_manager')

    def action_approve(self):
        if not self.allow_another_loan and self.old_loan_remaining > 0: raise UserError(
            _('The Employee has already loan with balance.Please allow another loan or refuse!'))
        self.compute_installment_board()
        self.write({'state': 'progress3', 'account_manager_id': self.env.uid
                       , 'account_manager_date': fields.date.today()})
        # Send Notification To Admin and financial director
        self.sending_notification(self._description, self._name, self.id, self.name,
                                  'hr_loan_advance.group_admin_fd_user')

    def action_progress3(self):
        move_id = self.sudo().generate_entry()
        self.write({'state': 'approve', 'move_id': move_id
                       , 'account_manager_id': self.env.uid, 'admin_manager_id': self.env.uid
                       , 'account_manager_date': fields.date.today()})

    def action_refuse(self):
        self.write({'state': 'refused'})

    def check_detucted(self):
        result = False
        for record in self.hr_employee_loan_line_ps:
            if record.state == 'deducted': result = True
        return result

    def update_detucted(self, update):
        installment_value = tot_current_value = rem_value = t = 0
        for installment_lin_deducted in self.hr_employee_loan_line_ps:
            if installment_lin_deducted.state == 'deducted':
                tot_current_value = tot_current_value + installment_lin_deducted.amount
                rem_value = self.loan_amount - tot_current_value
                t += 1
                name_temp = str(self.name) + ' - ' + str(t) + '/' + str(self.loan_month_ins)
                if update: self.env.cr.execute(
                    "update hr_employee_loan_line_ps set installment_value = %s,remaining_value = %s,name = '%s' where id = %s" % (
                        installment_value, rem_value, name_temp, installment_lin_deducted.id))
                installment_value = installment_value + installment_lin_deducted.amount
        return tot_current_value, t, installment_value

    def compute_installment_value(self, update):
        amount_to_ins = ins_per_month = installment_value = remaining_value = loan_month_ins = t = 0
        if self.check_detucted():
            tot_current_value, t, installment_value = self.update_detucted(update)
            amount_to_ins = self.loan_amount - tot_current_value
            if (self.loan_month_ins - t) > 0: ins_per_month = amount_to_ins / (self.loan_month_ins - t)
            remaining_value = amount_to_ins - ins_per_month
            loan_month_ins = (self.loan_month_ins - t)
        else:
            amount_to_ins = self.loan_amount
            if self.loan_month_ins > 0: ins_per_month = amount_to_ins / self.loan_month_ins
            remaining_value = amount_to_ins - ins_per_month
            loan_month_ins = self.loan_month_ins
        return amount_to_ins, ins_per_month, remaining_value, loan_month_ins, t, installment_value

    def compute_installment_board(self):
        if self.loan_amount_required <= 0:
            raise UserError(_('Loan Amount must be greater than Zero!'))
        if self.loan_month_ins <= 0:
            raise UserError(_('Number of Installments must be greater than Zero!'))
        if not self.loan_ins_start_date: raise UserError(_('Choose Installment Start Date'))
        loan_ins_start_date = self.loan_ins_start_date
        for record in self.hr_employee_loan_line_ps:
            if record.state == 'notdeducted':
                record.unlink()
            else:
                loan_ins_start_date = (record.installment_date + relativedelta(months=+1))
        amount_to_ins, ins_per_month, remaining_value, loan_month_ins, t, installment_value = self.compute_installment_value(
            True)
        for x in range(0, loan_month_ins):
            installment_date = (loan_ins_start_date + relativedelta(months=+x))
            i = x + 1 + t
            vals = {
                'amount': ins_per_month,
                'hr_employee_loan_ps': self.id,
                'sequence': i,
                'name': str(self.name) + ' - ' + str(i) + '/' + str(self.loan_month_ins),
                'remaining_value': remaining_value,
                'installment_value': installment_value,
                'installment_date': installment_date.strftime('%Y-%m-%d'),
                'confirm': True,
            }
            self.env['hr.employee.loan.line.ps'].create(vals)
            installment_value = installment_value + ins_per_month
            remaining_value = remaining_value - ins_per_month
        return True

    def generate_entry(self):
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        company_currency = self.company_id.currency_id.id
        diff_currency_p = self.currency_id.id != company_currency
        if not self.employee_id.address_home_id: raise UserError(_('Please set the home address for employee'))
        ref = self.employee_id.name + '/' + self.name
        # config = self.env['hr.accounting.config']._get_hr_accounting_config()
        if not self.company_id.loan_journal_id:
            raise UserError(_('Journal is not configured. Select Journal in Company Configuration'))
        journal_id = self.company_id.loan_journal_id
        if not journal_id.default_account_id:
            raise UserError(
                _('Missing credit or debit account for journal.Please set credit and debit account for journal.'))
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
            'debit': self.loan_amount,
            # 'centralisation': 'normal',
            'company_id': self.company_id.id,
            # 'state': 'valid',
            'blocked': False,
            'account_id': journal_id.default_account_id.id,
            # 'period_id': move_id.period_id.id,
            'name': 'Loan',
            'amount_currency': diff_currency_p and self.currency_id.id or False,
            'quantity': 1,

        })]
        line1.append((0, 0, {
            # 'move_id': move_id.id,
            'journal_id': journal_id.id,
            'partner_id': self.employee_id.address_home_id.id,
            'credit': self.loan_amount,
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

    def action_draft(self):
        return self.write({'state': 'draft'})

    def _get_loan_manual_closing(self):
        for item in self:
            if item.loan_manual_closing_id or item.state != 'approve':
                item.loan_manual_closing = True
            else:
                item.loan_manual_closing = False

    def manual_closing_loan(self):
        if not self.env.company.manual_close_loan_journal_id:
            raise UserError(_('Please configure the closing loan journal'))

        # Get amount of all not deducted installments
        not_deducted = self.env['hr.employee.loan.line.ps'].search_read(
            [('hr_employee_loan_ps', '=', self.id), ('state', '=', 'notdeducted')], ['amount'])

        total_amount = 0.0
        if not_deducted:
            for line in not_deducted:
                total_amount += line['amount']
        credit_id = self.env.company.manual_close_loan_journal_id.default_account_id.id
        debit_id = self.env.company.manual_close_loan_journal_id.default_account_id.id

        line_ids = [(0, 0, {'account_id': credit_id, 'credit': total_amount}),
                    (0, 0, {'account_id': debit_id, 'debit': total_amount})]

        account_move_id = self.env['account.move'].create({
            'line_ids': line_ids,
            'closed_loan_id': self.id,
        })
        self.loan_manual_closing_id = account_move_id.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Close Loan'),
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
