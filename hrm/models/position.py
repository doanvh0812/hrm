from odoo import models, fields, api
from . import constraint


class Position(models.Model):
    _name = 'hrm.position'
    _rec_name = "work_position"

    work_position = fields.Char(string='Tên Vị Trí', required=True)
    block = fields.Selection(selection=[
        (constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_OFFICE_NAME),
        (constraint.BLOCK_COMMERCE_NAME, constraint.BLOCK_COMMERCE_NAME)], string="Khối", required=True)
    department = fields.Many2one("hrm.departments", string='Phòng/Ban')
    active = fields.Boolean(default=True)

    related = fields.Boolean(compute='_compute_related_field')

    @api.depends('block')
    def _compute_related_field(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block != constraint.BLOCK_OFFICE_NAME
