# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Author: Nilmar Shereef (<shereef@cybrosys.in>)
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
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
import logging

_logger = logging.getLogger(__name__)
try:
    import mechanize
    import webbrowser
    from linkedin import linkedin
    from urllib.request import HTTPRedirectHandler as MechanizeRedirectHandler

except ImportError:
    _logger.error('Odoo module hr_linkedin_recruitment depends on the several external python package'
                  'Please read the doc/requirement.txt file inside the module.')

import requests
import mechanicalsoup
import json
from urllib.parse import urlsplit
from urllib.parse import parse_qs
from urllib.parse import urlparse
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
import builtins as exceptions


class HrJobShare(models.Model):
    _inherit = 'hr.job'

    description = fields.Text("Description")
    update_key = fields.Char(string='Update Key', readonly=True)

    def share_linkedin(self):
        """ Button function for sharing post """
        # credential_dict = self.get_authorize()
        if self.env['ir.config_parameter'].sudo().get_param('recruitment.li_access_token'):
            li_access_token = self.env['ir.config_parameter'].sudo().get_param('recruitment.li_access_token')
        else:
            raise ValidationError("Please add Access token in recruitment settings")
        # access_token = self.get_access_token()
        li_credential = self.get_profile(li_access_token)
        print(li_credential)
        if 'id' not in li_credential.keys():
            raise ValidationError("Please Check Access Token or Generate New One From Linkedin App Maybe Expired")
        share_data = {
            "author": "urn:li:person:" + str(li_credential["id"]),
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": self.description
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # URLS

        page_share_url = 'https://api.linkedin.com/v2/ugcPosts'
        if self.description:
            response = self.share_request('POST', page_share_url, li_access_token, data=json.dumps(share_data))
            share_response_text = response.json()
            share_response_code = response.status_code

            if share_response_code == 201:
                self.update_key = True

            elif share_response_code == 404:
                raise ValidationError("Resource does not exist.!")
            elif share_response_code == 409:
                raise ValidationError("Already shared!")
            else:
                raise ValidationError("Error!! Check your connection...")
        else:
            raise ValidationError("Provide a Job description....")

    def share_request(self, method, page_share_url, access_token, data):
        """ Function will return UPDATED KEY , [201] if sharing is OK """
        headers = {'x-li-format': 'json', 'Content-Type': 'application/json'}
        params = {}
        params.update({'oauth2_access_token': access_token})
        kw = dict(data=data, params=params, headers=headers, timeout=60)
        req_response = requests.request(method.upper(), page_share_url, **kw)
        return req_response

    # /////////////////////////////////////////////////////////////////////////////

    def get_profile(self, access_token):
        URL = "https://api.linkedin.com/v2/me"
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Authorization': 'Bearer {}'.format(access_token), 'X-Restli-Protocol-Version': '2.0.0'}
        response = requests.get(url=URL, headers=headers)
        print(response.json())
        return response.json()
    #
    # def get_auth_link(self):
    #     linkedin_auth_provider = self.env.ref('hr_linkedin_recruitment.provider_linkedin')
    #     URL = linkedin_auth_provider.auth_endpoint
    #     if linkedin_auth_provider.client_id and linkedin_auth_provider.client_secret:
    #         client_id = linkedin_auth_provider.client_id
    #         client_secret = linkedin_auth_provider.client_secret
    #     else:
    #         raise ValidationError(_('LinkedIn Access Credentials are empty.!\n'
    #                                 'Please fill up in Auth Provider form.'))
    #     redirect_uri = str(self.env['ir.config_parameter'].sudo().get_param('web.base.url')) + '/linkedin/callback'
    #     scope = "r_liteprofile"
    #     PARAMS = {'response_type': 'code', 'client_id': client_id, 'redirect_uri': redirect_uri, 'scope': scope}
    #     r = requests.get(url=URL, params=PARAMS)
    #     return_url = r.url
    #     return return_url
    #
    # def get_access_token(self):
    #     headers = {'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'OAuth gem v0.4.4'}
    #     AUTH_CODE = self.get_auth_link()
    #     ACCESS_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
    #     linkedin_auth_provider = self.env.ref('hr_linkedin_recruitment.provider_linkedin')
    #     # URL = linkedin_auth_provider.auth_endpoint
    #     if linkedin_auth_provider.client_id and linkedin_auth_provider.client_secret:
    #         client_id = linkedin_auth_provider.client_id
    #         client_secret = linkedin_auth_provider.client_secret
    #     else:
    #         raise ValidationError(_('LinkedIn Access Credentials are empty.!\n'
    #                                 'Please fill up in Auth Provider form.'))
    #     redirect_uri = 'http://localhost:8015/linkedin/callback'
    #
    #     if self.env['ir.config_parameter'].sudo().get_param('recruitment.li_code'):
    #         li_code = self.env['ir.config_parameter'].sudo().get_param('recruitment.li_code')
    #     else:
    #         webbrowser.open(AUTH_CODE)
    #
    #     PARAM = {'grant_type': 'authorization_code',
    #              'code': li_code,
    #              'redirect_uri': redirect_uri,
    #              'client_id': client_id,
    #              'client_secret': client_secret}
    #     response = requests.post(ACCESS_TOKEN_URL, data=PARAM, headers=headers, timeout=600)
    #     data = response.json()
    #     access_token = data['access_token']
    #     print(access_token)
    #     return access_token

    # /////////////////////////////////////////////////////////////////////////////
    def get_urn(self, method, has_access_url, access_token):
        """ Function will return TRUE if credentials user has the access to update """
        headers = {'x-li-format': 'json', 'Content-Type': 'application/json'}
        params = {}
        params.update({'oauth2_access_token': access_token})
        kw = dict(params=params, headers=headers, timeout=60)
        req_response = requests.request(method.upper(), has_access_url, **kw)
        return req_response

    def get_authorize(self):
        """ Supporting function for authenticating operations """
        li_credential = {}
        linkedin_auth_provider = self.env.ref('hr_linkedin_recruitment.provider_linkedin')
        if linkedin_auth_provider.client_id and linkedin_auth_provider.client_secret:
            li_credential['api_key'] = linkedin_auth_provider.client_id
            li_credential['secret_key'] = linkedin_auth_provider.client_secret
        else:
            raise ValidationError(_('LinkedIn Access Credentials are empty.!\n'
                                    'Please fill up in Auth Provider form.'))

        if self.env['ir.config_parameter'].sudo().get_param('recruitment.li_username'):
            li_credential['un'] = self.env['ir.config_parameter'].sudo().get_param('recruitment.li_username')
        else:
            raise ValidationError(_('Please fill up username in LinkedIn Credential settings.'))

        if self.env['ir.config_parameter'].sudo().get_param('recruitment.li_password'):
            li_credential['pw'] = self.env['ir.config_parameter'].sudo().get_param('recruitment.li_password')
        else:
            raise ValidationError(_('Please fill up password in LinkedIn Credential settings.'))

        # Browser Data Posting And Signing
        br = mechanicalsoup.StatefulBrowser()
        br.set_cookiejar(mechanize.CookieJar())
        return_uri = str(self.env['ir.config_parameter'].sudo().get_param('web.base.url')) + '/linkedin/callback'
        li_permissions = ['r_liteprofile']

        auth = linkedin.LinkedInAuthentication(li_credential['api_key'],
                                               li_credential['secret_key'],
                                               return_uri,
                                               li_permissions)
        print("||||||||||||||||||||||||||||", auth, return_uri, li_permissions)
        print("||||||||||||||||||||||||||||", auth.authorization_url)
        try:
            print(auth.authorization_url)
            br.open(auth.authorization_url)
            br.select_form(selector='form', nr=1)
            br['session_key'] = li_credential['un']
            br['session_password'] = li_credential['pw']
            br.submit_selected()
            try:
                auth.authorization_code = parse_qs(urlsplit(br.get_url()).query)['code']

            except:
                br.open(br.get_url())
                br.select_form(selector='form', nr=1)
                # q = br.submit_selected()
                auth.authorization_code = parse_qs(urlsplit(br.get_url()).query)['code']
                if not auth.authorization_code:
                    raise ValidationError("Please check Redirect URLs in the LinkedIn app settings!")
        except:
            raise ValidationError("Please check Redirect URLs in the LinkedIn app settings!")

        li_suit_credent = {}
        li_suit_credent['access_token'] = str(auth.get_access_token().access_token)
        member_url = 'https://api.linkedin.com/v2/me'
        response = self.get_urn('GET', member_url, li_suit_credent['access_token'])
        urn_response_text = response.json()

        li_credential['profile_urn'] = urn_response_text['id']

        li_suit_credent['li_credential'] = li_credential

        return li_suit_credent
