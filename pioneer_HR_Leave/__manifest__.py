# -*- coding: utf-8 -*-

{
    'name': 'pioneer Leave Management',
    'version': '15.0',
    'author': "Arun, Pioneer Solution",
    'category': 'Human Resources',
    'sequence': 28,
    'summary': 'Holidays, Allocation and Leave Requests According To Saudi Rules',
    'website': 'http://www.ps-sa.net',
    'depends': ['base','hr',  'hr_contract','hr_payroll_customize', 'hr_holidays', 'calendar', 'resource'
        , 'hr_overtime_ps','hr_loan_advance', 'account', 'ps_mail_bot', 'alshrooq_employee_details'],
    'data': [
        'security/security.xml',
        'data/data.xml',
        'views/menu_view.xml',
        'views/hr_view.xml',
        'views/config_view.xml',
        'views/hr_holidays_saudi_view.xml',
        'views/time_off_view.xml',
        'wizard/update_used_vacation_view.xml',
        'security/ir.model.access.csv',
        'security/ps_security_rules.xml',
        'security/ps_hl_security_menu.xml',
        'report/report.xml',
        'report/report_hr_holidays_saudi.xml',
        'views/hr_res_config.xml',
        'security/ps_hl_security_menu.xml'
        ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}