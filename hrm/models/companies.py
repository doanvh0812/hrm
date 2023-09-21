import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Companies(models.Model):
    _name = "hrm.companies"
    _description = "Companies"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string="Tên hiển thị", compute='_compute_name_company', store=True)
    name_company = fields.Char(string="Tên công ty", required=True, tracking=True)
    parent_company = fields.Many2one('hrm.companies', string="Công ty cha", domain=[], tracking=True)
    type_company = fields.Selection(selection=constraint.SELECT_TYPE_COMPANY, string="Loại hình công ty", required=True,
                                    tracking=True)
    system_id = fields.Many2one('hrm.systems', string="Hệ thống", required=True, tracking=True)
    phone_num = fields.Char(string="Số điện thoại", required=True, tracking=True)
    chairperson = fields.Many2one('res.users', string="Chủ hộ")
    vice_president = fields.Many2one('res.users', string='Phó hộ')
    approval_id = fields.Many2one('hrm.approval.flow.object', tracking=True)
    active = fields.Boolean(string='Hoạt Động', default=True)
    change_system_id = fields.Many2one('hrm.systems', string="Hệ thống", default=False)

    @api.depends('system_id.name', 'type_company', 'name_company')
    def _compute_name_company(self):
        """
        decorator này để tự động tạo Tiên hiển thị theo logic 'Tiền tố . Tên hệ thông . Tên công ty'
        """
        for rec in self:
            name_main = rec.name_company or ''
            type_company = rec.type_company and rec.type_company[0].capitalize() or ''
            name_system = rec.system_id and rec.system_id.name or ''
            name_parts = [part for part in [type_company, name_system, name_main] if part]  # Lọc các trường không rỗng
            rec.name = '.'.join(name_parts)

    @api.constrains('name_company')
    def _check_name_case_insensitive(self):
        """ Kiểm tra trùng lặp dữ liệu không phân biệt hoa thường """
        for record in self:
            name = self.search([('id', '!=', record.id)])
            for n in name:
                if n['name_company'].lower() == record.name_company.lower():
                    raise ValidationError(constraint.DUPLICATE_RECORD % 'Công ty')

    @api.onchange('parent_company')
    def _onchange_parent_company(self):
        """decorator này  chọn cty cha
             sẽ tự hiển thị hệ thống mà công ty đó thuộc vào"""
        company_system = self.parent_company.system_id
        if company_system:
            self.system_id = company_system
        elif self.change_system_id:
            self.system_id = self.change_system_id
        else:
            self.system_id = False

    @api.onchange('system_id')
    def _onchange_company(self):
        """decorator này  chọn lại hệ thống sẽ clear công ty cha"""
        self.change_system_id = self.system_id
        if self.system_id != self.parent_company.system_id:
            self.parent_company = False

    @api.constrains("phone_num")
    def _check_phone_valid(self):
        """
        hàm kiểm tra số điện thoại: không âm, không có ký tự, có số 0 ở đầu
        """
        for rec in self:
            if rec.phone_num:
                if not re.match(r'^\d+$', rec.phone_num):
                    raise ValidationError(constraint.ERROR_PHONE)

    @api.constrains("chairperson", "vice_president")
    def _check_chairperson_and_vice_president(self):
        """ Kiểm tra xem chairperson và vice_president có trùng id không """
        for rec in self:
            chairperson_id = rec.chairperson.id if rec.chairperson else False
            vice_president_id = rec.vice_president.id if rec.vice_president else False

            if chairperson_id and vice_president_id and chairperson_id == vice_president_id:
                raise ValidationError("Chủ tịch và Phó chủ tịch không thể giống nhau.")

    # hàm này để hiển thị lịch sử lưu trữ
    def toggle_active(self):
        for record in self:
            record.active = not record.active
            if not record.active:
                record.message_post(body="Đã lưu trữ")
            else:
                record.message_post(body="Bỏ lưu trữ")
