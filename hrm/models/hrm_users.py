from odoo import models, fields, api
from . import constraint


class Users(models.Model):
    _inherit = 'res.users'

    block_id = fields.Selection(selection=[
        (constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_OFFICE_NAME),
        (constraint.BLOCK_COMMERCE_NAME, constraint.BLOCK_COMMERCE_NAME)], string="Khối", required=True,
        default=constraint.BLOCK_COMMERCE_NAME)
    department_id = fields.Many2many('hrm.departments', string='Phòng/Ban')
    system_id = fields.Many2many('hrm.systems', string='Hệ thống')
    company = fields.Many2many('hrm.companies', string='Công ty')
    related = fields.Boolean(compute='_compute_related_')

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block_id == constraint.BLOCK_OFFICE_NAME

