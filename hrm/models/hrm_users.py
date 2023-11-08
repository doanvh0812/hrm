from odoo import models, fields, api
from . import constraint
import random


def random_token():
    # the token has an entropy of about 120 bits (6 bits/char * 20 chars)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.SystemRandom().choice(chars) for _ in range(20))


class Users(models.Model):
    _inherit = 'res.users'

    block_id = fields.Selection(selection=[
        ('full', 'Tất cả khối'),
        (constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_OFFICE_NAME),
        (constraint.BLOCK_COMMERCE_NAME, constraint.BLOCK_COMMERCE_NAME)], string="Khối phân quyền",
        default=constraint.BLOCK_COMMERCE_NAME, required=True)
    department_id = fields.Many2many('hrm.departments', string='Phòng/Ban phân quyền')
    system_id = fields.Many2many('hrm.systems', string='Hệ thống phân quyền')
    company = fields.Many2many('hrm.companies', string='Công ty phân quyền')
    related = fields.Boolean(compute='_compute_related_')

    user_block_id = fields.Many2one('hrm.blocks', string='Khối', required=True,default=lambda self: self.default_block())
    user_department_id = fields.Many2one('hrm.departments', string='Phòng ban')
    user_system_id = fields.Many2one('hrm.systems', string='Hệ thống')
    user_company_id = fields.Many2one('hrm.companies', string='Công ty')
    user_code = fields.Char(string="Mã nhân viên")
    user_position_id = fields.Many2one('hrm.position', string='Vị trí', required=True)
    user_team_marketing = fields.Many2one('hrm.teams', string='Đội ngũ marketing')
    user_team_sales = fields.Many2one('hrm.teams', string='Đội ngũ bán hàng')
    user_phone_num = fields.Char('Số điện thoại di động', required=True)
    user_name_display = fields.Char('Tên hiển thị', readonly=True)
    user_related = fields.Boolean(compute='compute_related')
    require_team = fields.Boolean(default=False)

    url_reset_password = fields.Char(string='Reset Password URL')

    def default_block(self):
        """Đặt giá trị mặc định cho trường khối của tài khoản nhân sự"""
        return self.env['hrm.blocks'].sudo().search([('name', '=', constraint.BLOCK_COMMERCE_NAME)])

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block_id == constraint.BLOCK_OFFICE_NAME

    @api.depends('user_block_id')
    def compute_related(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị (thiết lập nhân sự)
        for record in self:
            record.user_related = record.user_block_id.name == constraint.BLOCK_OFFICE_NAME

    @api.onchange('block_id')
    def _onchange_block_id(self):
        self.department_id = self.system_id = self.company = False

    @api.onchange('user_block_id')
    def _onchange_block_id(self):
        """
            Khi chọn lại khối clear hết data cũ đã nhập (thiết lập nhân sự)
        """
        self.user_position_id = self.user_system_id = self.user_company_id = self.user_department_id \
            = self.user_team_sales = self.user_team_marketing = False

    @api.onchange('user_position_id')
    def onchange_position_id(self):
        """
            Khi thay đổi vị trí sẽ check loại đội ngũ hiển thị là gì.
        """
        if self.user_position_id.team_type == 'marketing':
            self.require_team = True
        else:
            self.require_team = False

    @api.onchange('system_id')
    def _onchange_system_id(self):
        """
            decorator này khi tạo hồ sơ nhân viên, chọn 1 hệ thống nào đó
            khi ta chọn cty nó sẽ hiện ra tất cả những cty có trong hệ thống đó
        """
        if self.system_id:
            # khi bỏ trường hệ thống thì loại bỏ các cty con của nó
            current_company_ids = self.company.ids
            child_company = []
            func = self.env['hrm.utils']
            for sys in self.system_id:
                child_company += func._system_have_child_company(sys.id.origin)
            # lấy ra cty chung trong hai list cty
            company_ids = list(set(current_company_ids) & set(child_company))
            self.company = [(6, 0, company_ids)]
            list_id = []
            for sys in self.system_id.ids:
                func = self.env['hrm.utils']
                list_id += func._system_have_child_company(sys)
            return {'domain': {'company': [('id', 'in', list_id)]}}
        self.company = [(6, 0, [])]

    def _remove_system_not_have_company(self):
        """
            Xóa hệ thống không có công ty
        """
        if self.company:
            list_system_ids = self.system_id.ids
            for sys in self.system_id.ids:
                func = self.env['hrm.utils']
                if not any(company in func._system_have_child_company(sys) for company in self.company.ids):
                    self.system_id = [(6, 0, list_system_ids)]

    def action_reset_password(self):
        token = random_token()
        type = 'reset'
        expiration = False
        self.partner_id.sudo().write({'signup_token': token, 'signup_type': type, 'signup_expiration': expiration})
        self.url_reset_password = f"http://localhost:8012/web/reset_password?db=hrm&token={token}"
        print(self.url_reset_password)

    def write(self, vals):
        res = super(Users, self).write(vals)
        self._remove_system_not_have_company()
        if 'name' in list(vals.keys()) and self.env.user.id == self.id:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        return res

    @api.model
    def create(self, vals_list):
        res = super(Users, self).create(vals_list)
        self._remove_system_not_have_company()
        return res
