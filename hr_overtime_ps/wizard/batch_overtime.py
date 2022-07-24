# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, Warning, RedirectWarning


class BatchOvertime(models.TransientModel):
    _name = 'batch.overtime'
    _rec_name = 'name'
    _description = 'Batch Overtime'

    name = fields.Char(string='Serial', default=lambda self: _('New'))
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    overtime_summary = fields.Char(string="Summary", required=True, )
    request_hours = fields.Float(string="Request Hours", required=True)

    employee_ids = fields.Many2many('hr.employee',)
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env['res.company']._company_default_get('hr.holidays.saudi'))

    @api.constrains('date_from', 'date_to')
    def _date_check(self):
        if self.date_from > self.date_to:
            raise except_orm(_('Invalid Date!'), _('The Date From should be less than or equal Date To'))

    # @api.model
    # def create(self, values):
    #     if values.get('name', 'New') == 'New':
    #         values['name'] = self.env['ir.sequence'].next_by_code('batch.overtime') or 'New'
    #     result = super(BatchOvertime, self).create(values)
    #     return result
    # def _create_all_overtime(self, employee, start_date, end_date):
    #     return self.env['hr.overtime.ps'].create(
    #         {
    #             'employee_id': employee.id,
    #             'department_id': employee.department_id.id or False,
    #             'date_from': start_date,
    #             'date_to': end_date,
    #             'overtime_summary': [[0, 0, {
    #                 'name': self.overtime_summary,
    #                 'date': self.date_from,
    #                 'request_hours': self.request_hours,
    #             }]]
    #         }
    #     )
    def create_overtime(self):
        overtime_model = self.env['hr.overtime.ps']
        if self.employee_ids and self.date_to and self.date_from and self.request_hours:
            overtime_vals = []
            for employee in self.employee_ids:
                print(employee.name)
                print(employee.department_id.name)
                # overtime_model.create({
                overtime_vals.append({
                    'employee_id': employee.id,
                    'department_id': employee.department_id.id or False,
                    'contract_id': employee.contract_id.id or False,
                    'job_id': employee.job_id.id or False,
                    'date_from': self.date_from,
                    'date_to': self.date_to,
                    'request_hours': self.request_hours,
                    'overtime_summary': [[0, 0, {
                        'name': self.overtime_summary,
                        'date': self.date_from,
                        'request_hours': self.request_hours,
                    }]]
                })
            res = overtime_model.create(overtime_vals)
            for rec in res:
                rec._compute_hours()
            return res