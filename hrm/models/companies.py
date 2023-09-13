from odoo import models, fields, api
from . import constraint


class Companies(models.Model):
    _name = "hrm.companies"
    _description = "Companies"
    _rec_name = "name"

    name = fields.Char(string="Tên hiển thị", compute="_compute_name_company", store=True)
    name_company = fields.Char(string="Tên Công ty", required=True)
    parent_company = fields.Many2one('hrm.companies', string="Công ty cha")
    type_company = fields.Selection(selection=constraint.SELECT_TYPE_COMPANY, string="Loại công ty", required=True)
    system_id = fields.Many2one('hrm.systems', string="Hệ thống", required=True)
    phone_num = fields.Char(string="Số điện thoại", required=True)
    chairperson = fields.Many2one('res.users', string="Chủ tịch")
    vice_president = fields.Many2one('res.users', string='Phó chủ tịch')
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
                rec.name = rec.name_company
                return
            if rec.system_id:
                rec.name = f"{prefix}.{rec.system_id.name}.{rec.name_company}"
            else:
                rec.name = f"{prefix}.{rec.name_company}"
