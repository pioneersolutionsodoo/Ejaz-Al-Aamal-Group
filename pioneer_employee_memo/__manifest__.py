{
    'name': 'Employee Memo',
    'version': '15.0.0.1',
    'summary': 'Employee Memo',
    'description': 'Employee Memo'
                   'Only HR Manager Can Create/Edit  Employee Memo and Approve',
    'category': 'hr',
    'author': 'Mostafa Abbas ,Pioneer solution',
    'website': 'ps-sa.net',
    'depends': ['base', 'hr','account','hr_contract','alshrooq_employee_details'],
    'data': [
        'report/employee_memo_report.xml',
        'views/employee_memo_view.xml',
        'data/data.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
