from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Department(models.Model):
    _name = "hrm.departments"

    name = fields.Char(string="Tên Phòng/Ban", required=True)
    manager_id = fields.Many2one("res.users", string="Quản lý", required=True)
    superior_department = fields.Many2one("hrm.departments", string="Phòng/Ban cấp trên")
    active = fields.Boolean(string='Hoạt động', default=True)

    @api.constrains('name')
    def _check_name_case_insensitive(self):
        for record in self:
            # Kiểm tra trùng lặp dữ liệu không phân biệt hoa thường
            name = self.search([('id', '!=', record.id)])
            for n in name:
                if n['name'].lower() == record.name.lower():
                    raise ValidationError(constraint.DUPLICATE_RECORD % record.name)
