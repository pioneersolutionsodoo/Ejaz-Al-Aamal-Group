# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def run_reminder_about_employee_id_expiry(self):
        iqama_expiry_limit = self.env['ir.config_parameter'].sudo().get_param('ps_expiry_reminder.iqama_expiry_limit')
        passport_expiry_limit = self.env['ir.config_parameter'].sudo().get_param(
            'ps_expiry_reminder.passport_expiry_limit')
        remind_user_id = self.env['ir.config_parameter'].sudo().get_param('ps_expiry_reminder.remind_user_id')
        hr_remind_user_id = self.env['ir.config_parameter'].sudo().get_param('ps_expiry_reminder.hr_remind_user_id')
        current_date = date.today()

        employees = self.env['hr.employee'].search([('work_email', '!=', False), ('iqama_expiry_date', '!=', False)])

        if employees:
            expiry_iqama_employees = []
            expiry_passport_employees = []
            for employee in employees:
                iqama_difference = employee.iqama_expiry_date - current_date
                if iqama_difference.days <= int(iqama_expiry_limit):
                    expiry_iqama_employees.append(employee.name)

                if employee.expiration_date_of_expiry:
                    passport_difference = employee.expiration_date_of_expiry - current_date
                    if passport_difference.days <= int(passport_expiry_limit):
                        expiry_passport_employees.append(employee.name)

            user_ids = []
            if remind_user_id:
                user_ids.append(int(remind_user_id))
            if hr_remind_user_id:
                user_ids.append(int(hr_remind_user_id))

            if expiry_iqama_employees:
                body_html = _(
                    'Hello,<br><br>There are employees about to end their Iqama<br> "%s"') % (expiry_iqama_employees)

                user_ids = self.env['res.users'].search([('id', 'in', user_ids)])
                if user_ids:
                    for user in user_ids:
                        if user.partner_id.email:
                            self.env['mail.mail'].create({
                                'body_html': body_html,
                                'state': 'outgoing',
                                'email_from': self.env.user.email_formatted or '',
                                'email_to': user.partner_id.email,
                                'subject': 'Iqama Expiry Reminder'
                            }).send()

            if expiry_passport_employees:
                body_html = _(
                    'Hello,<br><br>There are employees about to end their Passport numbers<br> "%s"') % (
                                expiry_passport_employees)

                user_ids = self.env['res.users'].search([('id', 'in', user_ids)])
                if user_ids:
                    for user in user_ids:
                        if user.partner_id.email:
                            self.env['mail.mail'].create({
                                'body_html': body_html,
                                'state': 'outgoing',
                                'email_from': self.env.user.email_formatted or '',
                                'email_to': user.partner_id.email,
                                'subject': 'Passport Expiry Reminder'
                            }).send()


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.model
    def contract_expiry(self):
        contracts = self.env['hr.contract'].search([])
        for rec in contracts:
            if rec.date_end:
                date_now = fields.Date.from_string(date.today())
                expire = fields.Date.from_string(rec.date_end)
                print(date_now)
                print(expire)
                difference = relativedelta(expire, date_now)
                total_days = difference.days + difference.years * 12 * 29 + difference.months * 29
                print(difference.days)
                print(total_days)
                if total_days <= 10:
                    # hr_mangers = self.env.user.has_group('hr.group_hr_manager')
                    # print(hr_mangers)
                    body_html = _(
                        'Hello,<br><br>There are employees called "%s" about to end their Contract in<br> "%s"') % (
                                    rec.employee_id.name, expire)

                    user_ids = self.env['res.users'].search([])
                    if user_ids:
                        for user in user_ids:
                            if user.has_group('hr.group_hr_manager'):
                                if user.partner_id.email:
                                    self.env['mail.mail'].create({
                                        'body_html': body_html,
                                        'state': 'outgoing',
                                        'email_from': self.env.user.email_formatted or '',
                                        'email_to': user.partner_id.email,
                                        'subject': 'Contract Expiry Reminder'
                                    }).send()
