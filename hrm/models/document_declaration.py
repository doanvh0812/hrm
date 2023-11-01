from odoo import api, models, fields
from odoo.exceptions import ValidationError
from . import constraint


class DocumentDeclaration(models.Model):
    _name = 'hrm.document_declaration'
    _description = 'Khai báo tài liệu'

    name = fields.Char(string='Tên hiển thị', compute='_compute_name_team', store=True)
    profile_id = fields.Many2one('hrm.employee.profile')
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, related='employee_id.block_id')
    related = fields.Boolean(compute='_compute_related_')
    employee_id = fields.Many2one('hrm.employee.profile', string='Nhân viên', required=True)
    type_documents = fields.Many2one('hrm.documents', string='Loại tài liệu', required=True)
    system_id = fields.Many2one('hrm.systems', string='Hệ thống', related='employee_id.system_id')
    company = fields.Many2one('hrm.companies', string='Công ty', related='employee_id.company')
    department_id = fields.Many2one('hrm.departments', string='Phòng ban', related='employee_id.department_id')
    give_back = fields.Boolean(string='Trả lại khi chấm dứt')
    manager_document = fields.Many2one('res.users', string='Quản lý tài liệu')
    complete = fields.Boolean(string='Hoàn thành')

    attachment_ids = fields.Many2many('ir.attachment', 'model_attachment_rel', 'model_id', 'attachment_id',
                                      string='Tệp đính kèm')

    # image_ids = fields.Many2many('ir.attachment', 'document_image_rel', 'document_id', 'attachment_id',
    #                              string='Tệp hình ảnh')

    picture_ids = fields.One2many('hrm.image', 'document_declaration', string="Hình ảnh")
    # public_image_url = fields.Char(compute="_compute_image_related_fields", compute_sudo=True, store=True)
    # has_picture = fields.Boolean(compute="_compute_image_related_fields", store=True, compute_sudo=True)
    max_photos = fields.Integer(related='type_documents.numbers_of_photos')
    max_files = fields.Integer(related='type_documents.numbers_of_documents')
    see_record_with_config = fields.Boolean()

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        self.env['hrm.utils']._see_record_with_config('hrm.document_declaration')
        return super(DocumentDeclaration, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                                submenu=submenu)

    @api.depends('employee_id', 'type_documents')
    def _compute_name_team(self):
        """
        Phần này tự động tạo tên hiển thị dựa trên logic 'Tên nhân viên _ Loại tài liệu'.
        """
        for rec in self:
            employee_name = rec.employee_id.name if rec.employee_id else ''
            type_name = rec.type_documents.name if rec.type_documents else ''

            if employee_name and type_name:
                rec.name = f"{employee_name} _ {type_name}"
            else:
                rec.name = ''

    @api.onchange('type_documents', 'attachment_ids')
    def onchange_type_documents(self):
        max_photos = 0
        max_files = 0

        if self.type_documents.numbers_of_photos == 0:
            max_photos = float('inf')  # Không giới hạn số lượng ảnh
        elif self.type_documents.numbers_of_photos > 0:
            max_photos = self.type_documents.numbers_of_photos

        if self.type_documents.numbers_of_documents == 0:
            max_files = float('inf')  # Không giới hạn số lượng tệp tài liệu
        elif self.type_documents.numbers_of_documents > 0:
            max_files = self.type_documents.numbers_of_documents

        # Kiểm tra số lượng ảnh
        # if len(self.image_ids) > max_photos:
        #     self.image_ids = False
        #     raise ValidationError('Vượt quá số lượng ảnh tối đa cho phép!')

        # Kiểm tra số lượng tệp tài liệu
        # if len(self.attachment_ids) > max_files:
        #     self.attachment_ids = False
        #     raise ValidationError('Vượt quá số lượng tệp tài liệu tối đa cho phép!')
        # if self.image_ids:
        #     self.image_ids = [(6, 0, self.image_ids.ids)]

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block_id.name == constraint.BLOCK_OFFICE_NAME

    @api.onchange('name')
    def default_employee(self):
        """Gán giá trị của trường nhân viên khi tạo mới bản ghi tại màn Tạo mới hồ sơ."""
        if self.profile_id:
            self.employee_id = self.profile_id.id


# @api.depends("picture_ids", "picture_ids.public_image_url")
# def _compute_image_related_fields(self):
#     for rec in self:
#         rec.has_picture = rec.picture_ids and len(rec.picture_ids) > 0
#         if rec.picture_ids and len(rec.picture_ids) > 0:
#             rec.has_picture = True
#             public_image_urls = [str(x.public_image_url) for x in rec.picture_ids]
#             rec.public_image_url = ','.join(public_image_urls)
#         else:
#             rec.has_picture = False

