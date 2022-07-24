# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError

class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def process_sheet(self):
        if not self.employee_id.address_home_id:
            raise ValidationError(_('You must add the home adress of employee!'))
        loan_ids = self.env['hr.employee.loan.ps'].search([('employee_id','=', self.employee_id.id),('state','=','approve')])
        for record in loan_ids:
            for line in record.hr_employee_loan_line_ps:
                if line.installment_date >= self.date_from and line.installment_date <= self.date_to and line.confirm == True and line.state == 'notdeducted':
                    line.state = 'deducted'
                    record.loan_open = True

        advance_ids = self.env['hr.employee.advance.ps'].search([('employee_id','=', self.employee_id.id)])
        for record in advance_ids:
            for line in record.hr_employee_advance_line_ps:
                if line.installment_date >= self.date_from and line.installment_date <= self.date_to and line.confirm == True and line.state == 'notdeducted':
                    line.state = 'deducted'
                    record.advance_open = True
        return super(HrPayslip, self).process_sheet()

        





# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
