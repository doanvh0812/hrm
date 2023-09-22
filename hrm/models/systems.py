from odoo import models, api, fields
from odoo.exceptions import ValidationError
from . import constraint
import re


class Systems(models.Model):
    _name = "hrm.systems"
    _description = "Hệ thống"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string="Tên hiển thị", compute="_compute_name", store=True, )
    name_system = fields.Char(string="Tên hệ thống", required=True, tracking=True)
    parent_system = fields.Many2one("hrm.systems", string="Hệ thống cha", tracking=True)
    type_system = fields.Selection(constraint.TYPE_SYSTEM, string="Loại hệ thống", required=True, tracking=True)
    phone_number = fields.Char(string="Số điện thoại", tracking=True)
    chairperson = fields.Many2one('res.users', string="Chủ tịch")
    vice_president = fields.Many2one('res.users', string='Phó chủ tịch')
    active = fields.Boolean(string='Hoạt Động', default=True)
    company_ids = fields.One2many('hrm.companies', 'system_id', string='Công ty trong hệ thống')
    approval_id = fields.Many2one('hrm.approval.flow.object', tracking=True)


    @api.depends("parent_system.name", "name_system")
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
                if not re.match(r'^\d+$', rec.phone_number):
                    raise ValidationError("Số điện thoại không hợp lệ")

    # hàm này để hiển thị lịch sử lưu trữ
    def toggle_active(self):
        for record in self:
            record.active = not record.active
            if not record.active:
                record.message_post(body="Đã lưu trữ")
            else:
                record.message_post(body="Bỏ lưu trữ")

    @api.constrains('name', 'type_system')
    def _check_name_block_combination(self):
        # Kiểm tra sự trùng lặp dựa trên kết hợp của work_position và block
        for record in self:
            duplicate_records = self.search([
                ('id', '!=', record.id),
                ('name', 'like', record.name),
                ('type_system', '=', record.type_system),
            ])
            if duplicate_records:
                raise ValidationError(constraint.DUPLICATE_RECORD % "Hệ thống")





    # @api.depends("name_system")
    # def compute_list_parent(self, vals):
    #     sort_lst = []
    #     self._cr.execute(
    #         "SELECT LENGTH(name) - LENGTH(REPLACE(name, '.', '')) as count_dots, id FROM hrm_systems ORDER BY count_dots ASC")
    #     for item in self._cr.fetchall():
    #         sort_lst.append(self.env["hrm.systems"].browse(item[1]))
    #     print(sort_lst)
    #     return sort_lst

