# -*- coding: utf-8 -*-

{
    'name': 'Payroll customize',
    'version': '13.0.0',
    'author': "Mostafa Abbas, Pioneer Solution",
    'category': 'Human Resources',
    'sequence': 28,
    'website': 'http://www.ps-sa.net',
    'depends': ['hr','hr_payroll'],
    'data': [
        'data/data.xml',
        'views/hr_contract_view.xml',
        'views/payslip_other_input_type.xml',
        'views/salary_rule_view.xml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}