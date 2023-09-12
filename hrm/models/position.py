from odoo import models, fields, api
from . import constraint


class Position(models.Model):
    _name = 'hrm.position'

    work_position = fields.Char(string='Tên Vị Trí', required=True)
    block = fields.Many2one('hrm.blocks', string="Khối", required=True, default=lambda self: self.__default_block_())
    department = fields.Many2one("hrm.departments", string='Phòng/Ban')

    related = fields.Boolean()

    @api.onchange('block')
    def _compute_related_field(self):
        for record in self:
            if record.block.name == constraint.BLOCK_OFFICE_NAME:
                record.related = True
            else:
                record.related = False

    def _default_block_(self):
        ids = self.env['hrm.blocks'].search([('work_position', '=', constraint.BLOCK_TRADE_NAME)], limit=1).id
        print('---------------->', ids)
        return ids
