# -*- coding: utf-8 -*-

{
    'name': 'OverTime Management',
    'version': '11.0',
    'author': "Mani, Pioneer Solution",
    'category': 'Human Resources',
    'sequence': 28,
    'website': 'http://www.ps-sa.net',
    'depends': ['hr','hr_contract', 'hr_payroll','alshrooq_employee_details','hr_payroll_customize'],
    'data': [
        'data/sequence.xml',
        'security/hr_security_menuitem.xml',
        'data/data.xml',
        'views/model_view.xml',
        'report/over_time_report.xml',
        # 'views/hr_contract_view.xml',
        'wizard/batch_overtime.xml',
        'security/ir.model.access.csv',
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}