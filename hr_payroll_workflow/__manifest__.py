# -*- coding: utf-8 -*-
{
    'name': 'Maena HR Payroll Workflow',
    'version': '15.0.1',
    'summary': 'CEO, FM, GM approvals in HR Payroll workflow (for Maena project)',
    'description': '',
    'category': 'hr',
    'author': 'Hossam Zaki, Pioneer Solutions',
    'depends': ['base',
                'hr_payroll',
                'ps_mail_bot',
                ],
    'data': [
        'security/groups.xml',
        'views/hr_payslip_run.xml',
        'views/hr_payslip.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
