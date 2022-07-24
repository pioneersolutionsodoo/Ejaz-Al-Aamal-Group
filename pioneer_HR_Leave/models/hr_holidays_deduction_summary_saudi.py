# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime,timedelta
from lxml import etree, html

import math
import collections
# try:
#     from service_solutions.common_ps.models.nazar import mail_create, get_email_from, get_config
# except:
#     try:
#         from odoo.common_ps.models.nazar import mail_create, get_email_from, get_config
#     except:
#         from odoo.addons.common_ps.models.nazar import mail_create, get_email_from, get_config

from odoo import SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.addons.pioneer_HR_Leave.models import ps_br_hr_config_global as hg


class hr_holidays_deduction_summary_saudi(models.Model):
    _name = 'hr.holidays.deduction.summary.saudi'
    _description = "Hr holidays deduction summary"

    leave_id = fields.Many2one('hr.leave', string='Leave', required=True, readonly=True)
    deduction_type = fields.Selection(related='leave_id.leave_type_id.deduction_type', required=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True)
    date = fields.Datetime(string='Date', required=True, readonly=True, )
    amount = fields.Float(string='Amount', required=True, readonly=True)

    state = fields.Selection([
        ('deducted', 'Deducted'),
        ('undeducted', 'Undeducted'),
    ],
        'Status', readonly=True, default='undeducted')








     
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
