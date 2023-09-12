from odoo import models, api, fields
from . import constraint


class Systems(models.Model):
    _name = "hrm.systems"
    _description = "System of Hrm"

    name = fields.Char(string="Tên hiển thị", compute="_compute_name", readonly=True)
    name_system = fields.Char(string="Tên hệ thống", required=True)
    parent_system = fields.Many2one("hrm.systems", string="Hệ thống cha")
    type_system = fields.Selection(constraint.TYPE_SYSTEM, string="Loại hệ thống", required=True)
    phone_number = fields.Char(string="Số điện thoại")
    chairperson = fields.Char(string="Chủ tịch")
    vice_president = fields.Char(string="Phó chủ tịch")
    active = fields.Boolean(string="Hoạt động")

    @api.depends("parent_system", "name_system")
    def _compute_name(self):
        """ Tính toán logic tên hiển thị """
        for rec in self:
            if rec.parent_system:
                rec.name = f"{rec.parent_system.display_name}.{rec.name_system}"
            else:
                rec.name = rec.name_system
