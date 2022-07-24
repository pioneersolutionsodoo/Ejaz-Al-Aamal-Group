# -*- coding: utf-8 -*-

import json
from odoo import http
import werkzeug
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
import functools
import logging

_logger = logging.getLogger(__name__)


def serialize_exception(f):
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            _logger.exception("An exception occured during an http request")
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return werkzeug.exceptions.InternalServerError(json.dumps(error))

    return wrap


class Cri_Report(http.Controller):

    @http.route('/web/binary/download_document', type='http', auth="public")
    @serialize_exception
    def download_document(self, id, wiz_id, **kw):
        """ https://www.odoo.com/forum/help-1/question/press-a-button-and-download-a-file-how-93037
        """
        Model = request.env['hr.payslip']
        wiz_obj = request.env['ps.salary.statement.report.wiz']
        case = Model.browse(list(eval(id)))
        wiz_id = wiz_obj.browse(list(eval(wiz_id)))
        if kw.get('from'):
            report = Model.generate_wages_xls(case, wiz_id)
        else:
            report = Model.generate_xls(case, wiz_id)
        filename = 'Payslip.xlsx'
        return request.make_response(report,
                                     headers=[
                                         ('Content-Disposition', content_disposition(filename)),
                                         ('Content-Type', 'application/vnd.ms-excel'),
                                         ('Content-Length', len(report))],
                                     cookies={'fileToken': ''})
