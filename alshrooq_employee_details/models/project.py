# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Contract(models.Model):
    _inherit = "project.project"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

