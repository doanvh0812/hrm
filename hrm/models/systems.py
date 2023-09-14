from odoo import models, api, fields
from odoo.exceptions import ValidationError
from . import constraint
import re


class Systems(models.Model):
    _name = "hrm.systems"
    _description = "System of Hrm"

    name = fields.Char(string="Tên hiển thị", compute="_compute_name", store=True)
    name_system = fields.Char(string="Tên hệ thống", required=True)
    parent_system = fields.Many2one("hrm.systems", string="Hệ thống cha")
    type_system = fields.Selection(constraint.TYPE_SYSTEM, string="Loại hệ thống", required=True)
    phone_number = fields.Char(string="Số điện thoại")
    chairperson = fields.Many2one('res.users', string="Chủ tịch")
    vice_president = fields.Many2one('res.users', string='Phó chủ tịch')
    active = fields.Boolean(string="Hoạt động", default=True)
    company_ids = fields.One2many('hrm.companies', 'system_id', string='Công ty trong hệ thống')

    @api.depends("parent_system", "name_system")
    def _compute_name(self):
        """ Tính toán logic tên hiển thị """
        for rec in self:
            if rec.parent_system and rec.name_system:
                rec.name = f"{rec.parent_system.name}.{rec.name_system}"
            elif rec.name_system:
                rec.name = rec.name_system

    @api.constrains("chairperson", "vice_president")
    def _check_chairperson_and_vice_president(self):
        """ Kiểm tra xem chairperson và vice_president có trùng id không """
        for rec in self:
            chairperson_id = rec.chairperson.id if rec.chairperson else False
            vice_president_id = rec.vice_president.id if rec.vice_president else False

            if chairperson_id and vice_president_id and chairperson_id == vice_president_id:
                raise ValidationError("Chủ tịch và Phó chủ tịch không thể giống nhau.")

    @api.constrains("phone_number")
    def _check_phone_valid(self):
        """
        hàm kiểm tra số điện thoại: không âm, không có ký tự, có số 0 ở đầu
        """
        for rec in self:
            if rec.phone_number:
                if not re.match(r'^[0]\d+$', rec.phone_number):
                    raise ValidationError("Số điện thoại không hợp lệ")

    list_name = []

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
        self.get_name()
        for line in self:
            if str.lower(line.name) in self.list_name:
                raise ValidationError("Dữ liệu đã tồn tại hệ thống này")
