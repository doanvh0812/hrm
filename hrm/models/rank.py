import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Ranks(models.Model):
    _name = 'hrm.ranks'
    _description = 'Cấp bậc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Tên cấp bậc', required=True)
    abbreviations = fields.Char(string='Tên viết tắt')
    department = fields.Many2one('hrm.departments', string='Phòng/Ban', required=True)
    active = fields.Boolean(string='Hoạt Động', default=True)

    @api.constrains('name', 'abbreviations')
    def check_duplicate(self):
        """ Kiểm tra trùng lặp dữ liệu không phân biệt hoa thường """
        for record in self:
            name = self.search([('id', '!=', record.id), ('active', 'in', (True, False))])
            for n in name:
                if n['name'].lower() == record.name.lower() and n.department == self.department:
                    raise ValidationError(constraint.DUPLICATE_RECORD % 'Cấp bậc')
                if (self.abbreviations and n['abbreviations'] and
                        n['abbreviations'].lower() == record.abbreviations.lower() and n.department == self.department):
                    raise ValidationError(constraint.DUPLICATE_RECORD % 'Tên viết tắt')

    @api.constrains('name', 'abbreviations', 'department')
    def _check_rank_access(self):
        if self.env.user.block_id == constraint.BLOCK_COMMERCE_NAME:
            raise ValidationError("Bạn không có quyền thực hiện tác vụ này trong khối thương mại")
