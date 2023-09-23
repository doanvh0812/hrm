import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Position(models.Model):
    _name = 'hrm.position'
    _description = 'Vị trí'
    _rec_name = "work_position"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    work_position = fields.Char(string='Tên Vị Trí', required=True, tracking=True)
    block = fields.Selection(selection=[
        (constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_OFFICE_NAME),
        (constraint.BLOCK_COMMERCE_NAME, constraint.BLOCK_COMMERCE_NAME)], string="Khối", required=True, tracking=True)
    department = fields.Many2one("hrm.departments", string='Phòng/Ban', tracking=True)
    active = fields.Boolean(string='Hoạt Động', default=True)

    related = fields.Boolean(compute='_compute_related_field')

    @api.constrains("work_position")
    def _check_valid_name(self):
        """
        kiểm tra trường name không có ký tự đặc biệt.
        \W là các ký tự ko phải là chữ, dấu cách, _
        """
        for rec in self:
            if rec.work_position:
                if re.search(r"[\W]+", rec.work_position.replace(" ", "")) or "_" in rec.work_position:
                    raise ValidationError(constraint.ERROR_NAME % 'vị trí')

    @api.depends('block')
    def _compute_related_field(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block != constraint.BLOCK_OFFICE_NAME

    # hàm này để hiển thị lịch sử lưu trữ
    def toggle_active(self):
        for record in self:
            record.active = not record.active
            if not record.active:
                record.message_post(body="Đã lưu trữ")
            else:
                record.message_post(body="Bỏ lưu trữ")

    """ tên vị trí giống nhau nhưng khối khác nhau vẫn có thể lưu được """

    @api.constrains('work_position', 'block')
    def _check_name_block_combination(self):
        # Kiểm tra sự trùng lặp dựa trên kết hợp của work_position và block
        for record in self:
            duplicate_records = self.search([
                ('id', '!=', record.id),
                ('work_position', 'ilike', record.work_position),
                ('block', '=', record.block),
            ])
            if duplicate_records:
                raise ValidationError(constraint.DUPLICATE_RECORD % "Vị trí")
