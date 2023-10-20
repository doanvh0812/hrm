from odoo import api, models, fields
from odoo.exceptions import ValidationError
from . import constraint


class DocumentDeclaration(models.Model):
    _name = 'hrm.document_declaration'
    _description = 'Khai báo tài liệu'

    name = fields.Char(string='Tên hiển thị')
    profile_id = fields.Many2one('hrm.employee.profile')
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, related='employee_id.block_id')
    related = fields.Boolean(compute='_compute_related_')
    employee_id = fields.Many2one('hrm.employee.profile', string='Nhân viên')
    type_documents = fields.Many2one('hrm.documents', string='Loại tài liệu', required=True)
    system_id = fields.Many2one('hrm.systems', string='Hệ thống', related='employee_id.system_id')
    company_id = fields.Many2one('hrm.companies', string='Công ty', related='employee_id.company')
    department_id = fields.Many2one('hrm.departments', string='Phòng ban', related='employee_id.department_id')
    give_back = fields.Boolean(string='Trả lại khi chấm dứt')
    manager_document = fields.Many2one('res.users', string='Quản lý tài liệu')
    complete = fields.Boolean(string='Hoàn thành')
    attachments = fields.Binary(string='Tệp đính kèm')
    attachment_ids = fields.Many2many('ir.attachment', 'model_attachment_rel', 'model_id', 'attachment_id',
                                      string='Tệp đính kèm')
    attachment_image_ids = fields.Many2many('ir.attachment', 'model_attachment_rel', 'model_id', 'attachment_id',
                                            string='Tệp tin ảnh')

    image = fields.Binary(string='Tệp hình ảnh')
    image_ids = fields.Many2many('ir.attachment', 'model_attachment_rel', 'model_id', 'attachment_id',
                                 string='Tệp hình ảnh')

    max_photos = fields.Integer(related='type_documents.numbers_of_photos')
    max_files = fields.Integer(related='type_documents.numbers_of_documents')

    @api.onchange('type_documents', 'image_ids', 'attachment_ids')
    def onchange_type_documents(self):
        max_photos = 0
        max_attachments = 0

        if self.type_documents.numbers_of_photos == 0:
            max_photos = float('inf')  # Không giới hạn số lượng ảnh
        elif self.type_documents.numbers_of_photos > 0:
            max_photos = self.type_documents.numbers_of_photos

        if self.type_documents.numbers_of_documents == 0:
            max_attachments = float('inf')  # Không giới hạn số lượng tệp tài liệu
        elif self.type_documents.numbers_of_documents > 0:
            max_attachments = self.type_documents.numbers_of_documents

        # Kiểm tra số lượng ảnh
        if len(self.image_ids) > max_photos:
            self.image_ids = False
            raise ValidationError('Vượt quá số lượng ảnh tối đa cho phép!')

        # Kiểm tra số lượng tệp tài liệu
        if len(self.attachment_ids) > max_attachments:
            self.attachment_ids = False
            raise ValidationError('Vượt quá số lượng tệp tài liệu tối đa cho phép!')

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block_id.name == constraint.BLOCK_OFFICE_NAME
            print(record.related)