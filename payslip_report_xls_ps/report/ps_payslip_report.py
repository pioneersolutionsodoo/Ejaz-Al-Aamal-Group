# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError
from pprint import pprint


class Reportpayslip(models.AbstractModel):
    _name = 'report.payslip_report_xls_ps.report_payslip_ps'
    _description = 'report.payslip_report_xls_ps.report_payslip_ps'

    @api.model
    def _get_report_values(self, docids, data=None):

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))

        clause = []
        sales_records = []
        orders = self.env['hr.payslip'].search([('company_id', '=', docs.company_id.id)])
        # if docs.date_from and docs.date_to:
        #     for order in orders:
        #         if parse(docs.date_from) <= parse(order.date_order) and parse(docs.date_to) >= parse(order.date_order):
        #             sales_records.append(order);
        # else:
        #     raise UserError("Please enter duration")
        clause += self._get_search_from_state(docs)
        clause += self._get_search_from_type(docs)
        if docs.analytic_account_ids:
            clause.append(('analytic_account_id', 'in', docs.analytic_account_ids.ids))
        payslip_ids = self.env['hr.payslip'].search(clause)

        if not payslip_ids:
            raise UserError('Null Data Record Not found.')

        # List all allowance
        allowance = []
        for payslip in payslip_ids:
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

        # List all Deduction
        deduction = []
        for payslip in payslip_ids:
            if payslip.line_ids:
                for line in payslip.line_ids:
                    if line.category_id.code == 'DED':
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
        for alw in allowance:
            if alw['name'] == 'BASIC' and index != 0:
                first_index = allowance[0]
                allowance[0] = alw
                allowance[index] = first_index
            index += 1
        # session_report = self.env['ir.actions.report']._get_report_from_name('payslip_report_xls_ps.report_payslip_ps')
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'time': time,
            'payslips': payslip_ids,
            'allowance': allowance,
            'deduction': deduction,
            'orders': sales_records,
            'case': self
        }

    def _get_search_from_state(self, docs):
        search = [('date_from', '>=', docs.f_date), ('date_to', '<=', docs.t_date),
                  ('company_id', '=', docs.company_id.id)]
        if docs.state != 'all':
            search += [('date_from', '>=', docs.f_date), ('date_to', '<=', docs.t_date),
                       ('company_id', '=', docs.company_id.id), ('state', '=', docs.state)]
        return search

    def _get_search_from_type(self, docs):
        search = []
        if docs.type == 'without_refund':
            search += [('credit_note', '=', False)]
        elif docs.type == 'only_refund':
            search += [('credit_note', '=', True)]
        return search

    def get_rule(self, slip_id, rule):
        self._cr.execute(
            "select total from hr_payslip_line where salary_rule_id in (select id from hr_salary_rule where lower(code) = '%s') and slip_id in (select id from hr_payslip where id = %s)" % (
                rule.lower(), slip_id))
        res = self._cr.fetchone()
        if res:
            return res[0]
        else:
            return 0.0

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

    def get_total_rule(self, rule, data):
        slip_obj = self.get_data(data)
        total = 0
        for slip_id in slip_obj:
            rule_amt = self.get_rule(slip_id.id, rule, data)
            if rule_amt != None:
                total = total + rule_amt
            else:
                total = total
        return total
