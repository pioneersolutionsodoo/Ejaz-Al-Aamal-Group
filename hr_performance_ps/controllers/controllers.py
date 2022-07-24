# -*- coding: utf-8 -*-
from odoo import http

# class HrPerformancePs(http.Controller):
#     @http.route('/hr_performance_ps/hr_performance_ps/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_performance_ps/hr_performance_ps/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_performance_ps.listing', {
#             'root': '/hr_performance_ps/hr_performance_ps',
#             'objects': http.request.env['hr_performance_ps.hr_performance_ps'].search([]),
#         })

#     @http.route('/hr_performance_ps/hr_performance_ps/objects/<model("hr_performance_ps.hr_performance_ps"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_performance_ps.object', {
#             'object': obj
#         })