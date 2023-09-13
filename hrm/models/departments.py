from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Department(models.Model):
    _name = "hrm.departments"

    name = fields.Char(string="Tên Phòng/Ban", required=True)
    manager_id = fields.Many2one("res.users", string="Quản lý", required=True)
    superior_department = fields.Many2one("hrm.departments", string="Phòng/Ban cấp trên")
    active = fields.Boolean(string='Hoạt động', default=True)

    list_name = []

    @api.model
    def __int__(self):
        self.get_name()

    def get_name(self):
        """
        Lấy tất cả tên của các bản ghi lưu vào list_name.
        """
        for line in self:
            receive = str.lower(line.name)
            self.list_name.append(receive)

    @api.constrains('name')
    def check_name(self):
        """
        Kiểm tra name tồn tại trong các bản ghi.
        """
        for line in self:
            if str.lower(line.name) in self.list_name:
                raise ValidationError("Dữ liệu đã tồn tại phòng ban này")
        self.get_name()
