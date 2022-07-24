# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT



def _get_employee(obj):
    ids = obj.env['hr.employee'].search([('user_id', '=', obj.env.uid)])
    if ids:
        return ids[0]
    else:
        raise ValidationError(_('The user is not an employee.'))
    return False

class hr_employee_loan_type_ps(models.Model):
    _name = 'hr.employee.loan.type.ps'
    _description = 'Loan Type'

    name = fields.Char(string='Name', required=True)
    is_annual = fields.Boolean("Annual Vacation")
