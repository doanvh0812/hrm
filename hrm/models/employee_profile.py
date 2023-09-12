from odoo import models, fields, api
from . import constraint


class EmployeeProfile(models.Model):
    _name = 'hrm.employee.profile'
    _description = 'Bảng thông tin nhân viên'

    name = fields.Char(string='Họ và tên nhân sự', required=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, default=lambda self: self._default_block_())
    position_id = fields.Many2one('hrm.position', required=True, string='Vị trí')
    work_start_date = fields.Date(string='Ngày vào làm')
    date_receipt = fields.Date(string='Ngày được nhận chính thức', required=True)
    employee_code = fields.Char(string='Mã nhân viên', required=True)
    email = fields.Char('Email công việc', required=True)
    phone_num = fields.Integer('Số điện thoại di động', required=True)
    identifier = fields.Integer('Số căn cước công dân', required=True)
    profile_status = fields.Selection(constraint.PROFILE_STATUS, string='Trạng thái hồ sơ', default=False)
    system_id = fields.Many2one('hrm.systems', string='Hệ thống')
    company = fields.Many2one('hrm.systems', string='Công ty con')
    team_marketing = fields.Char(string='Đội ngũ marketing')
    team_sales = fields.Char(string='Đội ngũ bán hàng')
    department_id = fields.Many2one('hrm.departments', string='Phòng/Ban')
    manager_id = fields.Many2one('res.users', string='Quản lý')
    rank_id = fields.Char(string='Cấp bậc')
    auto_create_acc = fields.Boolean(string='Tự động tạo tài khoản', default=True)

    related = fields.Boolean()

    @api.onchange('block_id')
    def _compute_related_field(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            if record.block_id.name == constraint.BLOCK_OFFICE_NAME:
                record.related = True
            else:
                record.related = False

    def _default_block_(self):
        # Đặt giá trị mặc định cho Khối
        ids = self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_TRADE_NAME)], limit=1).id
        return ids
