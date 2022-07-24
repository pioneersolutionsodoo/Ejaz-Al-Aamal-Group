# -*- coding: utf-8 -*-
{
    'name': 'Alshrooq Employee Details',
    'category': 'Product',
    'sequence': 21,
    'depends': ['base', 'account', 'hr', 'project', 'hr_skills', 'hr_loan_advance'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_group.xml',
        'views/inherited_hr_views.xml',
        'views/menu_view.xml',
        'report/print_badge_report.xml',
        'data/emp_ir_sequence.xml',
        'data/ir_sequence_data.xml',
        'data/data.xml',
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
