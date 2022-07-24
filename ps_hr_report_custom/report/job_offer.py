from odoo import fields, models, api


class JobOffer(models.Model):
    _name = 'job.offer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Job Offer Rec'

    name = fields.Char(string="Applicant")
    job_id = fields.Many2one(comodel_name='hr.job', string='Job')
    degree = fields.Char(string="Degree")
    contract_duration = fields.Char(string="Contract Duration")
    date = fields.Date(string='Date', default=lambda self: fields.Date.today())
    housing_allowance = fields.Float(string='Housing Allowance', default="0.0")
    transportation_allowance = fields.Float(string='Transportation Allowance', default="0.0")
    bias_salary = fields.Float(string='Bias Salary', default="0.0")


class ResignationAcceptance(models.Model):
    _name = 'resignation.acceptance'
    _rec_name = "employee_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Resignation acceptance Rec'

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    date = fields.Date(string='Date', default=lambda self: fields.Date.today())
    department_id = fields.Many2one(comodel_name='hr.department', string='Department',
                                    related="employee_id.department_id")
    job_title = fields.Char(string='Job Title', related="employee_id.job_title")
    emp_code = fields.Char(string='Job Title', related="employee_id.emp_code")
    job_code = fields.Char(string='Job Title', related="employee_id.emp_code")
    total = fields.Float(string='Total Salary', related="employee_id.contract_id.total")
    qualification = fields.Char(string='Qualification')
    qualification_institution = fields.Char(string='Qualification Institution')
    qualification_date = fields.Date(string='Qualification Issue Date')
    aj_date = fields.Date(string='Date of Join', related="employee_id.aj_date")
    leave_date = fields.Date(string='Date of Resignation')
    reason = fields.Text(string="Reason")
    committee_note = fields.Text(string="Committee Note")
    recommendations = fields.Text(string="Recommendations")
    last_evaluation = fields.Char(string='Last Evaluation')
    evaluation_rate = fields.Char(string='Evaluation Rate')
    state = fields.Selection(
        string='State',
        selection=[('Draft', 'Draft'),
                   ('Confirmed', 'Confirmed'), ],
        default="Draft", )

    def confirm(self):
        self.write({'state': 'Confirmed'})


class EmployeeStatement(models.Model):
    _name = 'employee.statement'
    _rec_name = "employee_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Statement Rec'

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    date = fields.Date(string='Date', default=lambda self: fields.Date.today())
    department_id = fields.Many2one(comodel_name='hr.department', string='Department',
                                    related="employee_id.department_id")
    job_code = fields.Char(string='Job Title', related="employee_id.emp_code")
    department = fields.Char(string='Department')
    report = fields.Text(string='Please Report')
    emp_report = fields.Text(string='Employee Report')
    dir_manager_report = fields.Text(string='Direct Manager Report')
    state = fields.Selection(
        string='State',
        selection=[('Draft', 'Draft'),
                   ('Confirmed', 'Confirmed'), ],
        default="Draft", )

    def confirm(self):
        self.write({'state': 'Confirmed'})