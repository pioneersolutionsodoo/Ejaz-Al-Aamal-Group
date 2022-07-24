# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from xlsxwriter.workbook import Workbook as WB
from odoo.exceptions import UserError
import tempfile
from io import StringIO
import io
from xlrd import cellname
from pprint import pprint


class HrPayslip(models.Model):
    # _name = 'hr.payslip'
    _inherit = 'hr.payslip'

    # Relational Fields
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          related='employee_id.project_name.analytic_account_id')

    # Override compute_sheet function
    def compute_sheet(self):
        if self.employee_id.project_name:
            if not self.analytic_account_id:
                raise UserError(
                    _('There is no Analytic account in project assigned to employee %s') % self.employee_id.name)

        for payslip in self.filtered(lambda slip: slip.state not in ['cancel', 'done']):
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
            payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})
        return True

    def get_total(self, slip_id):
        total = 0
        rule_type = ['loan', 'hrdf', 'advance', 'gosi', 'other_deduction', 'absent']
        for r in rule_type:
            res = self.get_rule(slip_id, r)
            if res:
                total = total + res
            else:
                total = total
        return total

    def get_total_deduction(self, slip_id):
        payslip_line_ids = self.env['hr.payslip.line'].search([('slip_id', '=', slip_id)])
        total_deduction = 0.0
        if payslip_line_ids:
            for line in payslip_line_ids:
                if line.category_id.code == 'DED':
                    total_deduction += line.total
        return total_deduction

    def get_other_allowance(self, slip_id):
        payslip_line_ids = self.env['hr.payslip.line'].search([('slip_id', '=', slip_id)])
        other_allowance = 0.0
        if payslip_line_ids:
            for line in payslip_line_ids:
                if line.category_id.code == 'ALW' and line.code != 'HRA':
                    other_allowance += line.total
        return other_allowance

    def get_rule(self, slip_id, rule):
        self._cr.execute(
            "select total from hr_payslip_line where salary_rule_id in (select id from hr_salary_rule where lower(code) = '%s') and slip_id in (select id from hr_payslip where id = %s)" % (
                rule.lower(), slip_id))
        res = self._cr.fetchone()
        if res:
            return res[0]
        else:
            return 0.0

    def generate_xls(self, case, wiz):

        output = io.BytesIO()
        workbook = WB(output, {'in_memory': True})
        sheet = workbook.add_worksheet()

        sheet.set_column('A:A', 4)
        sheet.set_column('B:Z', 15)
        # Normal
        centre_bold, left, left_bold, left_bold_border, centre_bold_border = self.get_styles(workbook, sheet, wiz,
                                                                                             'statement')

        cell_format = workbook.add_format()
        cell_format.set_font_color('#FFFFFF')
        cell_format.set_bg_color('#236e9e')

        col = 0
        cnt = 1

        row = 8

        allowance = []  # List all allowance
        deduction = []  # List all Deduction
        for payslip in case:

            if payslip.employee_id.work_locations_id.id in wiz.work_locations_id.ids or wiz.work_locations_id.ids == []:
                if payslip.line_ids:
                    for line in payslip.line_ids:
                        if line.category_id.code == 'ALW' or line.category_id.code == 'BASIC':
                            if allowance:
                                flag = False
                                for alw in allowance:
                                    if alw['allowance_id'] == line.salary_rule_id.id:
                                        alw['employee_ids'].append({
                                            'payslip_id': payslip.id,
                                            'employee_id': payslip.employee_id.id,
                                            'total': line.total
                                        })
                                        flag = True
                                if not flag:
                                    allowance.append({
                                        'allowance_id': line.salary_rule_id.id,
                                        'name': line.code,
                                        'employee_ids': [{
                                            'payslip_id': payslip.id,
                                            'employee_id': payslip.employee_id.id,
                                            'total': line.total
                                        }]
                                    })
                            else:
                                allowance.append({
                                    'allowance_id': line.salary_rule_id.id,
                                    'name': line.code,
                                    'employee_ids': [{
                                        'payslip_id': payslip.id,
                                        'employee_id': payslip.employee_id.id,
                                        'total': line.total
                                    }]
                                })

                        elif line.category_id.code == 'DED':
                            if deduction:
                                flag = False
                                for ded in deduction:
                                    if ded['deduction_id'] == line.salary_rule_id.id:
                                        ded['employee_ids'].append({
                                            'payslip_id': payslip.id,
                                            'employee_id': payslip.employee_id.id,
                                            'total': line.total
                                        })
                                        flag = True
                                if not flag:
                                    deduction.append({
                                        'deduction_id': line.salary_rule_id.id,
                                        'name': line.code,
                                        'employee_ids': [{
                                            'payslip_id': payslip.id,
                                            'employee_id': payslip.employee_id.id,
                                            'total': line.total
                                        }]
                                    })
                            else:
                                deduction.append({
                                    'deduction_id': line.salary_rule_id.id,
                                    'name': line.code,
                                    'employee_ids': [{
                                        'payslip_id': payslip.id,
                                        'employee_id': payslip.employee_id.id,
                                        'total': line.total
                                    }]
                                })

        # Make sure that BASIC is first line
        index = 0
        if allowance:
            for alw in allowance:
                if alw['name'] == 'BASIC' and index != 0:
                    first_index = allowance[0]
                    allowance[0] = alw
                    allowance[index] = first_index
                index += 1

        merge_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#cae3ec',
        })
        sheet.merge_range('B6:G7', 'Basic Info', merge_format)

        last_row = 7 + len(allowance)
        # merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        sheet.merge_range(5, 7, 6, last_row, 'Allowances', merge_format)

        deduction_first_row = last_row + 1

        sheet.merge_range(5, deduction_first_row, 6, len(deduction) + deduction_first_row, 'Deduction', merge_format)

        sheet.write(row, col, '#', cell_format)
        col = col + 1
        sheet.write(row, col, 'Iqama ID', cell_format)
        col = col + 1
        sheet.write(row, col, 'Bank account', cell_format)
        col = col + 1
        sheet.write(row, col, 'Name', cell_format)
        col = col + 1
        sheet.write(row, col, 'Arabic Name', cell_format)
        col = col + 1
        sheet.write(row, col, 'Date Start', cell_format)
        col = col + 1
        sheet.write(row, col, 'Work Location', cell_format)
        col = col + 1

        for alw in allowance:
            sheet.write(row, col, alw['name'], cell_format)
            col = col + 1

        sheet.write(row, col, 'Total Allowance', cell_format)
        col = col + 1

        for ded in deduction:
            sheet.write(row, col, ded['name'], cell_format)
            col = col + 1

        sheet.write(row, col, 'Total Deduction', cell_format)
        col = col + 1

        sheet.write(row, col, 'Net', cell_format)
        col = col + 1
        row += 1

        # Sum all cells in same column
        totals_list = []
        total_all_allowance = 0.0
        total_all_deduction = 0.0
        for alw in allowance:
            total_same_allowance = 0.0
            for employee in alw['employee_ids']:
                total_same_allowance += employee['total']
                total_all_allowance += employee['total']
            totals_list.append({
                'code': alw['name'],
                'total': total_same_allowance
            })
        totals_list.append({
            'code': 'Total Allowance',
            'total': total_all_allowance
        })
        for ded in deduction:
            total_same_deduction = 0.0
            for employee in ded['employee_ids']:
                total_same_deduction += employee['total']
                total_all_deduction += employee['total']
            totals_list.append({
                'code': ded['name'],
                'total': total_same_deduction
            })
        totals_list.append({
            'code': 'Total Deduction',
            'total': total_all_deduction
        })
        totals_list.append({
            'code': 'Total Net',
            'total': total_all_allowance + total_all_deduction
        })

        payslip_index = 1
        odd_cell_index = 0
        odd_cell_format = workbook.add_format({'align': 'left'})
        odd_cell_format.set_bg_color('#cae3ec')
        odd_cell_format.set_font_name('Verdana')
        odd_cell_format.set_font_size(10)

        for p in case:
            if p.employee_id.work_locations_id.id in wiz.work_locations_id.ids or wiz.work_locations_id.ids == []:

                odd_cell_index += 1
                if odd_cell_index % 2 == 1:
                    col = 0
                    sheet.write(row, col, payslip_index, odd_cell_format)
                    payslip_index += 1
                    col = col + 1
                    sheet.write(row, col, str(p.employee_id.identification_id), odd_cell_format)
                    col = col + 1
                    sheet.write(row, col, str(p.employee_id.bank_account_id.acc_number), odd_cell_format)
                    col = col + 1
                    sheet.write(row, col, str(p.employee_id.name), odd_cell_format)
                    col = col + 1
                    sheet.write(row, col, str(p.employee_id.arabic_name), odd_cell_format)
                    col = col + 1
                    sheet.write(row, col, str(p.date_from), odd_cell_format)
                    col = col + 1
                    sheet.write(row, col, str(p.employee_id.work_location), odd_cell_format)
                    col = col + 1

                    total_allowance = 0.0
                    for alw in allowance:
                        value = 0.0
                        for employee in alw['employee_ids']:

                            if employee['employee_id'] == p.employee_id.id and employee['payslip_id'] == p.id:
                                value = employee['total']
                                total_allowance += value

                        sheet.write(row, col, value, odd_cell_format)
                        col = col + 1

                    sheet.write(row, col, total_allowance, odd_cell_format)
                    col = col + 1

                    total_deduction = 0.0
                    for ded in deduction:
                        value = 0.0
                        for employee in ded['employee_ids']:

                            if employee['employee_id'] == p.employee_id.id and employee['payslip_id'] == p.id:
                                value = employee['total']
                                total_deduction += value

                        sheet.write(row, col, value, odd_cell_format)
                        col = col + 1

                    sheet.write(row, col, total_deduction, odd_cell_format)
                    col = col + 1

                    net = total_allowance + total_deduction
                    sheet.write(row, col, net, odd_cell_format)
                    col = col + 1

                    row += 1
                    cnt += 1
                else:
                    col = 0
                    sheet.write(row, col, payslip_index, left)
                    payslip_index += 1
                    col = col + 1
                    sheet.write(row, col, str(p.employee_id.identification_id), left)
                    col = col + 1
                    sheet.write(row, col, str(p.employee_id.bank_account_id.acc_number), left)
                    col = col + 1
                    sheet.write(row, col, str(p.employee_id.name), left)
                    col = col + 1
                    sheet.write(row, col, str(p.employee_id.arabic_name), left)
                    col = col + 1
                    sheet.write(row, col, str(p.date_from), left)
                    col = col + 1
                    sheet.write(row, col, str(p.employee_id.work_location), left)
                    col = col + 1

                    total_allowance = 0.0
                    for alw in allowance:
                        value = 0.0
                        for employee in alw['employee_ids']:

                            if employee['employee_id'] == p.employee_id.id and employee['payslip_id'] == p.id:
                                value = employee['total']
                                total_allowance += value

                        sheet.write(row, col, value, left)
                        col = col + 1

                    sheet.write(row, col, total_allowance, left)
                    col = col + 1

                    total_deduction = 0.0
                    for ded in deduction:
                        value = 0.0
                        for employee in ded['employee_ids']:

                            if employee['employee_id'] == p.employee_id.id and employee['payslip_id'] == p.id:
                                value = employee['total']
                                total_deduction += value

                        sheet.write(row, col, value, left)
                        col = col + 1

                    sheet.write(row, col, total_deduction, left)
                    col = col + 1

                    net = total_allowance + total_deduction
                    sheet.write(row, col, net, left)
                    col = col + 1

                    row += 1
                    cnt += 1

        col = 7

        sheet.merge_range(row, 1, row, 6, 'Total', merge_format)

        for total_line in totals_list:
            sheet.write(row, col, total_line['total'], cell_format)
            col = col + 1

        workbook.close()
        output.seek(0)
        data = output.read()
        output.close()
        # f = open(dataFile, 'rb')
        # data = f.read()
        # f.close()
        return data

    def get_styles(self, workbook, sheet, wiz, type):
        left = workbook.add_format({'align': 'left'})
        left.set_font_name('Verdana')
        left.set_font_size(10)
        right = workbook.add_format({'align': 'right'})
        right.set_font_name('Verdana')
        right.set_font_size(10)
        centre = workbook.add_format({'align': 'centre'})
        centre.set_font_name('Verdana')
        centre.set_font_size(10)
        left_indent = workbook.add_format({'align': 'left'})
        left_indent.set_font_name('Verdana')
        left_indent.set_font_size(10)
        left_indent.set_indent(1)
        left_bold = workbook.add_format({'align': 'left', 'bold': True})
        left_bold.set_font_name('Verdana')
        left_bold.set_font_size(10)
        centre_bold = workbook.add_format({'align': 'centre', 'bold': True})
        centre_bold.set_font_name('Verdana')
        centre_bold.set_font_size(12)
        left_bold_border = workbook.add_format({'align': 'left', 'bold': True})
        left_bold_border.set_font_name('Verdana')
        left_bold_border.set_font_size(9)
        left_bold_border.set_border(1)
        centre_bold_border = workbook.add_format({'align': 'centre', 'bold': True})
        centre_bold_border.set_font_name('Verdana')
        centre_bold_border.set_font_size(9)
        centre_bold_border.set_border(1)
        report_name = 'Salary Statement'
        type_position = 16
        state_position = 17
        main_position = 6
        if type == 'wages':
            report_name = 'Wages Report'
            type_position = 8
            state_position = 9
            main_position = 4

        sheet.write(0, 1, 'Date From', left_bold)
        sheet.write(0, 2, str(wiz.f_date), left)

        sheet.write(1, 1, 'Date To', left_bold)
        sheet.write(1, 2, str(wiz.t_date), left)

        sheet.write(1, main_position, report_name, left_bold)

        sheet.write(1, type_position, 'Type', left_bold)
        sheet.write(1, state_position, str(wiz.type), left)

        sheet.write(2, 1, 'Company', left_bold)
        sheet.write(2, 2, str(wiz.company_id.name), centre_bold)

        sheet.write(2, type_position, 'State', left_bold)
        sheet.write(2, state_position, str(wiz.state), left)

        sheet.write(3, 1, 'Analytic Account', left_bold)
        account_names = ''
        for account_name in wiz.analytic_account_ids:
            account_names += account_name.name
            account_names += ' , '
        sheet.write(3, 2, str(account_names))

        return centre_bold, left, left_bold, left_bold_border, centre_bold_border

    def generate_wages_xls(self, case, wiz, ):
        output = io.BytesIO()
        workbook = WB(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        # sheet.set_column('A:A', 40)
        sheet.set_column('A:K', 15)
        # Normal
        centre_bold, left, left_bold, left_bold_border, centre_bold_border = self.get_styles(workbook, sheet, wiz,
                                                                                             'wages')

        row = 5
        col = 0
        cnt = 1

        sheet.write(4, 0, 'Sl.no', left_bold_border)
        sheet.write(4, 1, 'Employee No', left_bold_border)
        sheet.write(4, 2, 'Employee Name', left_bold_border)
        sheet.write(4, 3, 'Iqama No', left_bold_border)
        sheet.write(4, 4, 'BANK Name', left_bold_border)
        sheet.write(4, 5, 'IBAN Number', left_bold_border)
        sheet.write(4, 6, 'Net Salary', left_bold_border)
        sheet.write(4, 7, 'Basic Salary', left_bold_border)
        sheet.write(4, 8, 'Housing', left_bold_border)
        sheet.write(4, 9, 'Other Earnings', left_bold_border)
        sheet.write(4, 10, 'Deductions', left_bold_border)
        sheet.write(4, 11, 'Payment Detail', left_bold_border)

        for p in case:
            sheet.write(row, 0, str(cnt), left)
            sheet.write(row, 1, str(p.employee_id.emp_code or ''), left)
            sheet.write(row, 2, p.employee_id.name, left)
            sheet.write(row, 3, str(p.employee_id.identification_id or ''), left)
            sheet.write(row, 4,
                        str(p.employee_id.bank_account_id and p.employee_id.bank_account_id.bank_id.name or ''), left)
            sheet.write(row, 5, str(p.employee_id.bank_account_id and p.employee_id.bank_account_id.bank_id.bic or ''),
                        left)
            sheet.write(row, 6, str(p.get_rule(p.id, 'net')), left)
            sheet.write(row, 7, str(p.get_rule(p.id, 'BASIC')), left)
            sheet.write(row, 8, str(p.get_rule(p.id, 'housing')), left)
            sheet.write(row, 9, str(p.get_rule(p.id, 'other_allowance')), left)
            sheet.write(row, 10, str(p.get_rule(p.id, 'deductions')), left)
            sheet.write(row, 11, str(p.get_rule(p.id, 'payment_details')), left)

        workbook.close()
        output.seek(0)
        data = output.read()
        output.close()
        # f = open(dataFile, 'rb')
        # data = f.read()
        # f.close()
        return data
