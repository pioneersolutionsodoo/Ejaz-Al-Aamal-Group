from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta



class HrContract(models.Model):
    _inherit = 'hr.contract'
    probationary_period = fields.Integer(string="Probationary Period", help="Probationary Period in Months")
    probationary_date = fields.Date(string="Probationary Date", compute="compute_probationary_date",
                                    help="Probationary End Date")

    @api.depends('probationary_period', 'date_start')
    def compute_probationary_date(self):
        for rec in self:
            if rec.date_start and rec.probationary_period > 0:
                rec.probationary_date = fields.Date.to_string(rec.date_start + relativedelta(months=rec.probationary_period))
            else:
                rec.probationary_date = False

    def get_ar_day(self):
        en_day = date.today().strftime('%a')
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

    def print_job_offer(self):
        if self.state != 'draft':
            raise UserError('You can print only Job Offer only for a contract in New state!')
        return self.env.ref('ps_hr_custom.job_offer_report').report_action(self)