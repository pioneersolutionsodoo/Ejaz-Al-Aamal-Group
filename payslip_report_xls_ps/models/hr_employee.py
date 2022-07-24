# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    gosi_number = fields.Char('Gosi Number', groups="hr.group_hr_user")

    # Relational Fields
    work_locations_id = fields.Many2one('work.location.name', store=True, groups="hr.group_hr_user")

    def get_work_location(self):
        employees = self.env['hr.employee'].search([('work_locations_id', '=', False)])
        if employees:

            for employee in employees:
                if employee.work_location:
                    locations = self.env['work.location.name'].search([])
                    if locations:
                        flag = False
                        for location in locations:
                            if location.name == employee.work_location:
                                employee.work_locations_id = location.id
                                flag = True
                        if not flag:
                            location = self.env['work.location.name'].create({'name': employee.work_location})
                            employee.work_locations_id = location.id
                    else:
                        location = self.env['work.location.name'].create({'name': employee.work_location})
                        employee.work_locations_id = location.id

    # @api.model
    # def create(self, values):
    #     model = super(HrEmployee, self).create(values)
    #     locations = self.env['work.location.name'].search([])
    #     if values['work_location']:
    #         if locations:
    #             flag = False
    #             for location in locations:
    #                 if location.name == values['work_location']:
    #                     values['work_locations_id'] = location.id
    #                     flag = True
    #             if not flag:
    #                 location = self.env['work.location.name'].create({'name': values['work_location']})
    #                 model.work_locations_id = location.id
    #         else:
    #             location = self.env['work.location.name'].create({'name': values['work_location']})
    #             model.work_locations_id = location.id
    #     return model


class WorkLocation(models.Model):
    _name = 'work.location.name'
    _rec_name = 'name'
    _description = 'Work Location'

    name = fields.Char(required=True)
