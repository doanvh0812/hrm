from odoo import models, fields, api
from . import constraint


class Users(models.Model):
    _inherit = 'res.users'

    block_id = fields.Selection(selection=[
        ('full', ''),
        (constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_OFFICE_NAME),
        (constraint.BLOCK_COMMERCE_NAME, constraint.BLOCK_COMMERCE_NAME)], string="Khối", required=True,
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
        # clear dữ liệu
        if self.system_id != self.company.system_id:
            self.company = False
        list_id = []
        for sys in self.system_id.ids:
            fun = self.env['hrm.employee.profile']
            list_id += fun._system_have_child_company(sys)
        return {'domain': {'company': [('id', 'in', list_id)]}}

    def write(self, vals):
        res = super(Users, self).write(vals)
        if 'name' in list(vals.keys()) and self.env.user.id == self.id:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        return res

    def reload(self):
        # user_ids = self._context.get('active_model') == 'res.users' and self._context.get('active_ids') or []
        user_ids = self._context.get('active_model')
        print(self._context.get('active_ids'))
        print(user_ids)
        return {'type': 'ir.actions.act_window_close'}
        # user = [
        #     (0, 0, {'user_id': user.id, 'user_login': user.login})
        #     for user in self.env['res.users'].browse(user_ids)
        # ]
        # print(user)

