import time
from odoo import api, models, fields,_
from datetime import datetime
from dateutil import relativedelta
from dateutil.parser import parse
from odoo.exceptions import UserError
import base64
from pprint import pprint


class SalaryStatementReportWiz(models.TransientModel):
    _name = "ps.salary.statement.report.wiz"
    _description = "ps.salary.statement.report.wiz"

    f_date = fields.Date('From Date', help='From Date', required=True,default=lambda *a: time.strftime('%Y-%m-01'))
    t_date = fields.Date('To Date', help='To Date', required=True, default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    type = fields.Selection([('with_refund', 'With Refund'),('without_refund', 'Without Refund'),('only_refund', 'Only Refund')], 'Type', required=True,default='without_refund')
    state = fields.Selection([('all', 'All'),('draft', 'Draft'),('verify', 'Waiting'),('done', 'Done'),('cancel', 'Rejected'),], 'State', required=True, default='all')
    report_type = fields.Selection([('xls','XLS')],'Report Type', default='xls')

    # Relational Fields
    work_locations_id = fields.Many2many('work.location.name')
    analytic_account_ids = fields.Many2many('account.analytic.account')
    company_id = fields.Many2one('res.company', 'Company', required=True,default=lambda self: self.env.user.company_id)

    def check_report(self):
        data = {}
        data['form'] = self.read(['f_date', 't_date', 'company_id','type','state','analytic_account_ids'])[0]
        if self.report_type == 'xls':
            return self.get_xls_data(data['form'])
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read(['f_date', 't_date', 'company_id','type','state'])[0])
        return self.env.ref("payslip_report_xls_ps.ps_action_report_payslip_ps").with_context(landscape=True).report_action(self, data=data)

    def check_wages_report(self):
        data = {}
        data['form'] = self.read(['f_date', 't_date', 'company_id', 'type', 'state','analytic_account_ids'])[0]
        return self.get_wages_xls_data(data['form'])

    def get_xls_data(self, data):
        clause = [('company_id', '=', self.company_id.id)]
        if self.analytic_account_ids.ids:
            clause.append(('analytic_account_id', 'in', self.analytic_account_ids.ids))
        clause += self.get_search_from_state()
        clause += self.get_search_from_type()
        payslip_ids = self.env['hr.payslip'].search(clause)
        if not payslip_ids:
            raise UserError('Null Data Record not found.')

        rec_string = payslip_ids._ids

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=hr.payslip&field=datas&id=%s&filename=Payslip.xls&wiz_id=%s' % (
                str(rec_string), self.ids),
            'target': 'new',
            'tag': 'reload',
        }

    def get_wages_xls_data(self, data):
        clause = [('company_id', '=', self.company_id.id)]
        clause += self.get_search_from_state()
        clause += self.get_search_from_type()
        payslip_ids = self.env['hr.payslip'].search(clause)
        if not payslip_ids:
            raise UserError('Null Data Record Not Found.')

        rec_string = payslip_ids._ids

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=hr.payslip&field=datas&id=%s&filename=Payslip.xls&wiz_id=%s&from=wages' % (
                str(rec_string), self.ids),
            'target': 'new',
            'tag': 'reload',
        }

    def get_search_from_state(self):

        # Here i user only self.f_date to search for one month not period [from - to]
        search = [('date_from', '<=', self.f_date), ('date_to', '>=', self.f_date),
                  ('company_id', '=', self.company_id.id)]
        if self.state != 'all':
            search += [('date_from', '<=', self.f_date), ('date_to', '>=', self.f_date),
                       ('company_id', '=', self.company_id[0]), ('state', '=', self.state)]
        return search

    def get_search_from_type(self):
        search = []
        if self.type == 'without_refund':
            search += [('credit_note', '=', False)]
        elif self.type == 'only_refund':
            search += [('credit_note', '=', True)]
        return search