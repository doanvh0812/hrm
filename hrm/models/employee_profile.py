from odoo import models, fields, api
from . import constraint


class EmployeeProfile(models.Model):
    _name = 'hrm.employee.profile'
    _description = 'Bảng thông tin nhân viên'

    name = fields.Char(string='Họ và tên nhân sự', required=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, default=lambda self: self._default_block_())
    # position_id = fields.Many2one('hrm.position', required=True)
    work_start_date = fields.Date(string='Ngày vào làm')
    date_receipt = fields.Date(string='Ngày được nhận chính thức', required=True)
    employee_code = fields.Char(string='Mã nhân viên', required=True)
    email = fields.Char('Email công việc', required=True)
    phone_num = fields.Integer('Số điện thoại di động', required=True)
    identifier = fields.Integer('Số căn cước công dân', required=True)
    profile_status = fields.Selection(constraint.PROFILE_STATUS, string='Trạng thái hồ sơ', default=False)
    system_id = fields.Many2one('hrm.systems', string='Hệ thống')
    company = fields.Many2one('hrm.systems')
    # team_marketing = chưa có model position
    # team_sales = chưa có model position
    # department_id = chưa có model department
    manager_id = fields.Many2one('res.users', string='Quản lý')
    # rank_id = chưa có model rank
    auto_create_acc = fields.Boolean(string='Tự động tạo tài khoản')

    @api.onchange('block_id')
    def _check_block_(self):
        self.fields_view_get()

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(EmployeeProfile, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                           submenu=submenu)

        # Thay đổi thuộc tính của trường 'company'
        if view_type == 'form':
            for field_name, field_attrs in res['fields'].items():
                if field_name == 'company':
                    # Thiết lập thuộc tính 'invisible' cho trường 'company' dựa trên giá trị của 'block_id'
                    field_attrs['invisible'] = [('block_id.name', '=', constraint.BLOCK_OFFICE_NAME)]

        return res

    def _default_block_(self):
        ids = self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_TRADE_NAME)], limit=1).id
        print('---------------->', ids)
        return ids
