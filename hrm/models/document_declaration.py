from odoo import models, fields


class DocumentDeclaration(models.Model):
    _name = 'hrm.document_declaration'
    _description = 'Khai báo tài liệu'

    name = fields.Char(string='Tên hiển thị')
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True)
    employee_id = fields.Many2one('res.users', string='Nhân viên')
    # type_documents = fields.Many2one('')