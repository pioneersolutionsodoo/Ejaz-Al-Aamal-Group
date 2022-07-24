from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_contact_name(self, partner, name):
        return "%s" % (name)
