import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessDenied
from . import constraint
from odoo import http

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
    related = fields.Boolean(compute='_compute_related_')

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block_id.name == constraint.BLOCK_OFFICE_NAME

    @api.onchange('block_id')
    def _onchange_block(self):
        self.company = self.department_id = self.system_id = False

    @api.onchange('document_list')
    def set_sequence(self):
        i = 1
        for document in self.document_list:
            document.sequence = i
            i += 1

    @api.constrains('name', 'block_id', 'department_id', 'position_id', 'system_id', 'company')
    def check_duplicate_document_config(self):
        """hàm này để kiểm tra trùng lặp cấu hình danh sách tài liệu cho các đối tượng được áp dụng"""
        def check_exist_object(department_id=False, position_id=False, system_id=False, company=False):
            check = self.search([('block_id', '=', self.block_id.id), ('id', 'not in', [self.id, False]),
                                 ('department_id', '=', department_id), ('position_id', '=', position_id),
                                 ('system_id', '=', system_id), ('company', '=', company)])
            return check.ids

        if self.position_id and check_exist_object(position_id=self.position_id.id, department_id=self.department_id.id, system_id=self.system_id.id, company=self.company.id):
            raise ValidationError(f"Đã có cấu hình danh sách tài liệu cho vị trí {self.position_id.work_position}")
        elif not self.position_id and self.department_id and check_exist_object(department_id=self.department_id.id):
            raise ValidationError(f"Đã có cấu hình danh sách tài liệu cho phòng ban {self.department_id.name}")
        elif self.company and check_exist_object(company=self.company.id, system_id=self.system_id.id):
            raise ValidationError(f"Đã có cấu hình danh sách tài liệu cho công ty {self.company.name}")
        elif not self.company and self.system_id and check_exist_object(system_id=self.system_id.id):
            raise ValidationError(f"Đã có cấu hình danh sách tài liệu cho hệ thống {self.system_id.name}")
        elif not self.system_id and not self.department_id and check_exist_object():
            raise ValidationError(f"Đã có cấu hình danh sách tài liệu cho khối {self.block_id.name}")

    def unlink(self):
        for record in self:
            document = self.env['hrm.employee.profile'].sudo().search([('document_config', '=', record.id)])
            if document:
                raise AccessDenied("Không thể xoá " + record.name)
        return super(DocumentListConfig, self).unlink()

    @api.constrains('document_list')
    def check_approval_flow_link(self):
        if not self.document_list:
            raise ValidationError('Không thể tạo khi không có tài liệu nào trong danh sách tài liệu.')
        else:
            list_check = []
            for item in self.document_list:
                if item.obligatory:
                    list_check.append(True)
            if not any(list_check):
                raise ValidationError('Cần có ít nhất một tài liệu bắt buộc.')

class DocumentList(models.Model):
    _name = 'hrm.document.list'
    _description = 'Danh sách tài liệu'

    document_id = fields.Many2one('hrm.document.list.config')
    sequence = fields.Integer(string="STT")
    doc = fields.Many2one('hrm.documents', string='Tên tài liệu')
    name = fields.Char(related='doc.name')
    obligatory = fields.Boolean(string='Bắt buộc')
