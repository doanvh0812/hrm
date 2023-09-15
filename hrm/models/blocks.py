from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Blocks(models.Model):
    _name = 'hrm.blocks'
    _description = 'Block'

    has_change = fields.Boolean(default=True)
    name = fields.Char(string='Tên khối', required=True)
    description = fields.Text(string='Mô tả', default='')
    create_new = fields.Boolean(default=False)
    active = fields.Boolean(string='Hoạt động', default=True)

    @api.constrains('name')
    def _check_name_case_insensitive(self):
        for record in self:
            # Kiểm tra trùng lặp dữ liệu không phân biệt hoa thường
            if record.name:
                duplicate_records = self.search([('id', '!=', record.id), ('name', 'ilike', record.name)])
                if duplicate_records:
                    raise ValidationError(constraint.DUPLICATE_RECORD % record.name)

    # @api.model
    # def _auto_init(self):
    #     """
    #         Tự tạo các bản ghi 'Văn phòng', 'Thương mại'
    #         Duyệt qua bảng hrm.blocks
    #         Nếu không có bản ghi nào có tên 'Văn phòng' hoặc 'Thương mại' thì tạo mới cả 2
    #         Thiếu 1 bản ghi thì tạo mới bản ghi còn thiếu
    #     """
    #     super(Blocks, self)._auto_init()
    #     existing_records = self.env['hrm.blocks'].search([('has_change', '=', False)])
    #     if len(existing_records) == 0:
    #         self._default_value_office()
    #         self._default_value_trade()
    #     elif len(existing_records) == 1:
    #         for rec in existing_records:
    #             if rec.name == constraint.BLOCK_OFFICE_NAME:
    #                 self._default_value_trade()
    #             else:
    #                 self._default_value_office()

    def action_archive(self):
        # Thực hiện kiểm tra điều kiện trước khi lưu trữ
        for line in self:
            if line.name in [constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_COMMERCE_NAME]:
                raise ValidationError("Không thể lưu trữ bản ghi này.")
            else:
                # Tiến hành lưu trữ bản ghi
                return super(Blocks, self).action_archive()

    def unlink(self, context=None):
        # Chặn không cho xoá khối 'Văn phòng' và 'Thương mại'
        for line in self:
            if line.name in [constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_COMMERCE_NAME]:
                raise ValidationError(constraint.DO_NOT_DELETE)
        return super(Blocks, self).unlink()

    def _default_value_office(self):
        # Tạo khối 'Văn phòng' mặc định
        self.create(constraint.DEFAULT_OFFICE)

    def _default_value_trade(self):
        # Tạo khối 'Thương mại' mặc định
        self.create(constraint.DEFAULT_TRADE)
