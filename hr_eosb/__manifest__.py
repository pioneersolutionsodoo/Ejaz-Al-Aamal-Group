# -*- coding: utf-8 -*-
{
    'name': 'HR EOSB',
    'version': '15.0',
    'category': 'Human Resources',
    'description': "",
    'author': "Mani, Pioneer Solution",
    'migrated': 'Arun, Pioneer Solution',
    'depends': ['base', 'hr', 'hr_contract', 'alshrooq_employee_details', 'hr_loan_advance', 'account', 'contacts',
                'hr_payroll', 'hr_payroll_customize', 'ps_eosb_report'],
    'data': [
        'views/hr_view.xml',
        'views/hr_payroll_view.xml',
        'views/model_view.xml',
        'views/res_company.xml',
        'views/hr_contract_employee_report_view.xml',
        'report/report.xml',
        'report/report_eosb_eosb.xml',
        'data/sequence.xml',
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/ps_security_menuitem.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
