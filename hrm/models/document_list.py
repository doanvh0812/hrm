import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint

class DocumentListConfig(models.Model):
    _name = 'hrm.document.list.config'
    _description = 'Cấu hình danh sách tài liệu'

    name = fields.Char(string='Tên hiển thị', required=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True)
    department_id = fields.Many2one('hrm.departments', string='Phòng ban')
    position_id = fields.Many2one('hrm.position', string='Vị trí')
    system_id = fields.Many2one('hrm.systems', string="Hệ thống")
    company = fields.Many2one('hrm.companies', string="Công ty")
    document_list = fields.One2many('hrm.document.list', 'document_id', string='Danh sách tài liệu')
class DocumentList(models.Model):
    _name = 'hrm.document.list'
    _description = 'Danh sách tài liệu'

    document_id = fields.Many2one('hrm.document.list.config')
    doc = fields.Many2one('hrm.documents', string='Tên tài liệu')
    status_doc = fields.Boolean(string='Trạng thái')