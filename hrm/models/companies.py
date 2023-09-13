from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Companies(models.Model):
    _name = "hrm.companies"
    _description = "Companies"

    name = fields.Char(string="Tên hiển thị")
    name_company = fields.Char(string="Tên công ty", required=True)
    parent_company = fields.Many2one('hrm.companies', string="Công ty cha", domain=[])
    type_company = fields.Selection(selection=constraint.SELECT_TYPE_COMPANY, string="Loại hình công ty", required=True)
    system_id = fields.Many2one('hrm.systems', string="Hệ thống", required=True)
    phone_num = fields.Char(string="Số điện thoại", required=True)
    chairperson = fields.Many2one('res.users', string="Chủ hộ")
    vice_president = fields.Many2one('res.users', string='Phó hộ')

    active = fields.Boolean(string='Hoạt động', default=True)
    """
    decorator này để tự động tạo Tiên hiển thị theo logic 'Tiền tố . Tên hệ thông . Tên công ty'
    """
    @api.onchange('system_id', 'type_company', 'name_company')
    def update_name_company(self):
        for company in self:
            prefix = ""
            if company.type_company == 'sale':
                prefix = 'S'
            else:
                prefix = 'U'

            name_display = f"{prefix}.{company.system_id.name}.{company.name_company}"

            company.name = name_display
