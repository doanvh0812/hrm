from odoo import models, fields, api, _
from . import constraint
from odoo.exceptions import ValidationError


class EmployeeProfile(models.Model):
    _name = 'hrm.employee.profile'
    _description = 'Bảng thông tin nhân viên'

    name = fields.Char(string='Họ và tên nhân sự', required=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, default=lambda self: self._default_block_())
    # position_id = fields.Many2one('hrm.position', required=True) chưa có model position
    work_start_date = fields.Date(string='Ngày vào làm')
    date_receipt = fields.Date(string='Ngày được nhận chính thức', required=True)
    employee_code = fields.Char(string='Mã nhân viên', required=True)
    email = fields.Char('Email công việc', required=True)
    phone_num = fields.Integer('Số điện thoại di động', required=True, max_length=10)
    identifier = fields.Integer('Số căn cước công dân', required=True, max_length=10)
    profile_status = fields.Selection(constraint.PROFILE_STATUS, string='Trạng thái hồ sơ', default=False)
    # system_id = fields.Many2one('hrm.systems', string='Hệ thống')
    # company = chưa có model systems
    # team_marketing = chưa có model position
    # team_sales = chưa có model position
    # department_id = chưa có model department
    manager_id = fields.Many2one('res.users', string='Quản lý')
    # rank_id = chưa có model rank
    auto_create_acc = fields.Boolean(string='Tự động tạo tài khoản')
    # employee_id = fields.Char(string="ID", copy=False, index=True)
    employee_id = fields.Char(
        string="Mã nhân viên",
        required=True,
        copy=False,
        index=True,
        size=7,
        default=lambda self: self._generate_employee_id(),
    )
    # lọc duy nhất mã nhân viên

    _sql_constraints = [
        ('employee_id_uniq', 'unique(employee_id)', 'Mã nhân viên phải là duy nhất!'),
    ]

    def _default_block_(self):
        ids = self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_TRADE_NAME)], limit=1).id
        print('---------------->', ids)
        return ids

# hiển thị mã nhân viên, nếu chọn 1 số bất kỳ tiếp tục nhảy tiếp từ số đó
    @api.model
    def _generate_employee_id(self):
        last_employee = self.search([], order='employee_id desc', limit=1)
        if last_employee:
            last_employee_id = last_employee.employee_id
            last_number = int(last_employee_id[3:])  # Trích xuất phần số
            new_number = last_number + 1
            new_employee_id = f'UNI{str(new_number).zfill(4)}'
            return new_employee_id
        return 'UNI0000'

   # Lọc nhân viên
    @api.constrains('employee_id')
    def check_employee_id_format(self):
        for record in self:
            if record.employee_id and not record.employee_id.startswith('UNI'):
                raise ValidationError(_("Mã nhân viên phải bắt đầu bằng 'UNI'."))
