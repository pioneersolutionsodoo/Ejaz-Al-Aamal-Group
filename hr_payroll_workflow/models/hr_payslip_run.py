# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[('wait_ceo', 'Waiting For CEO Approval'),
                                            ('wait_fm', 'Waiting For FM Approval'),
                                            ('wait_gm', 'Waiting For GM Approval'),
                                            ('close', )],
                             ondelete={'wait_ceo': lambda recs: recs.write({'state': 'verify'}),
                                       'wait_fm': lambda recs: recs.write({'state': 'verify'}),
                                       'wait_gm': lambda recs: recs.write({'state': 'verify'})},
                             )

    def action_wait_ceo(self):
        self.write({'state': 'wait_ceo'})
        self._notify_group_user(group='hr_payroll_workflow.group_ceo', approval='CEO')

    def action_wait_fm(self):
        self.write({'state': 'wait_fm'})
        self._notify_group_user(group='hr_payroll_workflow.group_fm', approval='FM')

    def action_wait_gm(self):
        self.write({'state': 'wait_gm'})
        self._notify_group_user(group='hr_payroll_workflow.group_gm', approval='GM')

    def _get_mail_from(self):
        return self.env['res.users'].sudo().browse(SUPERUSER_ID).email

    def _prepare_mail_body(self, approval=''):
        body = "<p>Hello,</p>"
        body += f"<p>A new Payslip Batches <b>{self.name}</b> waiting for {approval} approval.</p>"
        body += "<p>Please take necessary action.</p>"
        return body

    def _notify_group_user(self, group, approval=''):
        email_from = self._get_mail_from()
        users = self.env.ref(group).users
        mails_to = ','.join(users.mapped('email'))
        subject = "Payslip Batch Approval"
        body = self._prepare_mail_body(approval)
        self.send_email(email_from, mails_to, subject, body)
        self.send_notification("Payslip Batch", self._name, self.id, self.name, group)

    def send_notification(self, description, model, res_id, res_name, group_name):
        mail_channel = self.env['mail.channel']
        mail_channel.sudo().send_message_without_refresh(description, model, res_id, res_name, group_name)

    def send_email(self, email_from, email_to, subject, body):
        mail_mail = self.env['mail.mail']
        mail_id = mail_mail.sudo().create({'email_from': email_from,
                                           'email_to': email_to,
                                           'subject': subject,
                                           'body_html': body})
        mail_id.send()
        return True
