from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Blocks(models.Model):
    _name = 'hrm.blocks'
    _description = 'Block'

    has_change = fields.Boolean(default=True)
    name = fields.Char(string='Tên khối', required=True)
    description = fields.Text(string='Mô tả', default='')
    # active = fields.Boolean(string='Hoạt động', default=True)

    @api.model
    def _auto_init(self):
        """
            Tự tạo các bản ghi 'Văn phòng', 'Thương mại'
            Duyệt qua bảng hrm.blocks
            Nếu không có bản ghi nào có tên 'Văn phòng' hoặc 'Thương mại' thì tạo mới cả 2
            Thiếu 1 bản ghi thì tạo mới bản ghi còn thiếu
        """
        super(Blocks, self)._auto_init()
        existing_records = self.env['hrm.blocks'].search([('has_change', '=', False)])
        if len(existing_records) == 0:
            self._default_value_office()
            self._default_value_trade()
        elif len(existing_records) == 1:
            for rec in existing_records:
                if rec.name == constraint.BLOCK_OFFICE_NAME:
                    self._default_value_trade()
                else:
                    self._default_value_office()

    # @api.constrains('active')
    # def _do_not_archive_(self):
    #     # Chặn không cho lưu trữ khối 'Văn phòng' và 'Thương mại'
    #     for line in self:
    #         if line.name in [constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_TRADE_NAME]:
    #             raise ValidationError(constraint.DO_NOT_ARCHIVE)

    def unlink(self, context=None):
        # Chặn không cho xoá khối 'Văn phòng' và 'Thương mại'
        for line in self:
            if line.name in [constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_TRADE_NAME]:
                raise ValidationError(constraint.DO_NOT_DELETE)
        return super(Blocks, self).unlink()

    def _default_value_office(self):
        # Tạo khối 'Văn phòng' mặc định
        self.create(constraint.DEFAULT_OFFICE)

    def _default_value_trade(self):
        # Tạo khối 'Thương mại' mặc định
        self.create(constraint.DEFAULT_TRADE)
