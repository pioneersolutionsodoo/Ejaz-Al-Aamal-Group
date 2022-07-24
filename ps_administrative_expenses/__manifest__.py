{
    'name': 'Administrative Expenses',
    'version': '15.0.0.1',
    'summary': 'Administrative Expenses',
    'description': 'Administrative Expenses'
                   'Only HR Manager Can Create/Edit  Employee Memo and Approve',
    'category': 'hr',
    'author': 'Mostafa Abbas ,Pioneer solution',
    'website': 'ps-sa.net',
    'depends': ['base', 'hr','account','hr_payroll','hr_payroll_customize','alshrooq_employee_details'],
    'data': [
        'views/administrative_expenses_view.xml',
        'data/data.xml',
        'security/ir.model.access.csv',
        'report/administrative_expenses_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
