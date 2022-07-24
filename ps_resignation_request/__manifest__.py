{
    'name': 'Employee Resignation Request',
    'version': '15.0.1',
    'summary': 'Employee Resignation Request',
    'description': 'Employee Resignation Request',
    'category': 'hr',
    'author': 'Hossam Zaki | Pioneer Solutions',
    'depends': ['base',
                'hr',
                'hr_contract',
                'alshrooq_employee_details',
                'ps_mail_bot',
                ],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/resignation_request.xml',

    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
