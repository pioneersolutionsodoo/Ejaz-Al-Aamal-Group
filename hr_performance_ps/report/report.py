# -*- coding: utf-8 -*-

import time
from odoo import api, models, _


class hr_performance_evaluation_report(models.AbstractModel):
    _name = 'hr_performance_evaluation_report'

    def _get_currency(self, currency_id):
        currency = self.pool.get('res.currency').browse(self.cr, self.uid, currency_id)
        return currency

    def _get_result(self, performance_id):
        cr, uid = self._cr, self._uid
        # if product_id:
        #     where_clause = where_clause + " and il.product_id = " + str(product_id)

        isql = """ select *
                   from
                    (
                    select distinct pe_technique
                        ,pe_quality
                        ,pe_quantity
                        ,pe_implementation
                        ,pe_completition
                        ,pe_team
                        ,pe_desire
                        ,pe_professional
                        ,pe_pressure
                        ,pe_adapt
                        ,pe_reporting
                        ,pe_honesty
                        ,pe_assets
                        ,pe_relationship
                        ,pe_punctuality
                        ,pe_appearance

                    from sdl_performance_evaluation e
                    inner join hr_employee h on h.id = e.employee_id
                    inner join resource_resource ro on ro.id = h.resource_id
                    where e.id = """ + str(performance_id) + """ --and ro.user_id = """ + str(uid) + """
                    )data
                    """
        cr.execute(isql)
        res = cr.dictfetchall()
        return res

    @api.model
    def render_html(self, docids, data=None):
        model = 'hr.performance.evaluation'
        docs = self.env[model].browse(2)
        docargs = {
            'doc_ids': self._ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'get_result': self._get_result(2),
        }
        return self.env.ref('hr_performance_ps.hr_performance_evaluation_report').report_action(self, docargs)