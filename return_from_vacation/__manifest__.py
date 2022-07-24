{
    'name': 'Return From Vacation',
    'version': '15.0.0.1',
    'summary': 'Return From Vacation',
    'description': 'Return From Vacation - Vacation Management',
    'category': 'hr',
    'author': 'Mostafa Mahmoud',
    'website': 'ps-sa.net',
    'depends': ['base', 'hr', 'alshrooq_employee_details', 'pioneer_HR_Leave', 'project'],
    'data': [
        'views/return_from_vacation_view.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'report/return_from_vacation_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
