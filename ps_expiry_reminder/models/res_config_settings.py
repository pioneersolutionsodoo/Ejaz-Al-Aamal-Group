# -*- coding: utf-8 -*-
from odoo import fields, models,api,_


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    iqama_expiry_limit = fields.Integer(config_parameter='ps_expiry_reminder.iqama_expiry_limit')
    passport_expiry_limit = fields.Integer(config_parameter='ps_expiry_reminder.passport_expiry_limit')

    # Relational Fields
    remind_user_id = fields.Many2one('res.users',config_parameter='ps_expiry_reminder.remind_user_id')
    hr_remind_user_id = fields.Many2one('res.users',config_parameter='ps_expiry_reminder.hr_remind_user_id')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        iqama_expiry_limit = ICPSudo.get_param('ps_expiry_reminder.iqama_expiry_limit')
        passport_expiry_limit = ICPSudo.get_param('ps_expiry_reminder.passport_expiry_limit')
        res.update(
            iqama_expiry_limit=int(iqama_expiry_limit),
            passport_expiry_limit=int(passport_expiry_limit),

        )
        return res
