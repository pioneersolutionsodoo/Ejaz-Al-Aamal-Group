# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import datetime
from datetime import datetime as dt
import time


# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # ~ def get_employee_code(self):
    # ~ for case in self:
    # ~ emp_code_sort = 0
    # ~ if case.emp_code:
    # ~ try:
    # ~ emp_code_sort = int(case.emp_code)
    # ~ except:
    # ~ emp_code_sort = 0
    # ~ case.emp_code_sort = emp_code_sort
    is_saudi = fields.Boolean('Is Saudi')
    is_deduct = fields.Selection([('yes', 'Yes'), ('no', 'No')])
    mobile = fields.Char(string='Mobile', groups="hr.group_hr_user")
    iqama_national_id = fields.Char('Iqama ID', groups="hr.group_hr_user")
    driving_license = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Driving License',
                                       groups="hr.group_hr_user")
    # ~ emp_code_sort = fields.Integer(string='Employee Code Used For Sorting', compute='get_employee_code', store=True)
    emp_code = fields.Char(string="Job Number", copy=False, groups="hr.group_hr_user")
    family_name = fields.Char('Name', groups="hr.group_hr_user")
    arabic_name = fields.Char('Arabic Name', groups="hr.group_hr_user")
    contract_type = fields.Selection([('employee', 'Employee'), ('worker', 'Worker')], 'Basic Contract Type',
                                     default="employee", groups="hr.group_hr_user")
    start_date = fields.Date('Start Date', groups="hr.group_hr_user")
    end_date = fields.Date('End Date', groups="hr.group_hr_user")
    aj_date = fields.Date(groups="hr.group_hr_user")
    contact_number = fields.Char('Contact Number', groups="hr.group_hr_user")
    date_of_birth = fields.Date('Date Of Birth', groups="hr.group_hr_user")
    relation_type = fields.Selection([('wife', 'Wife'), ('son', 'Son'), ('mother', 'Mother'), ('father', 'Father'),
                                      ('sister', 'Sister'), ('brother', 'brother'), ('other', 'Other')],
                                     string='Relation Type', groups="hr.group_hr_user")

    sponsor_name = fields.Char('Sponsor Name', groups="hr.group_hr_user")
    sponsor_number = fields.Char('Sponsor Number', groups="hr.group_hr_user")
    id_expiration_details = fields.Char('Id Expiration Details', groups="hr.group_hr_user")
    expiration_date_of_issue = fields.Date('Date Of Issue', groups="hr.group_hr_user")
    iqama_date_of_issue = fields.Date(groups="hr.group_hr_user")
    iqama_expiry_date = fields.Date(groups="hr.group_hr_user")
    expiration_date_of_expiry = fields.Date('Date Of Expiry', groups="hr.group_hr_user")
    place_of_issue = fields.Char('Place of Issue', groups="hr.group_hr_user")
    degree_course = fields.Char('Degree Course', groups="hr.group_hr_user")
    institution_name = fields.Char('University Name', groups="hr.group_hr_user")
    date_course = fields.Datetime('Year Of Course', groups="hr.group_hr_user")
    note = fields.Char('Note', groups="hr.group_hr_user")
    file = fields.Char('File', groups="hr.group_hr_user")
    status = fields.Char('Status', groups="hr.group_hr_user")
    sponsor = fields.Char('Sponsor', groups="hr.group_hr_user")

    # Relational Fields
    religion = fields.Many2one('religion', string='Religion', groups="hr.group_hr_user")
    mother_tongue = fields.Many2one('mother.tongue', 'Mother Tongue', groups="hr.group_hr_user")
    project_name = fields.Many2one('project.project', string='Project Name', groups="hr.group_hr_user")
    # contract_type = fields.Many2one('contract.type','Contract Type')
    duration = fields.Many2one('contract.duration', 'Duration', groups="hr.group_hr_user")
    expiration_type = fields.Many2one('expiration.type', 'Expiration Type', groups="hr.group_hr_user")
    contract_status = fields.Many2one('contract.status', 'Contract Status', groups="hr.group_hr_user")
    family_ids = fields.One2many('hr.family.details', 'employee_id', 'Family Details',
                                 help="This includeds IQAMA details", groups="hr.group_hr_user")

    _sql_constraints = [
        ('unique_job_code_emp', 'UNIQUE (emp_code)', 'Job Number must be Unique!'),
        ('unique_iiqama_national_id', 'UNIQUE (iqama_national_id)', 'Iqama NO. must be Unique!'),
    ]


    @api.onchange('is_deduct', 'is_saudi')
    def compute_employee_deduction(self):
        for employee in self:
            if employee.is_saudi:
                deduction = 9.75/100
                total = employee.contract_id.wage + employee.contract_id.housing_allowance
                if employee.is_deduct == 'yes':
                    employee.contract_id.gosi_deduction = deduction * total
                else:
                    employee.contract_id.gosi_deduction = 0.00
            else:
                employee.is_deduct = False

    @api.constrains('emp_code')
    def _check_emp_code_value(self):
        for record in self:
            employee = self.env['hr.employee'].search([('emp_code', '=', record.emp_code)])
            if len(employee)>1:
                raise ValidationError("Job Number must be Unique!")


    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            # if 'emp_code' not in val:
            #     val['emp_code'] = self.env['ir.sequence'].next_by_code('hr.employee') or 'New'
            # Create Partner and assign it to address_home_id
            if 'address_home_id' not in val:
                partner_id = self.env['res.partner'].create({
                    'name': val['name'],
                })
                val['address_home_id'] = partner_id.id
        res = super(HrEmployee, self).create(vals)
        return res

    @api.onchange('project_name')
    def _onchange_academic_year_id(self):
        if self.project_name:
            self.start_date = self.project_name.start_date
            self.end_date = self.project_name.end_date

    # ~ @api.depends('start_date','end_date')
    # ~ def _duration(self):
    # ~ if self.start_date and self.end_date:
    # ~ for rec in self:
    # ~ init_date = dt.strptime(str(rec.start_date), '%Y-%m-%d')
    # ~ end_date = dt.strptime(str(rec.end_date), '%Y-%m-%d')
    # ~ rec.duration= str((end_date - init_date).days)

    # ~ def name_get(self):
    # ~ result = []
    # ~ for case in self:
    # ~ name = case.name or ''
    # ~ code = case.emp_code or ''
    # ~ if code:
    # ~ name = '[' + code + '] ' + name
    # ~ result.append((case.id, "%s" % (name and name or '',)))
    # ~ return result

    # ~ @api.model
    # ~ def name_search(self, name, args=None, operator='ilike', limit=100):
    # ~ context = dict(self._context or {})
    # ~ args = args or []
    # ~ recs = self.browse()
    # ~ if name:
    # ~ recs = self.search([('name', '=', name)] + args, limit=limit)
    # ~ if not recs:
    # ~ domain = ['|','|',  ('name', operator, name+ '%'), ('emp_code', operator, name+ '%'), ('name_arabic', operator, name+ '%')]
    # ~ recs = self.search(domain + args, limit=limit)
    # ~ return recs.name_get()


class Religion(models.Model):
    _name = 'religion'
    _description = "Religion"

    name = fields.Char('Religion Name')


class ExpirationType(models.Model):
    _name = 'expiration.type'
    _description = "Expiration type"

    name = fields.Char('Type')


class MotherTongue(models.Model):
    _name = 'mother.tongue'
    _description = 'Mother Tongue'

    name = fields.Char('Language')


class ContractType(models.Model):
    _name = 'contract.type'
    _description = 'Contract Type'

    name = fields.Char('Name')


class ContractStatus(models.Model):
    _name = 'contract.status'
    _description = 'Contract Status'

    name = fields.Char('Name')


class ContractDuration(models.Model):
    _name = 'contract.duration'
    _description = 'Contract Duration'

    name = fields.Char('Name')
