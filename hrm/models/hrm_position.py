from odoo import models, fields


class Position(models.Model):
    _name = 'hrm.position'

    work_position = fields.Char(string='Tên Vị Trí', required=True)
    block = fields.Selection([('commerce', 'Thương Mại'), ('office', 'Văn Phòng')],
                             default='commerce', required=True)
    #TODO
    department = fields.Char(string='HRM-Cấu Hình-Phòng/Ban')
