# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Aswani PC (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': "Open HRMS - HR Dashboard",
    'version': '14.0.1.0.3',
    'summary': """Open HRMS - HR Dashboard""",
    'description': """Open HRMS - HR Dashboard""",
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Techno solutions,Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': ['hr', 'hr_holidays', 'hr_timesheet', 'hr_payroll', 'hr_attendance', 'hr_timesheet_attendance',
                'event', 'base', 'hr_reward_warning', 'hr_loan_advance', 'hr_performance_ps', 'pioneer_Business_Trip',
                'pioneer_employee_memo', 'hr_expense', 'hr_overtime_ps', 'vacation_resettlement', 'air_ticket'],
    #    'external_dependencies': {
    #       'python': ['pandas'],
    #  },
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/broadfactor.xml',
        'views/dashboard_views.xml',
    ],
    'qweb': ["static/src/xml/hrms_dashboard.xml"],
    'images': ["static/description/banner.gif"],
    'assets': {
        'web.assets_backend': [

            'hrms_dashboard/static/src/css/hrms_dashboard.css',
            'hrms_dashboard/static/src/css/lib/nv.d3.css',
            'hrms_dashboard/static/src/js/hrms_dashboard.js',
            'hrms_dashboard/static/src/js/lib/d3.min.js',

        ],
        'web.assets_qweb': [
            'hrms_dashboard/static/src/xml/hrms_dashboard.xml',
        ],
    },

    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
