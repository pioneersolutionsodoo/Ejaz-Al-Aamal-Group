{
    'name': 'HR EOSB Report',
    'description': 'HR EOSB Report For employee',
    'category': 'hr',
    'author': 'Pioneer,Hossam Galal',
    'website': 'ps-sa.net',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee.xml',
        'wizards/wizard_view.xml',
        'wizards/report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
