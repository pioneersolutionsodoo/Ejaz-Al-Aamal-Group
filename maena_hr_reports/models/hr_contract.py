
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import date, datetime, time
from hijri_converter import Hijri, Gregorian



class HrContract(models.Model):
    _inherit = 'hr.contract'

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

    def compute_hijri_date(self, date):
        if date:
            year = int(date.year)
            month = int(date.month)
            day = int(date.day)
            print('year----> ',year)
            print('year----> ',month)
            print('year----> ',day)
            hijri_date = str(str(Gregorian(year, month, day).to_hijri()))
            return hijri_date
        else:
            return False
