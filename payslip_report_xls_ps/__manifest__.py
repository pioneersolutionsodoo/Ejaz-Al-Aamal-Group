# -*- coding: utf-8 -*-
{
    'name': "Payslip Report XlS",
    'description': """Payslip Report XlS""",
    'author': "Mani",
    'website': "http://www.ps-sa.net",
    'category': 'Uncategorized',
    'version': '15.0.0.1',
    'depends': ['base','hr','hr_payroll','hr_contract','alshrooq_employee_details'],
    'data': [
        'security/ir.model.access.csv',
        #'views/sale_order_line.xml',
        'views/templates.xml',
        'report/ps_payslip_report.xml',
        'report/hr_report_payslip_templates.xml',
        'views/ps_payslip_view.xml',
        'views/hr_employee.xml',
        'views/hr_contract.xml',
        'views/hr_payslip_view.xml'
    ],
    'license': 'LGPL-3',
}