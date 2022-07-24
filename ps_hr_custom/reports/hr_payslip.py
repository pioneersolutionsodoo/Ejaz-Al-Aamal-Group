from odoo import fields, models, api, _
from odoo.exceptions import UserError



class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    type = fields.Selection([('back_pay', 'Back Pay'),
                             ('basic', 'Basic Salary'),
                             ('housing_alw', 'Housing Allowance'),
                             ('transport_alw', 'Transport Allowance'),
                             ('responsibility_alw', 'Responsibility Allowance'),
                             ('provision', 'Provision Sales Invoices'),

                             ('gosi_annuities', 'GOSI Annuities'),
                             ('gosi_saned', 'GOSI Saned'),
                             ('cash_shortage', 'Cash Shortage'),
                             ('housing_alw_deduct', 'Housing Allowance Deduction'),
                             ('transport_alw_deduct', 'Transport Allowance Deduction'),
                             ('salary_voucher_recovery', 'Salary Voucher Recovery'),
                             ('monthly_basic_deduct', 'Monthly Basic Deduction'),
                             ('disciplinary_action', 'Disciplinary Action'),
                             ('gross', 'Gross'),
                             ('net', 'Net'),
                             ], string="Rule Type")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    res_partner_bank_id = fields.Many2one('res.partner.bank', string="Bank Account")

    back_pay = fields.Float(compute="compute_report_values", store=True)
    basic = fields.Float(compute="compute_report_values", store=True)
    housing_alw = fields.Float(compute="compute_report_values", store=True)
    transport_alw = fields.Float(compute="compute_report_values", store=True)
    responsibility_alw = fields.Float(compute="compute_report_values", store=True)
    provision = fields.Float(compute="compute_report_values", store=True)
    total_earnings = fields.Float(compute="compute_report_totals", store=True)
    ##############################
    gosi_annuities = fields.Float(compute="compute_report_values", store=True)
    gosi_saned = fields.Float(compute="compute_report_values", store=True)
    cash_shortage = fields.Float(compute="compute_report_values", store=True)
    housing_alw_deduct = fields.Float(compute="compute_report_values", store=True)
    transport_alw_deduct = fields.Float(compute="compute_report_values", store=True)
    monthly_basic_deduct = fields.Float(compute="compute_report_values", store=True)
    salary_voucher_recovery = fields.Float(compute="compute_report_values", store=True)
    disciplinary_action = fields.Float(compute="compute_report_values", store=True)
    total_deductions = fields.Float(compute="compute_report_totals", store=True)
    ###############################
    net_pay_salary = fields.Float(compute="compute_report_totals", store=True)


    @api.depends('back_pay' , 'basic', 'housing_alw', 'provision', 'transport_alw', 'responsibility_alw',
                 'gosi_annuities', 'gosi_saned', 'cash_shortage', 'housing_alw_deduct', 'transport_alw_deduct',
                 'salary_voucher_recovery', 'monthly_basic_deduct', 'disciplinary_action')
    def compute_report_totals(self):
        for rec in self:
            rec.total_earnings = rec.back_pay + rec.basic + rec.housing_alw + rec.provision + rec.transport_alw + rec.responsibility_alw
            rec.total_deductions = rec.gosi_annuities + rec.gosi_saned + rec.cash_shortage + rec.housing_alw_deduct + rec.transport_alw_deduct + rec.salary_voucher_recovery + rec.monthly_basic_deduct + rec.disciplinary_action
            rec.net_pay_salary = rec.total_earnings + rec.total_deductions


    @api.depends('line_ids.total', 'line_ids.salary_rule_id.type')
    def compute_report_values(self):
        for rec in self:
            rec.back_pay = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'back_pay' and line.salary_rule_id.appears_on_payslip])
            rec.basic = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'basic' and line.salary_rule_id.appears_on_payslip])
            rec.housing_alw = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'housing_alw' and line.salary_rule_id.appears_on_payslip])
            rec.transport_alw = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'transport_alw' and line.salary_rule_id.appears_on_payslip])
            rec.responsibility_alw = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'responsibility_alw' and line.salary_rule_id.appears_on_payslip])
            rec.provision = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'provision' and line.salary_rule_id.appears_on_payslip])
            # total_earnings = back_pay + basic + housing_alw + provision + transport_alw + responsibility_alw

            rec.gosi_annuities = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'gosi_annuities' and line.salary_rule_id.appears_on_payslip])
            rec.gosi_saned = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'gosi_saned' and line.salary_rule_id.appears_on_payslip])
            rec.cash_shortage = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'cash_shortage' and line.salary_rule_id.appears_on_payslip])
            rec.housing_alw_deduct = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'housing_alw_deduct' and line.salary_rule_id.appears_on_payslip])
            rec.transport_alw_deduct = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'transport_alw_deduct' and line.salary_rule_id.appears_on_payslip])
            rec.monthly_basic_deduct = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'monthly_basic_deduct' and line.salary_rule_id.appears_on_payslip])
            rec.salary_voucher_recovery = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'salary_voucher_recovery' and line.salary_rule_id.appears_on_payslip])
            rec.disciplinary_action = sum([line.total for line in rec.line_ids if line.salary_rule_id.type == 'disciplinary_action' and line.salary_rule_id.appears_on_payslip])
            # total_deductions = gosi_annuities + gosi_saned + cash_shortage + housing_alw_deduct + transport_alw_deduct + salary_voucher_recovery + monthly_basic_deduct + disciplinary_action

            # net_pay_salary = total_earnings + total_deductions


    def print_customized_report(self):

        self.check_rule_types()
        return self.env.ref("ps_hr_custom.payslip_report").report_action(self)


    def check_rule_types(self):
        self.ensure_one()
        # if any([not line.salary_rule_id.type for line in self.line_ids]):
        valid = True
        error_info = _('You Must determine Rule Type for each Salary Rule used in selected Salary Structure, Then you can print Report.')
        error_info += '\n'
        error_info += _('Please assign the appropriate type to each of the following rules:')
        error_info += '\n'
        count = 1
        for line in self.line_ids:
            if not line.salary_rule_id.type:
                valid = False
                error_info += str(count) + '- ' + line.salary_rule_id.name + '\n'
                count += 1

        if not valid:
            raise UserError(error_info)


    def _can_be_printed(self):
        self.ensure_one()
        if self.state not in ['done', 'paid']:
            return _("This payslip is not validated. This is not a legal document.")
        return False
