from odoo import api, fields, models, _
from datetime import date


class PurchaseOrderSearch(models.TransientModel):
    _name = 'eosb.employee.report'
    _description = 'Eosb Employee Report Record'

    date = fields.Date(_('Date'), default=date.today())
    year_from = fields.Integer(_('From Year'), required=True)
    year_to = fields.Integer(_('To Year'), required=True)
    department_ids = fields.Many2many(comodel_name="hr.department", string="Departments", )
    employees_ids = fields.Many2many(comodel_name="hr.employee", string="Employees", )

    def print_report(self):
        search_criteria = []
        self.env['hr.employee'].monthly_get_eosb_for_every_employee()
        reward_pool = self.env['reward.yearly']
        if self.year_from:
            search_criteria.append(('year', '>=', self.year_from))
        if self.year_to:
            search_criteria.append(('year', '<=', self.year_to))
        if self.employees_ids:
            list = []
            for rec in self.employees_ids:
                list.append(rec.id)
            search_criteria.append(('employee_id.id', 'in', self.employees_ids.ids))
        if self.department_ids:
            list = []
            for rec in self.department_ids:
                list.append(rec.id)
            search_criteria.append(('employee_id.department_id.id', 'in', self.department_ids.ids))
        resuts = reward_pool.search(search_criteria)
        res = []
        for rec in resuts:
            vals = {
                'id': rec.employee_id.id,
                'employee': rec.employee_id.name,
                'year': [],
                'amount': [],
            }
            for line in resuts:
                if line.employee_id.id == rec.employee_id.id:
                    vals['year'].append(line.year)
                    vals['amount'].append(line.amount)
            res.append(vals)

        final = []
        for i in res:
            if i not in final:
                final.append(i)
        data = {'model': 'eosb.employee.report', 'form': self.read()[0], }

        data['final'] = final
        print('final', data['final'])
        for line in data['final']:
            print(line)
        return self.env.ref('ps_eosb_report.eosb_reward_report_action').report_action(self, data=data)
