from odoo import models, api, fields
from odoo.exceptions import ValidationError
from . import constraint


class Systems(models.Model):
    _name = "hrm.systems"
    _description = "System of Hrm"
    _rec_name = "name"

    name = fields.Char(string="Tên hiển thị", compute="_compute_name", store=True)
    name_system = fields.Char(string="Tên hệ thống", required=True)
    parent_system = fields.Many2one("hrm.systems", string="Hệ thống cha")
    type_system = fields.Selection(constraint.TYPE_SYSTEM, string="Loại hệ thống", required=True)
    phone_number = fields.Char(string="Số điện thoại")
    chairperson = fields.Many2one('res.users', string="Chủ tịch")
    vice_president = fields.Many2one('res.users', string='Phó chủ tịch')
    active = fields.Boolean(string="Hoạt động", default=True)
    company_ids = fields.One2many('hrm.companies', 'system_id', string='Công ty trong hệ thống')

    @api.depends("parent_system", "name_system")
    def _compute_name(self):
        """ Tính toán logic tên hiển thị """
        for rec in self:
            if rec.parent_system and rec.name_system:
                rec.name = f"{rec.parent_system.name}.{rec.name_system}"
            elif rec.name_system:
                rec.name = rec.name_system

    @api.model
    def create(self, values):
        # Kiểm tra xem chairperson và vice_president có trùng id hay không
        chairperson_id = values.get('chairperson')
        vice_president_id = values.get('vice_president')

        if chairperson_id == vice_president_id:
            raise ValidationError("Chủ tịch và Phó chủ tịch không thể trùng nhau.")

        # Tiếp tục quá trình tạo bản ghi nếu không có trùng
        return super(Systems, self).create(values)
