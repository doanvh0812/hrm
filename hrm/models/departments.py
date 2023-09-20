import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Department(models.Model):
    _name = "hrm.departments"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string="Tên Phòng/Ban", required=True, tracking=True)
    manager_id = fields.Many2one("res.users", string="Quản lý", required=True, tracking=True)
    superior_department = fields.Many2one("hrm.departments", string="Phòng/Ban cấp trên",tracking=True)
    active = fields.Boolean(string='Hoạt Động',default=True)
    approval_id = fields.Many2one('hrm.approval.flow.object', tracking=True)

    @api.constrains('name')
    def _check_name_case_insensitive(self):
        for record in self:
            # Kiểm tra trùng lặp dữ liệu không phân biệt hoa thường
            name = self.search([('id', '!=', record.id)])
            for n in name:
                if n['name'].lower() == record.name.lower():
                    raise ValidationError(constraint.DUPLICATE_RECORD % "Phòng ban")

    @api.constrains("name")
    def _check_valid_name(self):
        """
        kiểm tra trường name không có ký tự đặc biệt.
        \W là các ký tự ko phải là chữ, dấu cách, _
        """
        for rec in self:
            if rec.name:
                if re.search(r"[\W]+", rec.name.replace(" ", "")) or "_" in rec.name:
                    raise ValidationError(constraint.ERROR_NAME % 'phòng/ban')

    # hàm này để hiển thị lịch sử lưu trữ
    def toggle_active(self):
        for record in self:
            record.active = not record.active
            if not record.active:
                record.message_post(body="Đã lưu trữ")
            else:
                record.message_post(body="Bỏ lưu trữ")
