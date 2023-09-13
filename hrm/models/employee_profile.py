import re
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from . import constraint


class EmployeeProfile(models.Model):
    _name = 'hrm.employee.profile'
    _description = 'Bảng thông tin nhân viên'

    name = fields.Char(string='Họ và tên nhân sự', required=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, default=lambda self: self._default_block_())
    position_id = fields.Many2one('hrm.position', required=True, string='Vị trí')
    work_start_date = fields.Date(string='Ngày vào làm')
    date_receipt = fields.Date(string='Ngày được nhận chính thức', required=True, default=datetime.now())
    email = fields.Char('Email công việc', required=True)
    phone_num = fields.Integer('Số điện thoại di động', required=True, max_length=10)
    identifier = fields.Integer('Số căn cước công dân', required=True, max_length=10)
    profile_status = fields.Selection(constraint.PROFILE_STATUS, string='Trạng thái hồ sơ', default=False)
    system_id = fields.Many2one('hrm.systems', string='Hệ thống')
    company = fields.Many2one('hrm.companies', string='Công ty con')
    team_marketing = fields.Char(string='Đội ngũ marketing')
    team_sales = fields.Char(string='Đội ngũ bán hàng')
    department_id = fields.Many2one('hrm.departments', string='Phòng/Ban')
    manager_id = fields.Many2one('res.users', string='Quản lý')
    rank_id = fields.Char(string='Cấp bậc')
    auto_create_acc = fields.Boolean(string='Tự động tạo tài khoản', default=True)
    employee_code = fields.Char(
        string="Mã nhân viên",
        required=True,
        copy=False,
        index=True,
        size=7,
        default=lambda self: self._generate_employee_id(),
    )
    # lọc duy nhất mã nhân viên

    _sql_constraints = [
        ('employee_code_uniq', 'unique(employee_code)', 'Mã nhân viên phải là duy nhất!'),
    ]

    active = fields.Boolean(string='Hoạt động', default=True)
    related = fields.Boolean(compute='_compute_related_')

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            if record.block_id.name == constraint.BLOCK_OFFICE_NAME:
                record.related = True
            else:
                record.related = False

    def _default_block_(self):
        # Đặt giá trị mặc định cho Khối
        ids = self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_TRADE_NAME)]).id
        return ids

    # hiển thị mã nhân viên, nếu chọn 1 số bất kỳ tiếp tục nhảy tiếp từ số đó
    @api.model
    def _generate_employee_id(self):
        last_employee = self.search([], order='employee_code desc', limit=1)
        if last_employee:
            last_employee_id = last_employee.employee_id
            last_number = int(last_employee_id[3:])  # Trích xuất phần số
            new_number = last_number + 1
            new_employee_id = f'UNI{str(new_number).zfill(4)}'
            return new_employee_id
        return 'UNI0000'

    # Lọc nhân viên
    @api.constrains('employee_code')
    def check_employee_id_format(self):
        for record in self:
            if record.employee_id and not record.employee_id.startswith('UNI'):
                raise ValidationError(_("Mã nhân viên phải bắt đầu bằng 'UNI'."))

    """decorator này tạo hồ sơ nhân viên, chọn cty cho hồ sơ đó 
    sẽ tự hiển thị hệ thống mà công ty đó thuộc vào"""

    @api.onchange('company')
    def _onchange_company(self):
        if self.company:
            company_system = self.company.system_id
            if company_system:
                self.system_id = company_system
            else:
                self.system_id = False

    """ decorator này khi tạo hồ sơ nhân viên, chọn 1 hệ thống nào đó
    khi ta chọn cty nó sẽ hiện ra tất cả những cty có trong hệ thống đó
    """

    @api.onchange('system_id')
    def _onchange_system_id(self):
        if self.system_id:
            companies = self.env['hrm.companies'].search([('system_id', '=', self.system_id.id)])
            return {'domain': {'company': [('id', 'in', companies.ids)]}}
        else:
            return {'domain': {'company': []}}

    @api.constrains("phone_num")
    def _check_phone_valid(self):
        """
        hàm kiểm tra số điện thoại: không âm, không có ký tự, có số 0 ở đầu
        """
        for rec in self:
            if not re.match(r'^[0]\d+$', rec.phone_num):
                raise ValidationError("Số điện thoại không hợp lệ")

    @api.constrains("identifier")
    def _check_identifier_valid(self):
        """
        hàm kiểm tra số căn cước không âm, không chứa ký tự chữ
        """
        for rec in self:
            if not re.match(r'^\d+$', rec.identifier):
                raise ValidationError("Số căn cước công dân không hợp lệ")
