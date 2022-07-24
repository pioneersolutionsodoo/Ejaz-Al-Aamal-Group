# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
class ResCompany(models.Model):
    _inherit = 'res.company'

    business_trip_journal_id = fields.Many2one('account.journal', string='Business Trip Journal', help = "The journal used when the Business Trip is done.")

# class hr_accounting_config(models.TransientModel):
#     _inherit = 'hr.accounting.config'
#
#     def _get_business_trip_journal(self):
#         config = self._get_hr_accounting_config()
#         if config and config.business_trip_journal_id:return config.business_trip_journal_id.id
#         return False
#
#
#     business_trip_journal_id = fields.Many2one('account.journal', string='Business Trip Journal', help = "The journal used when the Business Trip is done.", default=_get_business_trip_journal)










