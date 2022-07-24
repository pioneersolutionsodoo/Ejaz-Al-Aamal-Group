{
    'name': 'Air Ticket',
    'version': '13.0.0.1',
    'summary': 'Air Ticket',
    'description': 'Air Ticket - Vacation Management',
    'category': 'hr',
    'author': 'Mostafa Mahmoud',
    'website': 'ps-sa.net',
    'depends': ['base', 'hr', 'hr_attendance', 'account','alshrooq_employee_details','hr_contract','hr_loan_advance','hr_payroll','pioneer_HR_Leave','ps_mail_bot'],
    'data': [
        'views/air_ticket_view.xml',
        'views/hr_leave_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_payroll_view.xml',
        'report/air_ticket_report.xml',
        'security/ir.model.access.csv',
        'data/data.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    
    
}
