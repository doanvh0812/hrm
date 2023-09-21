import re, pytz
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class EmployeeProfile(models.Model):
    _name = 'hrm.employee.profile'
    _description = 'Bảng thông tin nhân viên'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    date_receipt = fields.Date(string='Ngày được nhận chính thức', required=True,
                               default=lambda self: self._get_server_date())
    name = fields.Char(string='Họ và tên nhân sự', required=True, tracking=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, default=lambda self: self._default_block_(),
                               tracking=True)
    position_id = fields.Many2one('hrm.position', required=True, string='Vị trí', tracking=True)
    work_start_date = fields.Date(string='Ngày vào làm', tracking=True)
    employee_code_old = fields.Char(string='Mã nhân viên cũ')
    employee_code_new = fields.Char(
        string="Mã nhân viên mới",
        compute='render_code',
        store=True
    )

    email = fields.Char('Email công việc', required=True, tracking=True)
    phone_num = fields.Char('Số điện thoại di động', required=True, tracking=True)
    identifier = fields.Char('Số căn cước công dân', required=True)
    profile_status = fields.Selection(constraint.PROFILE_STATUS, string='Trạng thái hồ sơ', default='incomplete',
                                      tracking=True)
    system_id = fields.Many2one('hrm.systems', string='Hệ thống', tracking=True)
    company = fields.Many2one('hrm.companies', string='Công ty con', tracking=True)
    team_marketing = fields.Char(string='Đội ngũ marketing', tracking=True)
    team_sales = fields.Char(string='Đội ngũ bán hàng', tracking=True)
    department_id = fields.Many2one('hrm.departments', string='Phòng/Ban', tracking=True)
    manager_id = fields.Many2one('res.users', string='Quản lý', tracking=True)
    rank_id = fields.Char(string='Cấp bậc')
    auto_create_acc = fields.Boolean(string='Tự động tạo tài khoản', default=True)

    # lọc duy nhất mã nhân viên
    _sql_constraints = [
        ('employee_code_uniq', 'unique(employee_code_new)', 'Mã nhân viên phải là duy nhất!'),
    ]

    active = fields.Boolean(string='Hoạt động', default=True)
    related = fields.Boolean(compute='_compute_related_')
    state = fields.Selection(constraint.STATE, default='draft')

    # Các trường trong tab
    approved_link = fields.One2many('hrm.approval.flow.profile', 'profile_id')
    approved_name = fields.Many2one('hrm.approval.flow.object')

    def _get_server_date(self):
        # Lấy ngày hiện tại theo múi giờ của máy chủ
        server_date = fields.Datetime.now()
        return server_date

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
                if record.system_id.name:
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
        domain = [('employee_code_new', operator, name), ('active', 'in', (True, False))]
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

    @api.onchange('company')
    def _onchange_company(self):
        """decorator này tạo hồ sơ nhân viên, chọn cty cho hồ sơ đó
             sẽ tự hiển thị hệ thống mà công ty đó thuộc vào"""
        if self.company:
            company_system = self.company.system_id
            if company_system:
                self.system_id = company_system
            else:
                self.system_id = False

    @api.onchange('system_id')
    def _onchange_system_id(self):
        """ decorator này khi tạo hồ sơ nhân viên, chọn 1 hệ thống nào đó
            khi ta chọn cty nó sẽ hiện ra tất cả những cty có trong hệ thống đó
            """
        # clear dữ liệu
        if self.system_id != self.company.system_id:
            self.position_id = self.company = self.team_sales = self.team_marketing = False

        if self.system_id:
            list_systems_id = []
            self._cr.execute(
                'select * from hrm_systems as hrm1 left join hrm_systems as hrm2 on hrm2.parent_system = hrm1.id where hrm1.name ILIKE %s;',
                (self.system_id.name + '%',))
            for item in self._cr.fetchall():
                list_systems_id.append(item[0])
            self._cr.execute(
                'select * from hrm_companies where hrm_companies.system_id in %s;',
                (tuple(list_systems_id),))
            list_systems_id.clear()
            for item in self._cr.fetchall():
                list_systems_id.append(item[0])
            return {'domain': {'company': [('id', 'in', list_systems_id)]}}
        else:
            return {'domain': {'company': []}}

    @api.onchange('block_id')
    def _onchange_block_id(self):
        """
            decorator này khi tạo hồ sơ nhân viên, chọn 1 vị trí nào đó
            khi ta vị trí nó sẽ hiện ra tất cả những vị trí có trong khối đó
        """
        self.position_id = self.system_id = self.company = self.team_sales = self.team_marketing = self.department_id = self.manager_id = self.rank_id = False
        if self.block_id:
            position = self.env['hrm.position'].search([('block', '=', self.block_id.name)])
            return {'domain': {'position_id': [('id', 'in', position.ids)]}}
        else:
            return {'domain': {'position_id': []}}

    @api.constrains("phone_num")
    def _check_phone_valid(self):
        """
            hàm kiểm tra số điện thoại: không âm, không có ký tự, có số 0 ở đầu
        """
        for rec in self:
            if rec.phone_num:
                if not re.match(r'^\d+$', rec.phone_num):
                    raise ValidationError(constraint.ERROR_PHONE)

    @api.constrains("identifier")
    def _check_identifier_valid(self):
        """
        hàm kiểm tra số căn cước không âm, không chứa ký tự chữ
        """
        for rec in self:
            if rec.identifier:
                if not re.match(r'^\d+$', rec.identifier):
                    raise ValidationError("Số căn cước công dân không hợp lệ")

    @api.onchange('email')
    def validate_mail(self):
        # Hàm kiểm tra định dạng email
        if self.email:
            match = re.match(r'^[\w.-]+@[\w.-]+\.\w+$', self.email)
            if not match:
                raise ValidationError('Email không hợp lệ')

    @api.constrains("name")
    def _check_valid_name(self):
        """
            kiểm tra trường name không có ký tự đặc biệt.
            \W là các ký tự ko phải là chữ, dấu cách, _
        """
        for rec in self:
            if rec.name:
                if re.search(r"[\W]+", rec.name.replace(" ", "")) or "_" in rec.name:
                    raise ValidationError(constraint.ERROR_NAME % '')

    @api.onchange('position_id')
    def onchange_position_id(self):
        # Khi thay đổi khối của vị trí đang chọn trong màn hình popup thì trường position_id = null
        if self.position_id.block != self.block_id.name:
            self.position_id = ''

    def action_confirm(self):
        # Khi ấn button Phê duyệt sẽ chuyển từ pending sang approved
        orders = self.filtered(lambda s: s.state in ['pending'])
        id_access = self.env.user.id
        for rec in orders.approved_link:
            if rec.approve.id == id_access:
                rec.approve_status = 'confirm'
                rec.time = fields.Datetime.now()

        return orders.write({
            'state': 'approved'
        })

    def action_refuse(self):
        # Khi ấn button Từ chối sẽ chuyển từ pending sang draft
        orders = self.filtered(lambda s: s.state in ['pending'])
        # Lấy id người đăng nhập
        id_access = self.env.user.id
        # Duyệt qua bản ghi trong luồng (là những người được duyệt)
        for rec in orders.approved_link:
            # Tìm người trong luồng có id = người đang đăng nhập
            # Thay trạng thái của người đó trong bản ghi thành refuse
            if rec.approve.id == id_access:
                rec.approve_status = 'refuse'
                rec.time = fields.Datetime.now()

        return orders.write({
            'state': 'draft'
        })

    def action_send(self):
        orders = self.filtered(lambda s: s.state == 'draft')

        records = self.env['hrm.approval.flow.object'].search([])
        if self.block_id.name == constraint.BLOCK_COMMERCE_NAME:
            name_system_configured = []
            for rec in records:
                for sys in rec.system_id:
                    if sys:
                        name_system_configured.append(sys.name_system)

            system_last = self.find_common_elements(self.system_id.name.split('.'), name_system_configured)

            lis_company = self.find_company_hierarchy(self.company.id)

            approved_id = self.find_last_company(records, lis_company)
            if not approved_id:
                approved_id = self.find_last_system(records, system_last)
                if not approved_id:
                    approved_id = self.find_block(records, self.block_id)

            if not approved_id:
                raise ValidationError("LỖI KHÔNG TÌM THẤY LUỒNG")
            self.approved_name = approved_id.id

        self.env['hrm.approval.flow.profile'].search([('profile_id', '=', self.id)]).unlink()
        for rec in approved_id.approval_flow_link:
            self.approved_link.create({
                'profile_id': self.id,
                'step': rec.step,
                'approve': rec.approve.id,
                'obligatory': rec.obligatory,
                'excess_level': rec.excess_level,
                'approve_status': 'pending',
                'time': False,
            })

        return orders.write({'state': 'pending'})

    def find_common_elements(self, list1, list2):
        common_elements = set(list1) & set(list2)
        if common_elements:
            return common_elements.pop()
        return None

    def find_company_hierarchy(self, company_id):
        query = """
            WITH RECURSIVE CompanyHierarchy AS (
                SELECT id, parent_company FROM hrm_companies WHERE id = %s
                UNION ALL
                SELECT c.id, c.parent_company FROM hrm_companies c
                INNER JOIN CompanyHierarchy ch ON c.id = ch.parent_company
            )
            SELECT id FROM CompanyHierarchy;
        """
        self._cr.execute(query, (company_id,))
        return self._cr.fetchall()

    def find_last_company(self, records, lis_company):
        for company_id in lis_company:
            for cf in records:
                if company_id[0] == cf.company.id:
                    return cf

    def find_last_system(self, records, system_last):
        for rec in records:
            if not rec.company:
                list_name = [i.name_system for i in rec.system_id]
                if system_last in list_name:
                    return rec

    def find_block(self, records, block_id):
        approved_list = self.env['hrm.approval.flow.object'].search([('block_id', '=', block_id.id)])
        for approved in approved_list:
            if not approved.department_id and not approved.system_id:
                return approved

    # hàm này để hiển thị lịch sử lưu trữ
    def toggle_active(self):
        for record in self:
            record.active = not record.active
            if not record.active:
                record.message_post(body="Đã lưu trữ")
            else:
                record.message_post(body="Bỏ lưu trữ")
