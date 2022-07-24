{
    'name': 'Alshrooq Contract Details',
    'version': '13.0.1.0.0',
    'category': 'Contacts',
    'summary': 'Contract Details for Employee, Customer',
    'description': """
        Contract Details
        
    """,
    'sequence': 1,
    'author': 'Arunagiri/pioneer solutions',
    'website': 'http://ps-sa.net/',
    'depends': ['base', 'hr', 'hr_contract', 'hr_payroll', 'hr_payroll_customize'],
    'data': [
        'views/inherited_hr_views.xml',
        'data/data.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3'
}
