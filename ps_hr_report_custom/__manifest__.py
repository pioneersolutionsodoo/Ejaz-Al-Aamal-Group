{
    'name': 'Pioneer HR Reports',
    'version': '15.0.1',
    'summary': 'Pioneer HR Reports',
    'description': 'Pioneer HR Reports',
    'category': 'hr',
    'author': 'Pioneer Solutions | Hossam Galal',
    'website': 'https://ps-sa.net',
    'depends': ['hr', 'pioneer_employee_memo'],
    'data': [
        'security/ir.model.access.csv',
        'report/employee_definistion.xml',
        'report/job_offer.xml',
        'report/emp_def_report.xml',
    ],
    'installable': True,
    'auto_install': False
}
