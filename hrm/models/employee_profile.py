from odoo import models, fields, api
from . import constraint


class EmployeeProfile(models.Model):
    _name = 'hrm.employee_profile'
    _description = 'Bảng thông tin nhân viên'

    name = fields.Char(string='Họ và tên nhân sự', required=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, default=lambda self: self._default_block_())
    # position_id = fields.Many2one('hrm.position', required=True) chưa có model position
    work_start_date = fields.Date(string='Ngày vào làm')
    date_receipt = fields.Date(string='Ngày được nhận chính thức', required=True)
    employee_code = fields.Char(string='Mã nhân viên', required=True)
    email = fields.Char('Email công việc', required=True)
    phone_num = fields.Integer('Số điện thoại di động', required=True)
    identifier = fields.Integer('Số căn cước công dân', required=True)
    profile_status = fields.Boolean(string='Trạng thái hồ sơ', default=False)
    # system_id = fields.Many2one('hrm.systems', string='Hệ thống')
    # company chưa có model systems
    # team_marketing = chưa có model position
    # team_sales = chưa có model position
    # department_id = chưa có model department
    # manager_id = chưa có model employee
    # rank_id = chưa có model rank
    auto_create_acc = fields.Boolean(string='Tự động tạo tài khoản')

    def _default_block_(self):
        ids = self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_TRADE_NAME)], limit=1).id
        print('---------------->', ids)
        return ids
