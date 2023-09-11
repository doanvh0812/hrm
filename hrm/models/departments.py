from odoo import models, fields


class Department(models.Model):
    _name = "hrm.departments"

    name = fields.Char(string="Tên phòng ban", required=True)
    manager_id = fields.Selection("res.users", string="Quản lý", required=True)
    superior_department = fields.Selection("hrm.departments", string="Phòng/Ban cấp trên")
