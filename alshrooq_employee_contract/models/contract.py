# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil import relativedelta


class Contract(models.Model):
    _inherit = "hr.contract"

    housing_allowance = fields.Float()
    transportation_allowance = fields.Float()
    project_allowance = fields.Float()
    supervisory_allowance = fields.Float()
    coordination_allowance = fields.Float()
    developement_allowance = fields.Float()
    mobile_allowance = fields.Float()
    travel_allowance = fields.Float()
    gosi_allowance = fields.Float()
    gosi_deduction = fields.Float()
    rentry_allowance = fields.Float()
    number_of_tickets_per_year = fields.Float('Number of tickets per year')
    total = fields.Float('Gross', compute='_get_sum')
    contract_period = fields.Float(compute='_get_contract_period')
    iqama_transfer = fields.Float()
    iqama_expense = fields.Float()
    iqama_per_month = fields.Float()
    recruitment_allowance = fields.Float()
    employee_medical_insurance = fields.Float()
    family_medical_insurance = fields.Float()
    other_allowance = fields.Float()
    other_deduction = fields.Float()

    @api.depends('date_start', 'date_end')
    def _get_contract_period(self):
        for contract in self:
            if contract.date_start and contract.date_end:
                d1 = datetime.strftime(contract.date_start, "%m-%d-%Y")
                d1 = datetime.strptime(d1, "%m-%d-%Y")

                d2 = datetime.strftime(contract.date_end, "%m-%d-%Y")
                d2 = datetime.strptime(d2, "%m-%d-%Y")
                contract.contract_period = abs((d2 - d1).days)
            else:
                contract.contract_period = 0.0

    @api.depends('wage', 'housing_allowance', 'recruitment_allowance', 'transportation_allowance', 'project_allowance',
                 'supervisory_allowance', 'coordination_allowance', 'developement_allowance', 'mobile_allowance',
                 'travel_allowance', 'gosi_allowance', 'gosi_deduction', 'other_allowance', 'other_deduction')
    def _get_sum(self):
        for rec in self:
            total = rec.housing_allowance + rec.recruitment_allowance + rec.transportation_allowance + rec.project_allowance + rec.supervisory_allowance + rec.coordination_allowance + rec.developement_allowance + rec.mobile_allowance + rec.travel_allowance + rec.gosi_allowance + rec.other_allowance - rec.other_deduction - rec.gosi_deduction
            rec.total = total + rec.wage


class HrSalaryRules(models.Model):
    _inherit = 'hr.salary.rule'

    input_type_ids = fields.One2many(comodel_name="hr.payslip.input.type", inverse_name="salary_rule_id",
                                     string="Input Type", readonly=True)


class HrInputType(models.Model):
    _inherit = 'hr.payslip.input.type'

    salary_rule_id = fields.Many2one(comodel_name="hr.salary.rule", string="Salary Rule", )


class HrInput(models.Model):
    _inherit = 'hr.payslip.input'

    salary_rule_id = fields.Many2one(comodel_name="hr.salary.rule", string="Salary Rule",
                                     related="input_type_id.salary_rule_id")
