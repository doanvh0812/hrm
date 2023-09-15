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
        readonly=True,
        index=True
        # ,default=lambda self: self.env['ir.sequence'].next_by_code('hrm.employee.profile')
    )

    email = fields.Char('Email công việc', required=True)
    phone_num = fields.Char('Số điện thoại di động', required=True, max_length=10)
    identifier = fields.Char('Số căn cước công dân', required=True, max_length=10)
    profile_status = fields.Selection(constraint.PROFILE_STATUS, string='Trạng thái hồ sơ', default=False)
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

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block_id.name == constraint.BLOCK_OFFICE_NAME

    def _default_block_(self):
        # Đặt giá trị mặc định cho Khối
        ids = self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_COMMERCE_NAME)]).id
        return ids

        # hiển thị mã nhân viên, nếu chọn 1 số bất kỳ tiếp tục nhảy tiếp từ số đó
        # @api.onchange('system_id')
        # def _generate_employee_code(self):
        # last_employee = self.search([], order='employee_code_new desc', limit=1)
        # last_employee_code = last_employee.employee_code_new
        # last_number = int(last_employee_code[3:])  # Trích xuất phần số
        # new_number = last_number + 1
        # print('-----------', self.get_name_systems())
        # new_employee_code = f'UNI{str(new_number).zfill(4)}'
        # return new_employee_code
        # return 'UNI0001'

    # Lọc nhân viên
    # @api.constrains('employee_code_new')
    # def check_employee_code_format(self):
    #     for record in self:
    #         if record.employee_code and not record.employee_code.startswith('UNI'):
    #             raise ValidationError(_("Mã nhân viên phải bắt đầu bằng 'UNI'."))

    #

    # @api.depends('system_id')
    # def render_code(self):
    #     for rec in self:
    #         if rec.system_id:
    #             name = str.split(rec.system_id.name, '.')[0]
    #             last_employee_code = self.env['hrm.employee.profile'].search([('employee_code_new', 'like', name)],
    #                                                                          order='employee_code_new desc',
    #                                                                          limit=1).employee_code_new
    #             if last_employee_code:
    #                 numbers = int(re.search(r'\d+', last_employee_code).group(0)) + 1
    #                 rec.employee_code_new = name + str(numbers).zfill(4)
    #                 print(rec.employee_code_new)
    #             else:
    #                 rec.employee_code_new = str.upper(name) + '0001'

    """decorator này tạo hồ sơ nhân viên, chọn cty cho hồ sơ đó 
    sẽ tự hiển thị hệ thống mà công ty đó thuộc vào"""

    """
        decorator này tạo hồ sơ nhân viên, chọn cty cho hồ sơ đó 
        sẽ tự hiển thị hệ thống mà công ty đó thuộc vào
    """

    @api.onchange('company')
    def _onchange_company(self):
        if self.company:
            company_system = self.company.system_id
            if company_system:
                self.system_id = company_system
            else:
                self.system_id = False

    """ 
        decorator này khi tạo hồ sơ nhân viên, chọn 1 hệ thống nào đó
        khi ta chọn công ty nó sẽ hiện ra tất cả những công ty có trong hệ thống đó
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('block_id') == 1:
                sequence_code = 'hrm.employee.profile'
            else:
                break
            sequence = self.env['ir.sequence'].sudo().next_by_code(sequence_code)
            vals['employee_code_new'] = sequence or _('New')
        return super(EmployeeProfile, self).create(vals_list)
