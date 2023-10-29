from odoo import models, fields, api
from . import constraint


class Users(models.Model):
    _inherit = 'res.users'

    block_id = fields.Selection(selection=[
        ('full', 'Tất cả khối'),
        (constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_OFFICE_NAME),
        (constraint.BLOCK_COMMERCE_NAME, constraint.BLOCK_COMMERCE_NAME)], string="Khối",
        default=constraint.BLOCK_COMMERCE_NAME)
    department_id = fields.Many2many('hrm.departments', string='Phòng/Ban')
    system_id = fields.Many2many('hrm.systems', string='Hệ thống')
    company = fields.Many2many('hrm.companies', string='Công ty')
    related = fields.Boolean(compute='_compute_related_')
    login = fields.Char(string="Login")

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            if not record.block_id:
                record.block_id = 'full'
            record.related = record.block_id == constraint.BLOCK_OFFICE_NAME

    @api.onchange('block_id')
    def _onchange_block_id(self):
        self.department_id = self.system_id = self.company = False

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

    def write(self, vals):
        res = super(Users, self).write(vals)
        self._remove_system_not_have_company()
        if 'name' in list(vals.keys()) and self.env.user.id == self.id:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        return res

    def create(self, vals_list):
        res = super(Users, self).create(vals_list)
        self._remove_system_not_have_company()
        return res
