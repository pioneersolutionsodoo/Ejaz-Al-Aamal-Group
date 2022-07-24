
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import date, datetime, time
from hijri_converter import Hijri, Gregorian



class HrLeave(models.Model):
    _inherit = 'hr.leave'

    period_type = fields.Selection([('am', 'Morning'), ('pm', 'Evening')], string='Authorization Period', default='am')
    date_actual_return = fields.Datetime(string='Actual Return')
    deduction_exempt = fields.Boolean(string='Deduction Exempt', default=False)

    def compute_ar_day_name(self, date):
        # en_day = date.today().strftime('%a')
        en_day = date.strftime('%a')
        ar_day = ''
        if en_day == 'Sat':
            ar_day = 'السبت'
        if en_day == 'Sun':
            ar_day = 'الأحد'
        if en_day == 'Mon':
            ar_day = 'الإثنين'
        if en_day == 'Tue':
            ar_day = 'الثلاثاء'
        if en_day == 'Wed':
            ar_day = 'الأربعاء'
        if en_day == 'Thu':
            ar_day = 'الخميس'
        if en_day == 'Fri':
            ar_day = 'الجمعة'
        return ar_day
