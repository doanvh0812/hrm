from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError
from . import constraint

class Documents(models.Model):
    _name = 'hrm.documents'
    _description = 'Tài liệu'

    name = fields.Char(string='Tên hiển thị', required=True)
    document_code = fields.Char(string='Mã tài liệu', required=True)
    numbers_of_photos = fields.Integer(string='Số lượng ảnh', required=True)
    numbers_of_documents = fields.Integer(string='Số lượng tài liệu', required=True)

    @api.constrains('numbers_of_photos', 'numbers_of_documents')
    def check_negative_numbers(self):
        if self.numbers_of_photos < 0 or self.numbers_of_documents < 0:
            raise ValidationError('Số lượng ảnh và tài liệu không thể là số âm!')
    @api.constrains('name')
    def check_duplicate_name(self):
        for record in self:
            name = self.search([('id', '!=', record.id)])
            for n in name:
                if n['name'].lower() == record.name.lower():
                    raise ValidationError(constraint.DUPLICATE_RECORD % "Tài liệu")

