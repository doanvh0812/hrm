from odoo import models, fields


class DocumentDeclaration(models.Model):
    _name = 'hrm.document_declaration'
    _description = 'Khai báo tài liệu'

    name = fields.Char(string='Tên hiển thị')
    profile_id = fields.Many2one('hrm.employee.profile')
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True)
    employee_id = fields.Many2one('res.users', string='Nhân viên')
    type_documents = fields.Many2one('hrm.documents', string='Loại tài liệu', required=True)
    system_id = fields.Many2one('hrm.systems', string='Hệ thống')
    company_id = fields.Many2one('hrm.companies', string='Công ty')
    department_id = fields.Many2one('hrm.departments', string='Phòng ban')
    give_back = fields.Boolean(string='Trả lại khi chấm dứt')
    manager_document = fields.Many2one('res.users', string='Quản lý tài liệu')
    complete = fields.Boolean(string='Hoàn thành')
    attachments = fields.Binary(string='Tệp đính kèm')
    attachment_ids = fields.Many2many('ir.attachment', 'model_attachment_rel', 'model_id', 'attachment_id',
                                      string='Tệp đính kèm')
