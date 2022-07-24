{

    'name': 'VISA Request (Reentry)',
    'version': '15.0.0.1',
    'summary': 'VISA Request (Reentry)',
    'description': 'VISA Request (Reentry):',
    'category': 'hr',
    'author': 'Mostafa Mahmoud, Pioneer Solution',
    'website': 'ps-sa.net',
    'depends': ['base', 'hr','hr_contract','alshrooq_employee_details','alshrooq_employee_contract','hr_payroll_customize','pioneer_HR_Leave','project'],
    'data': [
        'views/hr_leave_view.xml',
        'views/visa_request_view.xml',
        'report/visa_request_report.xml',
        'security/ir.model.access.csv',
        'data/data.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}