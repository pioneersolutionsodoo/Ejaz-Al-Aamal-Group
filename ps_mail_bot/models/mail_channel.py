# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _, fields
from odoo.exceptions import UserError


class Channel(models.Model):
    _inherit = 'mail.channel'

    # @api.model
    def send_message_without_refresh(self, description, model, res_id, res_name, group_name):
        if group_name == 'direct_manager':
            record = self.env[model].search([('id', '=', int(res_id))])
            if record:
                if record.employee_id:
                    if record.employee_id.parent_id:
                        if record.employee_id.parent_id.user_id:
                            user = record.employee_id.parent_id.user_id
                            self.call_channel_sender(user, description, model, res_id, res_name)
                        else:
                            raise UserError(_(
                                'Direct Manager "%s" has no related user to approve') % record.employee_id.parent_id.name)
        else:
            users = self.env['res.users'].search([])
            if users:
                for user in users:
                    if user.has_group(group_name):
                        self.call_channel_sender(user, description, model, res_id, res_name)

    def call_channel_sender(self, user, description, model, res_id, res_name):
        partner = user.partner_id
        if partner.bot_mail_channel_id and partner.id in partner.bot_mail_channel_id.channel_partner_ids.ids:
            channel = partner.bot_mail_channel_id
        else:
            OdooBot = 1
            channel = self.with_user(OdooBot).with_context(mail_create_nosubscribe=True).create({
                'public': 'private',
                'channel_type': 'chat',
                'channel_partner_ids': [(4, partner.id), (4, 2)],
                'name': 'OdooBot' + '/' + partner.name
            })
            partner.sudo().bot_mail_channel_id = channel.id
        message = (_(
            'Hello, {user_name} <br/>') + '{description} <a href=# data-oe-model={model} data-oe-id={id}>{name}</a> Require Your Approval').format(
            user_name=user.name,
            description=description,
            model=model,
            id=res_id,
            name=res_name,)

        channel.sudo().message_post(body=message, author_id=2, message_type="comment", subtype_xmlid='mail.mt_comment')
        return channel


    def notify_user_by_approval(self, user, description, model, res_id, res_name):
        partner = user.partner_id
        if partner.bot_mail_channel_id and partner.id in partner.bot_mail_channel_id.channel_partner_ids.ids:
            channel = partner.sudo().bot_mail_channel_id
        else:
            OdooBot = 1
            channel = self.env['mail.channel'].sudo().with_user(OdooBot).with_context(mail_create_nosubscribe=True).create({
                'public': 'private',
                'channel_type': 'chat',
                'channel_partner_ids': [(4, partner.id), (4, 2)],
                'name': 'OdooBot' + '/' + partner.name
            })
            partner.sudo().bot_mail_channel_id = channel.id
        message = (_(
            'Hello, {user_name} <br/>') + 'Your {description} <a href=# data-oe-model={model} data-oe-id={id}>{name}</a> has been Approved').format(
            user_name=user.name,
            description=description,
            model=model,
            id=res_id,
            name=res_name, )

        channel.sudo().message_post(body=message, author_id=2, message_type="comment", subtype_xmlid='mail.mt_comment')
        # return channel
        # return channel



class Partner(models.Model):
    _inherit = 'res.partner'

    # Relational Fields
    bot_mail_channel_id = fields.Many2one('mail.channel')
