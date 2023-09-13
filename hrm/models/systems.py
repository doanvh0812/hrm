from odoo import models, api, fields
from . import constraint


class Systems(models.Model):
    _name = "hrm.systems"
    _description = "System of Hrm"
    _rec_name = "name_system"

    name = fields.Char(string="Tên hiển thị", compute="_compute_name", store=True)
    name_system = fields.Char(string="Tên hệ thống", required=True)
    parent_system = fields.Many2one("hrm.systems", string="Hệ thống cha")
    type_system = fields.Selection(constraint.TYPE_SYSTEM, string="Loại hệ thống", required=True)
    phone_number = fields.Char(string="Số điện thoại")
    chairperson = fields.Char(string="Chủ tịch")
    vice_president = fields.Char(string="Phó chủ tịch")

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
