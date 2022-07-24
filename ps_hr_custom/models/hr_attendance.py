from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import re
import pytz
# Datetime.now().replace(hour=0, minute=0, second=0)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    check_in = fields.Datetime(required=False, default=datetime.now().replace(second=0))

    check_in_date = fields.Date(string="Check In Date", store=True,
                                compute="_get_check_date_time", inverse='_set_check_date_time')
    check_in_time = fields.Char(string="Check In Time", store=True,
                                compute="_get_check_date_time", inverse='_set_check_date_time')

    check_out_date = fields.Date(string="Check Out Date", store=True,
                                 compute="_get_check_date_time", inverse='_set_check_date_time')
    check_out_time = fields.Char(string="Check Out Time", store=True,
                                 compute="_get_check_date_time", inverse='_set_check_date_time')

    @api.constrains('check_in_time', 'check_out_time')
    def _check_time_exp(self):
        print('Entered')
        allowed = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', ':']
        for rec in self:
            if rec.check_in_time:
                if len(rec.check_in_time) != 5 or ':' not in rec.check_in_time \
                    or int(rec.check_in_time.split(':')[0]) > 23 or int(rec.check_in_time.split(':')[1]) > 59 \
                        or any([c not in allowed for c in rec.check_in_time]):
                    print('yes')
                    raise ValidationError(_('Check in time not valid.\nUse formate 00:00.'))
            if rec.check_out_time:
                if len(rec.check_out_time) != 5 or ':' not in rec.check_out_time \
                    or int(rec.check_out_time.split(':')[0]) > 23 or int(rec.check_out_time.split(':')[1]) > 59 \
                        or any([c not in allowed for c in rec.check_out_time]):
                    print('yes')
                    raise ValidationError(_('Check in time not valid.\nUse formate 00:00.'))

    # @api.constrains('check_in_time')
    # def validate_mail(self):
    #     exp = '^(2[0-3]|[01]?[0-9]){2}:([0-5]?[0-9]){2}$'
    #     for rec in self:
    #         if rec.check_in_time:
    #             match = re.match(exp, rec.check_in_time)
    #             if match == None:
    #                 raise ValidationError(_('Check in time not valid.\nUse formate 00:00.'))
    #         if rec.check_out_time:
    #             match = re.match(exp, rec.check_out_time)
    #             if match == None:
    #                 raise ValidationError(_('Check out time not valid.\nUse formate 00:00.'))

    @api.depends('check_in', 'check_out')
    def _get_check_date_time(self):
        timezone = pytz.timezone(self.env.context.get('tz') or 'UTC')
        for rec in self:
            if rec.check_in:
                check_in_tz = pytz.utc.localize(rec.check_in).astimezone(timezone)
                rec.check_in_date = check_in_tz.date()
                rec.check_in_time = check_in_tz.strftime('%H:%M')
            else:
                rec.check_in_date = False
                rec.check_in_time = False

            if rec.check_out:
                check_out_tz = pytz.utc.localize(rec.check_in).astimezone(timezone)
                rec.check_out_date = check_out_tz.date()
                rec.check_out_time = check_out_tz.strftime('%H:%M')
            else:
                rec.check_out_date = False
                rec.check_out_time = False

    @api.depends('check_in_date', 'check_in_time', 'check_out_date', 'check_out_time')
    def _set_check_date_time(self):
        timezone = pytz.timezone(self.env.context.get('tz') or 'UTC')
        for rec in self:
            if rec.check_in_date and rec.check_in_time:
                date_str = rec.check_in_date.strftime('%Y-%m-%d')
                time_str = rec.check_in_time
                check_in_str = ' '.join([date_str, time_str])
                check_in = datetime.strptime(check_in_str, '%Y-%m-%d %H:%M')
                check_in_tz = timezone.localize(check_in).astimezone(pytz.utc)
                rec.check_in = check_in_tz.strftime('%Y-%m-%d %H:%M:%S')

            if rec.check_out_date and rec.check_out_time:
                date_str = rec.check_out_date.strftime('%Y-%m-%d')
                time_str = rec.check_out_time
                check_out_str = ' '.join([date_str, time_str])
                check_out = datetime.strptime(check_out_str, '%Y-%m-%d %H:%M')
                check_in_tz = timezone.localize(check_out).astimezone(pytz.utc)
                rec.check_out = check_in_tz.strftime('%Y-%m-%d %H:%M')

