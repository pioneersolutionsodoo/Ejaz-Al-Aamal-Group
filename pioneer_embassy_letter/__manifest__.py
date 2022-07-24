{
    'name': 'Embassy Letter',
    'version': '15.0.0.1',
    'summary': 'Embassy Letter',
    'description': 'Embassy Letter',
    'category': 'hr',
    'author': 'Mostafa Abbas ,Pioneer solution',
    'website': 'ps-sa.net',
    'depends': ['base', 'hr','account','hr_contract','alshrooq_employee_details','alshrooq_employee_contract'],
    'data': [
        'report/embassy_letter_report.xml',
        'views/embassy_letter_view.xml',
        'data/data.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
