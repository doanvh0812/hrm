from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Blocks(models.Model):
    _name = 'hrm.blocks'
    _description = 'Block'

    name = fields.Char(string='Tên khối', required=True)
    description = fields.Text(string='Mô tả')
    active = fields.Boolean(string='Hoạt động', default=True)
    has_change = fields.Boolean(default=True)

    @api.constrains('name')
    def _check_name_case_insensitive(self):
        for record in self:
            # Kiểm tra trùng lặp dữ liệu không phân biệt hoa thường
            name = self.search([('id', '!=', record.id)])
            for n in name:
                if n['name'].lower() == record.name.lower():
                    raise ValidationError(constraint.DUPLICATE_RECORD % record.name)

    @api.onchange('name', 'description')
    def _onchange_name(self):
        if not self.has_change:
            raise ValidationError("Bạn không có quyền chỉnh sửa bản ghi này.")

    def action_archive(self):
        # Thực hiện kiểm tra điều kiện trước khi lưu trữ
        for line in self:
            if not line.has_change:
                raise ValidationError("Không thể lưu trữ bản ghi này.")
            else:
                # Tiến hành lưu trữ bản ghi
                return super(Blocks, self).action_archive()

    def unlink(self, context=None):
        # Chặn không cho xoá khối 'Văn phòng' và 'Thương mại'
        for line in self:
            if not line.has_change:
                raise ValidationError(constraint.DO_NOT_DELETE)
        return super(Blocks, self).unlink()
