# -*- coding: utf-8 -*-
{
    'name': 'Pioneer Solutions-Business Trip',
    'version': '15.1.0.0',
    'description': """  Business Trip Module In HR""",
    'author': 'Arun, Pioneer Solutions.',
    'depends': ['base', 'alshrooq_employee_details','account'],
    'data': [
        'data/ps_bt_sequence.xml',
        'views/ps_bt_res_company.xml',
        'views/ps_bt_business_trip_view.xml',
        'views/ps_bt_config_view.xml',
        'views/ps_bt_report_view.xml',
        'report/ps_bt_report.xml',
        'report/ps_bt_report_business_trip.xml',
        'security/ps_bt_security_groups.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
    'installable': True,
}
