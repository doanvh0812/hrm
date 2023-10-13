from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Documents(models.Model):
    _name = 'hrm.documents'
    _description = 'Tài liệu'

    name = fields.Char(string='Tên hiển thị', required=True)
    document_code = fields.Char(string='Mã tài liệu', required=True)
    numbers_of_photos = fields.Integer(string='Số lượng ảnh', required=True)
    numbers_of_document = fields.Integer(string='Số lượng tài liệu', required=True)
