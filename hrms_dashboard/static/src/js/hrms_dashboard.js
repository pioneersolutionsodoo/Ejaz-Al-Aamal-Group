odoo.define('hrms_dashboard.DashboardRewrite', function (require) {
    "use strict";

    const ActionMenus = require('web.ActionMenus');
    const ComparisonMenu = require('web.ComparisonMenu');
    const ActionModel = require("web.ActionModel");
    const FavoriteMenu = require('web.FavoriteMenu');
    const FilterMenu = require('web.FilterMenu');
    const GroupByMenu = require('web.GroupByMenu');
    // const patchMixin = require('web.patchMixin');
    const Pager = require('web.Pager');
    const SearchBar = require('web.SearchBar');
    const {useModel} = require('web.Model');

    const { Component, hooks } = owl;

    var concurrency = require('web.concurrency');
    var config = require('web.config');
    var field_utils = require('web.field_utils');
    var time = require('web.time');
    var utils = require('web.utils');
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var Dialog = require('web.Dialog');
    var field_utils = require('web.field_utils');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var web_client = require('web.web_client');
    var abstractView = require('web.AbstractView');
    var _t = core._t;
    var QWeb = core.qweb;

    const {useRef, useSubEnv} = hooks;


    var HrDashboard = AbstractAction.extend({

        template: 'HrDashboardMain',
        cssLibs: [
            '/hrms_dashboard/static/src/css/lib/nv.d3.css'
        ],
        jsLibs: [
            '/hrms_dashboard/static/src/js/lib/d3.min.js'
        ],

        events: {
            'click .hr_payslip': 'hr_payslip',
            'click .hr_leave_request_approve': 'leaves_to_approve',
            'click .hr_overtime_request': 'overtime_request',
            'click .hr_vacation': 'vacation_request',
            'click .hr_loan': 'loan_request',
            'click .hr_air_tiket': 'at_request',
            'click .hr_bt_request': 'bt_request',
            'click .hr_performance_evaluation': 'performance_ref_req',
            'click .hr_expenses': 'expenses_req',
            'click .hr_advance': 'advance_request',
            'click .hr_leave_allocations_approve': 'leave_allocations_to_approve',
            'click .leaves_request_today': 'leaves_request_today',
            'click .leaves_request_month': 'leaves_request_month',
            'click .hr_contract': 'hr_contract',
            'click .hr_timesheets': 'hr_timesheets',
            'click .login_broad_factor': 'employee_broad_factor',
            "click .o_hr_attendance_sign_in_out_icon": function () {
                this.$('.o_hr_attendance_sign_in_out_icon').attr("disabled", "disabled");
                this.update_attendance();
            },
            'click #broad_factor_pdf': 'generate_broad_factor_report',


        },


        init: function (parent, context) {

            this._super(parent, context);
            this.date_range = 'week';  // possible values : 'week', 'month', year'
            this.date_from = moment().subtract(1, 'week');
            this.date_to = moment();
            this.dashboards_templates = ['LoginEmployeeDetails', 'ManagerDashboard', 'EmployeeDashboard'];
            this.employee_birthday = [];
            this.upcoming_events = [];
            this.announcements = [];
            this.login_employee = [];

        },

        willStart: function () {
            var self = this;
            this.login_employee = {};
            return this._super()
                .then(function () {
                    var def0 = self._rpc({
                        model: 'hr.employee',
                        method: 'check_user_group'
                    }).then(function (result) {
                        if (result == true) {
                            self.is_manager = true;
                        } else {
                            self.is_manager = false;
                        }
                    });
                    var def1 = self._rpc({
                        model: 'hr.employee',
                        method: 'get_user_employee_details'
                    }).then(function (result) {
                        self.login_employee = result[0];
                    });
                    var def2 = self._rpc({
                        model: "hr.employee",
                        method: "get_upcoming",
                    })
                        .then(function (res) {
                            self.employee_birthday = res['birthday'];
                            self.upcoming_events = res['event'];
                            self.announcements = res['announcement'];
                        });
                    return $.when(def0, def1, def2);
                });
        },


        start: function () {
            console.log("START FUNCTION")
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function () {
                self.update_cp();
                self.render_dashboards();
                /*self.render_graphs();*/
                self.$el.parent().addClass('oe_background_grey');
            });
        },

        fetch_data: function () {
            var self = this;
            var def0 = self._rpc({
                model: 'hr.employee',
                method: 'check_user_group'
            }).then(function (result) {
                if (result == true) {
                    self.is_manager = true;
                } else {
                    self.is_manager = false;
                }
            });
            var def1 = this._rpc({
                model: 'hr.employee',
                method: 'get_user_employee_details'
            }).then(function (result) {
                self.login_employee = result[0];
            });
            var def2 = self._rpc({
                model: "hr.employee",
                method: "get_upcoming",
            })
                .then(function (res) {
                    self.employee_birthday = res['birthday'];
                    self.upcoming_events = res['event'];
                    self.announcements = res['announcement'];
                });
            return $.when(def0, def1, def2);
        },


        render_dashboards: function () {
            var self = this;
            if (this.login_employee) {
                var templates = []
                if (true) {
                    templates = ['LoginEmployeeDetails', 'ManagerDashboard', 'EmployeeDashboard'];
                } else {
                    templates = ['LoginEmployeeDetails', 'EmployeeDashboard'];
                }
                _.each(templates, function (template) {
                    self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}));
                });
            } else {
                self.$('.o_hr_dashboard').append(QWeb.render('EmployeeWarning', {widget: self}));
            }
        },

        /*render_graphs: function () {
            console.log("RENDER_GRAPHS")
            var self = this;
            if (this.login_employee) {
                /!*self.render_department_employee();
                self.render_leave_graph();
                self.update_join_resign_trends();
                self.update_monthly_attrition();
                self.update_leave_trend();*!/
            }
        },*/

        on_reverse_breadcrumb: function () {
            console.log("ON_REVERSE_BREADCRUMB")
            var self = this;
            web_client.do_push_state({});
            this.update_cp();
            this.fetch_data().then(function () {
                self.$('.o_hr_dashboard').empty();
                self.render_dashboards();
                self.render_graphs();
            });
        },

        update_cp: function () {
            var self = this;
        },

        get_emp_image_url: function (employee) {
            return window.location.origin + '/web/image?model=hr.employee&field=image_1920&id=' + employee;
        },

        update_attendance: function () {
            var self = this;
            this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.login_employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
            })
                .then(function (result) {
                    var attendance_state = self.login_employee.attendance_state;
                    var message = ''
                    var action_client = {
                        type: "ir.actions.client",
                        name: _t('Dashboard '),
                        tag: 'hr_dashboard',
                    };
                    self.do_action(action_client, {clear_breadcrumbs: true});
                    if (attendance_state == 'checked_in') {
                        message = 'Checked Out'
                    } else if (attendance_state == 'checked_out') {
                        message = 'Checked In'
                    }
                    self.trigger_up('show_effect', {
                        message: _t("Successfully " + message),
                        type: 'rainbow_man'
                    });
                });

        },

        //events

        hr_payslip: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);
            /*hr_payroll.group_hr_payroll_user*/
            /*session.user_has_group('hr_payroll.group_hr_payroll_user').then(function (has_group) {
                if (has_group) {*/
            console.log('entered function hr payslip')

            var options = {
                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
            };

            self.do_action({
                name: _t("Employee Payslips"),
                type: 'ir.actions.act_window',
                res_model: 'hr.payslip',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'], [false, 'form']],
                domain: [['employee_id', '=', self.login_employee.id]],
                target: 'current' //self on some of them
            }, {
                on_reverse_breadcrumb: self.on_reverse_breadcrumb
            });
            /* }
         });*/
        },

        leaves_to_approve: function (e) {
            console.log("leaves_to_approve")
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Leave Request"),
                type: 'ir.actions.act_window',
                res_model: 'hr.leave',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id]],
                target: 'current'
            }, options)
        },

        overtime_request: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Overtime Request"),
                type: 'ir.actions.act_window',
                res_model: 'hr.overtime.ps',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id]],
                target: 'current'
            }, options)
        },

        vacation_request: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Vacation Resettlement Request"),
                type: 'ir.actions.act_window',
                res_model: 'vacation.resettlement',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id]],
                target: 'current'
            }, options)
        },

        loan_request: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Loan"),
                type: 'ir.actions.act_window',
                res_model: 'hr.employee.loan.ps',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id]],
                target: 'current'
            }, options)
        },

        advance_request: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Advance"),
                type: 'ir.actions.act_window',
                res_model: 'hr.employee.advance.ps',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id]],
                target: 'current'
            }, options)
        },
        at_request: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Air Ticket"),
                type: 'ir.actions.act_window',
                res_model: 'air.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id]],
                target: 'current'
            }, options)
        },
        bt_request: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Business Trip"),
                type: 'ir.actions.act_window',
                res_model: 'hr.business.trip',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id]],
                target: 'current'
            }, options)
        },

        performance_ref_req: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Performance Evaluation"),
                type: 'ir.actions.act_window',
                res_model: 'hr.performance.evaluation',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id]],
                target: 'current'
            }, options)
        },

        expenses_req: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Expenses"),
                type: 'ir.actions.act_window',
                res_model: 'hr.expense',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id]],
                target: 'current'
            }, options)
        },

        //employee broad factor

        employee_broad_factor: function (e) {
            console.log("broad_factor")
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            var today = new Date();
            var dd = String(today.getDate()).padStart(2, '0');
            var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
            var yyyy = today.getFullYear();

            today = mm + '/' + dd + '/' + yyyy;
            console.log(this, "loploploplop");
            this.do_action({
                name: _t("Leave Request"),
                type: 'ir.actions.act_window',
                res_model: 'hr.leave',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id], ['date_to', '<=', today]],
                target: 'current',
                context: {'order': 'duration_display'}
            }, options)
        },

        //hr timesheets

        hr_timesheets: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            /*hr_payroll.group_hr_payroll_user*/
            /*
                        session.user_has_group('hr_timesheet.group_hr_timesheet_user').then(function (has_group) {
                            if (has_group) {
            */

            var options = {
                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
            };
            self.do_action({
                name: _t("Timesheets"),
                type: 'ir.actions.act_window',
                res_model: 'account.analytic.line',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                context: {
                    'search_default_month': true,
                },
                domain: [['employee_id', '=', self.login_employee.id]],
                target: 'current'
            }, options)

            /* }
         });*/
        },

        //Contracts

        hr_contract: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            /*session.user_has_group('hr_contract.group_hr_contract_manager').then(function (has_group) {
                if (has_group) {*/
            var options = {
                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
            };
            self.do_action({
                name: _t("Contracts"),
                type: 'ir.actions.act_window',
                res_model: 'hr.contract',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'], [false, 'form']],
                context: {
                    'search_default_employee_id': self.login_employee.id,
                },
                target: 'current'
            })
            /* }
         });*/

        },

        //leave request today
        leaves_request_today: function (e) {
            var self = this;
            var date = new Date();
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Leaves Today"),
                type: 'ir.actions.act_window',
                res_model: 'hr.leave',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id], ['date_from', '<=', date], ['date_to', '>=', date]],
                target: 'current'
            }, options)
        },

        //leave requests this month

        leaves_request_month: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            var date = new Date();
            var firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
            var lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
            var fday = firstDay.toJSON().slice(0, 10).replace(/-/g, '-');
            var lday = lastDay.toJSON().slice(0, 10).replace(/-/g, '-');
            this.do_action({
                name: _t("This Month Leaves"),
                type: 'ir.actions.act_window',
                res_model: 'hr.leave',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id], ['date_from', '>', fday], ['date_from', '<', lday]],
                target: 'current'
            }, options)
        },

        leave_allocations_to_approve: function (e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Employee Memo Request"),
                type: 'ir.actions.act_window',
                res_model: 'employee.memo',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['employee_id', '=', this.login_employee.id]],
                target: 'current'
            }, options)
        },
    });
    core.action_registry.add('hr_dashboard', HrDashboard);

    return HrDashboard;
});

