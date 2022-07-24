{
    'name': 'Manpower Requisition',
    'version': '15.0.1',
    'summary': 'Manpower Requisition',
    'description': 'This module manages Manpower Requisition',
    'category': 'hr',
    'author': 'Hossam Zaki | Pioneer Solutions',
    'depends': ['base', 'hr', 'ps_mail_bot'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/manpower_request.xml',
        'reports/report.xml',

    ],
    'demo': [],
    'sequence': 0,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
