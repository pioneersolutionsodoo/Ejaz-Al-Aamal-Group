from odoo import api, fields, models

class Stock(models.Model):
    _inherit = 'stock.location'

    # Relational Fields
    partner_id = fields.Many2one('res.partner')
