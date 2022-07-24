# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import except_orm, Warning, RedirectWarning


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    total_eosb = fields.Float(compute='_get_total_eosb', groups="hr.group_hr_user", store=True)

    # Relational Fields
    eosb_emp_type_id = fields.Many2one('eosb.emp.type', string="EOSB Category", domain=[('state', '=', 'active')], groups="hr.group_hr_user")

    @api.depends('aj_date', 'contract_ids', 'contract_id')
    def _get_total_eosb(self):
        for item in self:
            total_salary = 0
            eosb = 0
            contract_obj = self.env['hr.contract']
            contract_ids = contract_obj.search([('employee_id', '=', item.id)], limit=1)
            for record in contract_ids:
                total_salary += record.wage
            sdate = item.aj_date
            edate = date.today()
            if sdate and edate:
                tday = edate
                sday = (tday - sdate).days
                sday = sday + 1
                if sday <= 1826:
                    eosb = (total_salary / 2) * (sday / 365.25)
                else:
                    eosb = total_salary * (sday / 365.25)
            item.total_eosb = round(eosb, 2)

    @api.model
    def monthly_get_eosb_for_every_employee(self):
        hr_employee_ids = self.env['hr.employee'].search([])
        contract_obj = self.env['hr.contract']
        for item in hr_employee_ids:
            if item.aj_date:
                total_salary = 0
                eosb = 0
                total_salary = item.contract_id.wage
                sdate = item.aj_date
                edate = date.today()
                if sdate and edate:
                    tday = edate
                    sday = (tday - sdate).days
                    sday = sday + 1
                    # print(int((sday / 365.25)))
                    list = []
                    if sday <= 1826 and sday >= 731:
                        yearly = item.aj_date.year + 1
                        for year in range(int((sday / 365.25))):
                            if year + 1 <= 2:
                                amount = 0
                            elif year + 1 > 2 and year + 1 <= 5:
                                amount = total_salary / 2
                            else:
                                amount = total_salary
                            print(yearly)
                            print(year + 1)
                            print(amount)
                            list.append((0, 0, {
                                "employee_id": item.id,
                                "year": yearly,
                                "amount": amount,
                            }))
                            item.reward_yearly = [(6, 0, [])]
                            item.reward_yearly = list
                            yearly += 1
                        eosb = (total_salary / 2) * int((sday / 365.25))
                    elif sday > 1826:
                        yearly = item.aj_date.year + 1
                        for year in range(int((sday / 365.25))):
                            if year + 1 <= 2:
                                amount = 0 * year
                            elif year + 1 > 2 and year + 1 <= 5:
                                amount = (total_salary / 2) * year
                            else:
                                amount = total_salary * year
                            print(yearly)
                            print(year + 1)
                            print(amount)
                            list.append((0, 0, {
                                "employee_id": item.id,
                                "year": yearly,
                                "amount": amount,
                            }))
                            item.reward_yearly = [(6, 0, [])]
                            item.reward_yearly = list
                            yearly += 1
                        eosb = total_salary * int((sday / 365.25))
                item.total_eosb = round(eosb, 2)

    # @api.model
    # def monthly_get_eosb_for_every_employee(self):
    #     hr_employee_ids = self.env['hr.employee'].search([])
    #     contract_obj = self.env['hr.contract']
    #     for item in hr_employee_ids:
    #         if item.aj_date:
    #             total_salary = 0
    #             eosb = 0
    #             contract_ids = contract_obj.search([('employee_id', '=', item.id)])
    #             for record in contract_ids:
    #                 total_salary += record.wage
    #             sdate = item.aj_date
    #             edate = date.today()
    #             if sdate and edate:
    #                 tday = edate
    #                 sday = (tday - sdate).days
    #                 sday = sday + 1
    #                 if sday <= 1826:
    #                     eosb = (total_salary / 2) * (sday / 365.25)
    #                 else:
    #                     eosb = total_salary * (sday / 365.25)
    #             item.total_eosb = round(eosb, 2)

    def eosb_payslip(self, employee):
        total_salary = 0
        eosb = 0
        contract_ids = self.env['hr.contract'].search([('employee_id', '=', employee)])
        for record in contract_ids:
            total_salary += record.wage
        employee_id = self.env['hr.employee'].search([('id', '=', employee)])
        sdate = employee_id.aj_date
        edate = date.today()
        if sdate and edate:
            tday = edate
            sday = (tday - sdate).days
            sday = sday + 1
            if sday <= 1826:
                eosb = (total_salary / 12) / 2
            else:
                eosb = total_salary / 12
        return eosb

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
