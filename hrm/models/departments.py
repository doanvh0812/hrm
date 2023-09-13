from odoo import models, fields


class Department(models.Model):
    _name = "hrm.departments"

    name = fields.Char(string="Tên Phòng/Ban", required=True)
    manager_id = fields.Many2one("res.users", string="Quản lý", required=True)
    superior_department = fields.Many2one("hrm.departments", string="Phòng/Ban cấp trên")
    active = fields.Boolean(string='Hoạt động', default=True)
