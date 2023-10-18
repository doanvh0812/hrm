from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
from . import constraint

class Documents(models.Model):
    _name = 'hrm.documents'
    _description = 'Tài liệu'

    name = fields.Char(string='Tên hiển thị', required=True)
    document_code = fields.Char(string='Mã tài liệu', required=True)
    numbers_of_photos = fields.Integer(string='Số lượng ảnh', required=True)
    numbers_of_document = fields.Integer(string='Số lượng tài liệu', required=True)


    @api.onchange('numbers_of_photos', 'numbers_of_document')
    def check_negative_numbers(self):
        if self.numbers_of_photos < 0 or self.numbers_of_document < 0:
            raise ValidationError('Số lượng phải là số nguyên dương!')

    @api.constrains('name')
    def check_duplicate_name(self):
        for record in self:
            name = self.search([('id', '!=', record.id)])
            for n in name:
                if n['name'].lower() == record.name.lower():
                    raise ValidationError(constraint.DUPLICATE_RECORD % "Tài liệu")
