import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Companies(models.Model):
    _name = "hrm.companies"
    _description = "Companies"
    _rec_name = "name_company"

    name = fields.Char(string="Tên hiển thị")
    name_company = fields.Char(string="Tên công ty", required=True)
    parent_company = fields.Many2one('hrm.companies', string="Công ty cha", domain=[])
    type_company = fields.Selection(selection=constraint.SELECT_TYPE_COMPANY, string="Loại hình công ty", required=True)
    system_id = fields.Many2one('hrm.systems', string="Hệ thống", required=True)
    phone_num = fields.Char(string="Số điện thoại", required=True)
    chairperson = fields.Many2one('res.users', string="Chủ hộ")
    vice_president = fields.Many2one('res.users', string='Phó hộ')

    active = fields.Boolean(string='Hoạt động', default=True)

    @api.depends('system_id', 'type_company', 'name_company')
    def _compute_name_company(self):
        """
        decorator này để tự động tạo Tiên hiển thị theo logic 'Tiền tố . Tên hệ thông . Tên công ty'
        """
        for rec in self:
            if rec.name_company:
                rec.name = rec.name_company
            else:
                rec.name = ""
                return
            prefix = ""
            if rec.type_company == 'sale':
                prefix = "S"
            elif rec.type_company == 'upsale':
                prefix = "U"
            else:
                name_display = f"{prefix}.{rec.name_company}"
                rec.name = name_display
                rec.name = rec.name_company
                return
            if rec.system_id:
                rec.name = f"{prefix}.{rec.system_id.name}.{rec.name_company}"
            else:
                rec.name = f"{prefix}.{rec.name_company}"

    @api.constrains("phone_num")
    def _check_phone_valid(self):
        """
        hàm kiểm tra số điện thoại: không âm, không có ký tự, có số 0 ở đầu
        """
        for rec in self:
            if rec.phone_num:
                if not re.match(r'^[0]\d+$', rec.phone_num):
                    raise ValidationError("Số điện thoại không hợp lệ")


    @api.model
    def create(self, values):
        # Kiểm tra xem chairperson và vice_president có trùng id hay không
        chairperson_id = values.get('chairperson')
        vice_president_id = values.get('vice_president')

        if chairperson_id == vice_president_id:
            raise ValidationError("Chủ tịch và Phó chủ tịch không thể trùng nhau.")

        # Tiếp tục quá trình tạo bản ghi nếu không có trùng
        return super(Companies, self).create(values)