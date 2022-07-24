# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date

import datetime
from datetime import datetime, date
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError

from pprint import pprint


class ExpiryReminderWizard(models.TransientModel):
    _name = 'expiry.reminder.wizard'
    _description = 'Expiry Reminder Wizard'

    date_from = fields.Date()
    date_to = fields.Date(default=date.today())
    expiry_type = fields.Selection(selection=[('iqama', _('Iqama')), ('passport', _('Passport')), ], default='iqama')

    # Relational fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)

    def generate_report(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'expiry_type': self.expiry_type,
            'company_id': self.company_id.id,
        }
        return self.env.ref('ps_expiry_reminder.expiry_reminder_action_report').report_action([], data=data)

    @api.onchange('date_from', 'date_to')
    def restrict_date_period(self):
        if self.date_to and self.date_from:
            if self.date_from > self.date_to:
                raise UserError(_('Date From Can not be Greater than Date To'))

    # def generate_report_xlsx(self):
    #     data = {
    #         'date_from': self.date_from,
    #         'date_to': self.date_to,
    #         'company_id': self.company_id.id,
    #     }
    #     return self.env.ref('ps_expiry_reminder.action_report_xlsx').report_action([],
    #                                                                                      data=data)


class ReportExpiryReminderWizard(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.ps_expiry_reminder.expiry_reminder_template'
    _description = 'report.ps_expiry_reminder.expiry_reminder_template'

    @api.model
    def _get_report_values(self, docids, data=None):

        company_id = data['company_id']
        date_from = data['date_from']
        date_to = data['date_to']
        expiry_type = data['expiry_type']
        # iqama_expiry_limit = self.env['ir.config_parameter'].sudo().get_param('ps_expiry_reminder.iqama_expiry_limit')
        # passport_expiry_limit = self.env['ir.config_parameter'].sudo().get_param(
        #     'ps_expiry_reminder.passport_expiry_limit')
        current_date = date.today()

        docs = []

        if expiry_type == 'iqama':
            employees = self.env['hr.employee'].search(
                [('iqama_expiry_date', '>=', date_from), ('iqama_expiry_date', '<=', date_to),
                 ('company_id', '=', company_id)])
            if employees:
                for employee in employees:

                    docs.append({
                        'employee_code': employee.emp_code,
                        'employee_name': employee.name,
                        'number': employee.identification_id,
                        'expiry_date': employee.iqama_expiry_date,
                    })

        elif expiry_type == 'passport':
            employees = self.env['hr.employee'].search(
                [('expiration_date_of_expiry', '>=', date_from), ('expiration_date_of_expiry', '<=', date_to),
                 ('company_id', '=', company_id)])
            if employees:
                for employee in employees:
                    docs.append({
                        'employee_code': employee.emp_code,
                        'employee_name': employee.name,
                        'number': employee.passport_id,
                        'expiry_date': employee.expiration_date_of_expiry,
                    })
        return {
            'docs': docs,
            'expiry_type': expiry_type,
            'current_date': date.today(),
            'company_branch': self.env.user.company_id.name,
            'company': self.env.user.company_id,
        }
