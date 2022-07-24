# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime,timedelta
import math


class hr_official_holidays_saudi(models.Model):
    _name = 'hr.official.holidays.saudi'
    _description = "Hr official holidays saudi"

    @api.depends('date_from', 'date_to')
    def _compute_days(self):
        DATETIME_FORMAT = "%Y-%m-%d"
        no_days = 0
        if self.date_from and self.date_to:
            if self.date_from > self.date_to and self.date_to:
                raise except_orm(_('Invalid Date!'), _('Date To must be greater or equal to Date From'))
            if (self.date_to and self.date_from) and (self.date_from <= self.date_to):
                date_from = datetime.strptime(self.date_from, DATETIME_FORMAT)
                date_to = datetime.strptime(self.date_to, DATETIME_FORMAT)
                timedelta = date_to - date_from
                diff_day = timedelta.days + float(timedelta.seconds) / 86400
                no_days = round(math.floor(diff_day))+1
            self.no_days = no_days

    name = fields.Char()
    date_from = fields.Date()
    date_to = fields.Date()
    no_days = fields.Integer(store=True, compute='_compute_days')

    state = fields.Selection([
            ('draft',_('Draft')),
            ('approve',_('Approve')),
            ('cancel',_('Cancel')),

        ], index=True, readonly=True, default='draft', copy=False,
        help="Status")

    def approve(self):
        return self.write({'state': 'approve'})

    def cancel(self):
        return self.write({'state': 'cancel'})






     
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
