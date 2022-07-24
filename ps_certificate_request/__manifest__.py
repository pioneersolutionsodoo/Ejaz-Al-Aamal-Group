{
    'name': 'Employee Certificate Request',
    'version': '15.0.1',
    'summary': 'Employee Certificate Request',
    'description': 'Employee Certificate Request',
    'category': 'hr',
    'author': 'Hossam Zaki | Pioneer Solutions',
    'depends': ['base', 'alshrooq_employee_details', 'ps_mail_bot'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/certificate_request.xml',
        'views/certificate_purpose.xml',

    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
