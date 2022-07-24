# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.translate import _
from lxml import etree
# from odoo.osv.orm import setup_modifiers
from odoo.exceptions import AccessError, UserError, ValidationError


# class HrEmployee(models.Model):
#     _name = 'hr.employee'
#     _inherit = 'hr.employee'
#
#     namea = fields.Char(string='Name in Arabic')
#     emp_code = fields.Char(string='Employee Code', required=True)


# SDL Education
class hr_performance_evaluation(models.Model):
    _name = 'hr.performance.evaluation'
    _description = 'Performance Evaluation'
    _inherit = ['mail.thread', 'resource.mixin']
    _rec_name = "employee_id"

    def _get_current_user(self):
        self.current_user = False
        self.is_direct_manager = False
        if (self.employee_id and self.employee_id.parent_id and self.employee_id.parent_id.user_id) and self.employee_id.parent_id.user_id.id == self.env.uid:
            self.is_direct_manager = True
        if (self.employee_id and self.employee_id.user_id) and self.employee_id.user_id.id == self.env.uid:
            self.current_user = True


    def _get_answer_values(self):
        return [(str(int(r)).zfill(2), str(int(r))) for r in range(0,11)]

    @api.depends('pe_technique', 'pe_quality','pe_quantity','pe_implementation','pe_completition','pe_team','pe_desire','pe_professional','pe_pressure','pe_adapt','pe_reporting','pe_honesty','pe_assets','pe_relationship','pe_punctuality','pe_appearance')
    def _get_pe_percentage(self):
        count = 0
        percentage = 0
        for case in self:

            percentage = float(int(case.pe_technique))+ float(int(case.pe_quality))+ float(int(case.pe_quantity))+ float(int(case.pe_implementation))+ float(int(case.pe_completition)) \
                        + float(int(case.pe_team))+ float(int(case.pe_desire))+ float(int(case.pe_professional))+ float(int(case.pe_pressure)) \
                        + float(int(case.pe_adapt))+ float(int(case.pe_reporting))+ float(int(case.pe_honesty))+ float(int(case.pe_assets)) \
                        + float(int(case.pe_relationship))+ float(int(case.pe_punctuality))+ float(int(case.pe_appearance))
            percentage = (percentage/160)*100
            case.pe_percentage = percentage

    @api.depends('pe_percentage')
    def calculate_performace(self):
        for case in self:
            st = 'Bad' if case.pe_percentage <=30 else 'Good' if (case.pe_percentage >30 and case.pe_percentage <75) else 'Very Good' if (case.pe_percentage >75 and case.pe_percentage<100) else 'Excellent'
            case.performance = 'Your Performance is ' + st

    def show_button_details(self):
        for case in self:
            user = self.env.user
            is_group_hr_manager = user.has_group('hr.group_hr_manager')
            is_group_hr_general_manager = user.has_group('hr_performance_ps.group_hr_general_manager_11')

            is_show_request_button = False
            is_show_dm_button = False
            is_show_gm_button = False
            state = case.state
            if state in ('draft', 'waiting_dm_approval'):
                if case.is_direct_manager:
                    is_show_dm_button = True
            if state == 'waiting_gm_approval':
                if is_group_hr_general_manager:
                    is_show_gm_button = True
            if state == 'draft':
                if is_group_hr_manager:
                    is_show_request_button = True
            case.is_show_request_button = is_show_request_button
            case.is_show_dm_button = is_show_dm_button
            case.is_show_gm_button = is_show_gm_button

    employee_id  = fields.Many2one('hr.employee', 'Employee')
    pe_technique   = fields.Selection(selection="_get_answer_values", string='Comprehension of work techniques')
    pe_quality   = fields.Selection(selection="_get_answer_values", string='Quality of work accomplished')
    pe_quantity   = fields.Selection(selection="_get_answer_values", string='Quantity of work accomplished')
    pe_implementation   = fields.Selection(selection="_get_answer_values", string='Implementation level of Instruction')
    pe_completition   = fields.Selection(selection="_get_answer_values", string='Completion of work within normal working hours')
    pe_team   = fields.Selection(selection="_get_answer_values", string='Team work attitude')
    pe_desire   = fields.Selection(selection="_get_answer_values", string='Desire to develop oneself')
    pe_professional   = fields.Selection(selection="_get_answer_values", string='Professional development')
    pe_pressure   = fields.Selection(selection="_get_answer_values", string='Performance under pressure')
    pe_adapt   = fields.Selection(selection="_get_answer_values", string='Adapts to changes and improvements in work techniques')
    pe_reporting   = fields.Selection(selection="_get_answer_values", string='Reports information to superiors clearly and concisely')
    pe_honesty   = fields.Selection(selection="_get_answer_values", string='Honesty, confidentiality')
    pe_assets   = fields.Selection(selection="_get_answer_values", string='Safeguarding assets of institution')
    pe_relationship  = fields.Selection(selection="_get_answer_values", string='Colleagues Relationship')
    pe_punctuality   = fields.Selection(selection="_get_answer_values", string='Discipline & punctuality of work')
    pe_appearance   = fields.Selection(selection="_get_answer_values", string='General appearance')
    pe_percentage   = fields.Float(compute="_get_pe_percentage", string='Percentage')

    direct_manager_id = fields.Many2one('res.users', string='Direct Manager', readonly=True)
    direct_manager_date = fields.Datetime(string='Confirmed Date', readonly=True)
    direct_manager_note = fields.Text(string='Comments', readonly=True, states={'waiting_dm_approval': [('readonly', False)]})
    gm_manager_id = fields.Many2one('res.users', string='GM Manager', readonly=True)
    gm_manager_date = fields.Datetime(string='Confirmed Date', readonly=True)
    gm_manager_note = fields.Text(string='Comments', readonly=True, states={'approve': [('readonly', False)]})
    is_direct_manager = fields.Boolean(string='Is Direct Manager', readonly=True, compute='_get_current_user')
    current_user = fields.Boolean(string='Current User', readonly=True, compute='_get_current_user')
    performance = fields.Char(compute="calculate_performace")
    is_show_dm_button = fields.Boolean(compute='show_button_details')
    is_show_gm_button = fields.Boolean(compute='show_button_details')
    is_show_request_button = fields.Boolean(compute='show_button_details')
    state = fields.Selection([
	('draft', 'Draft'),
	('waiting_dm_approval', 'Waiting for DM Approval'),
	('waiting_gm_approval', 'Waiting for GM Approval'),
	('approve', 'Approved'),
	('refuse', 'Refused'),

	], string='Status', readonly=True, track_visibility='onchange', default='draft')


    def button_print_performance_evaluation(self):
        self.ensure_one()
        return self.env.ref('hr_performance_ps.hr_event_certificate_report').report_action(self)

    # @api.depends('name', 'type')
    # def name_get(self):
    #     result = []
    #     for case in self:
    #         name = case.name + (case.type and (' ['))+ float(int(case.type.title() + ']') or '')
    #         result.append((case.id, name))
    #     return result

    def button_hrm_request(self):
        for case in self:
            user = self.env.user
            is_direct_manger = case.is_direct_manager
            is_group_hr_manager = user.has_group('hr.group_hr_manager')
            is_group_hr_general_manager = user.has_group('hr_performance_ps.group_hr_general_manager_11')
            if not is_group_hr_manager:
                msg = 'Only HR Manager has privilege to raise request.'
                raise UserError(_(msg))
            return self.write({'state': 'waiting_dm_approval'})

    def button_dm_approve(self):
        for case in self:
            user = self.env.user
            is_direct_manger = case.is_direct_manager
            is_group_hr_manager = user.has_group('hr.group_hr_manager')
            is_group_hr_general_manager = user.has_group('hr_performance_ps.group_hr_general_manager_11')
            if not is_direct_manger:
                msg = 'Only Direct Manager has privilege to approve this request.'
                raise UserError(_(msg))
            return self.write({'state': 'waiting_gm_approval'
                                  , 'direct_manager_id': self.env.uid
                                  , 'direct_manager_date':fields.date.today()})

    def button_gm_approve(self):
        contr_obj = self.env['hr.contract']
        for case in self:
            user = self.env.user
            is_direct_manger = case.is_direct_manager
            is_group_hr_manager = user.has_group('hr.group_hr_manager')
            is_group_hr_general_manager = user.has_group('hr_performance_ps.group_hr_general_manager_11')
            if not is_group_hr_general_manager:
                msg = 'Only general Manager has privilege to approve this request.'
                raise UserError(_(msg))
            if case.pe_percentage >= 60.0:
                ct_id = contr_obj.search([('employee_id','=',case.employee_id.id)])
                # bonus = ct_id.wage and (ct_id.wage * case.pe_percentage) / 100.0 + ct_id.wage or 0.0
                # ct_id.basic_bonus = bonus
            return self.write({'state': 'approve'
                              , 'gm_manager_id': self.env.uid
                              , 'gm_manager_date':fields.date.today()})

    # def action_fm_approve(self):
    #     return self.write({'state': 'approve', 'account_manager_id': self.env.uid, 'account_manager_date':fields.date.today()})

    def action_refuse(self):
        for case in self:
            user = self.env.user
            is_direct_manger = case.is_direct_manager
            is_group_hr_manager = user.has_group('hr.group_hr_manager')
            is_group_hr_general_manager = user.has_group('hr_performance_ps.group_hr_general_manager_11')
            if is_group_hr_manager and not is_group_hr_general_manager :
                msg = 'HR Manager do not have the privilege to refuse this request.'
                raise UserError(_(msg))
            return self.write({'state': 'refuse'})