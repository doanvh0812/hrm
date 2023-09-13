from odoo import models, fields


class Position(models.Model):
    _name = 'hrm.position'
    _rec_name = 'work_position'

    work_position = fields.Char(string='Tên Vị Trí', required=True)
    block = fields.Selection([('commerce', 'Thương Mại'), ('office', 'Văn Phòng')], string='Khối',
                             default='commerce', required=True)

    department = fields.Char(string='Phòng/Ban')
    active = fields.Boolean(string='Hoạt động', default=True)
