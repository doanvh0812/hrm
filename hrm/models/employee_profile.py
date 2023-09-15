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

    employee_code_old = fields.Char(string='Mã nhân viên cũ')
    employee_code_new = fields.Char(
        string="Mã nhân viên mới",
        compute='render_code',
        store=True
    )

    email = fields.Char('Email công việc', required=True)
    phone_num = fields.Char('Số điện thoại di động', required=True)
    identifier = fields.Char('Số căn cước công dân', required=True)
    profile_status = fields.Selection(constraint.PROFILE_STATUS, string='Trạng thái hồ sơ', default='incomplete')
    system_id = fields.Many2one('hrm.systems', string='Hệ thống')
    company = fields.Many2one('hrm.companies', string='Công ty con')
    team_marketing = fields.Char(string='Đội ngũ marketing')
    team_sales = fields.Char(string='Đội ngũ bán hàng')
    department_id = fields.Many2one('hrm.departments', string='Phòng/Ban')
    manager_id = fields.Many2one('res.users', string='Quản lý')
    rank_id = fields.Char(string='Cấp bậc')
    auto_create_acc = fields.Boolean(string='Tự động tạo tài khoản', default=True)

    # lọc duy nhất mã nhân viên
    _sql_constraints = [
        ('employee_code_uniq', 'unique(employee_code_new)', 'Mã nhân viên phải là duy nhất!'),
    ]

    active = fields.Boolean(string='Hoạt động', default=True)
    related = fields.Boolean(compute='_compute_related_')

    @api.depends('system_id', 'block_id')
    def render_code(self):
        # Chạy qua tất cả bản ghi
        for record in self:
            # Nếu khối được chọn có tên là Văn phòng chạy qua các hàm lấy mã nhân viên cuối và render ra mã tiếp
            if record.block_id.name == constraint.BLOCK_OFFICE_NAME:
                last_employee_code = self._get_last_employee_code('like', 'BH')
                record.employee_code_new = self._generate_employee_code('BH', last_employee_code)
            # Ngược lại không phải khối văn phòng
            else:
                # Nếu đã chọn hệ thống chạy qua các hàm lấy mã nhân viên cuối và render ra mã tiếp
                if record.system_id:
                    name = str.split(record.system_id.name, '.')[0]
                    last_employee_code = self._get_last_employee_code('like', name)
                    record.employee_code_new = self._generate_employee_code(name, last_employee_code)
                # Ngược lại chưa chọn hệ thống ra mã là rỗng
                else:
                    record.employee_code_new = ''

    @api.model
    def _get_last_employee_code(self, operator, name):
        """
            Hàm lấy mã nhân viên cuối cùng mà nó trùng với mã hệ thống đang chọn
            query dữ liệu từ dưới lên gặp mã nào trùng thì lấy và kết thúc query
            Kết quả cuối cùng return về mã nhân viên nếu có hoặc None nếu không thấy
        """
        domain = [('employee_code_new', operator, name)]
        order = 'employee_code_new desc'
        limit = 1
        last_employee = self.env['hrm.employee.profile'].search(domain, order=order, limit=limit)
        if last_employee:
            return last_employee.employee_code_new
        return None

    @api.model
    def _generate_employee_code(self, prefix, last_employee_code):
        """
            Hàm nối chuỗi để lấy mã nhân viên theo logic
        """
        if last_employee_code:
            numbers = int(re.search(r'\d+', last_employee_code).group(0)) + 1
            return f"{prefix}{str(numbers).zfill(4)}"
        else:
            return f"{prefix}0001"

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block_id.name == constraint.BLOCK_OFFICE_NAME

    def _default_block_(self):
        # Đặt giá trị mặc định cho Khối
        ids = self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_COMMERCE_NAME)]).id
        return ids

    """decorator này tạo hồ sơ nhân viên, chọn cty cho hồ sơ đó 
    sẽ tự hiển thị hệ thống mà công ty đó thuộc vào"""

    """
        decorator này tạo hồ sơ nhân viên, chọn cty cho hồ sơ đó 
        sẽ tự hiển thị hệ thống mà công ty đó thuộc vào
    """

    @api.onchange('company')
    def _onchange_company(self):
        """
            decorator này tạo hồ sơ nhân viên, chọn cty cho hồ sơ đó
            sẽ tự hiển thị hệ thống mà công ty đó thuộc vào
        """
        if self.company:
            company_system = self.company.system_id
            if company_system:
                self.system_id = company_system
            else:
                self.system_id = False

    @api.onchange('system_id')
    def _onchange_system_id(self):
        """
            decorator này khi tạo hồ sơ nhân viên, chọn 1 hệ thống nào đó
            khi ta chọn công ty nó sẽ hiện ra tất cả những công ty có trong hệ thống đó
        """
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
            if rec.phone_num:
                if not re.match(r'^[0]\d+$', rec.phone_num):
                    raise ValidationError("Số điện thoại không hợp lệ")

    @api.constrains("identifier")
    def _check_identifier_valid(self):
        """
        hàm kiểm tra số căn cước không âm, không chứa ký tự chữ
        """
        for rec in self:
            if rec.identifier:
                if not re.match(r'^\d+$', rec.identifier):
                    raise ValidationError("Số căn cước công dân không hợp lệ")

    @api.onchange('system_id')
    def print_system(self):
        for record in self:
            if record.system_id.parent_system:
                @api.depends('system_id')
                def render_code(self):
                    for rec in self:
                        if rec.system_id:
                            name = str.split(rec.system_id.name, '.')[0]
                            last_employee_code = self.env['hrm.employee.profile'].search(
                                [('employee_code_new', 'like', name)],
                                order='employee_code_new desc',
                                limit=1).employee_code_new
                            if last_employee_code:
                                numbers = int(re.search(r'\d+', last_employee_code).group(0)) + 1
                                rec.employee_code_new = name + str(numbers).zfill(4)
                                print(rec.employee_code_new)
                            else:
                                rec.employee_code_new = str.upper(name) + '0001'
            else:
                print(record.system_id.name_system)

