from odoo import models, fields, api, _
import re
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
    identifier = fields.Char('Số căn cước công dân', required=True, tracking=True)
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
    reason = fields.Char(string='Lý Do Từ Chối')

    # lọc duy nhất mã nhân viên
    _sql_constraints = [
        ('employee_code_uniq', 'unique(employee_code_new)', 'Mã nhân viên phải là duy nhất!'),
    ]

    active = fields.Boolean(string='Hoạt động', default=True)
    related = fields.Boolean(compute='_compute_related_')
    state = fields.Selection(constraint.STATE, default='draft', string="Trạng thái phê duyệt")

    # Các trường trong tab
    approved_link = fields.One2many('hrm.approval.flow.profile', 'profile_id', tracking=True)
    approved_name = fields.Many2one('hrm.approval.flow.object')

    def _get_server_date(self):
        # Lấy ngày hiện tại theo múi giờ của máy chủ
        server_date = fields.Datetime.now()
        return server_date

    # lý do từ chối
    reason_refusal = fields.Char(string='Lý do từ chối',
                                 index=True, ondelete='restrict', tracking=True)

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
            list_id = []
            self._cr.execute(
                'select * from hrm_systems as hrm1 left join hrm_systems as hrm2 on hrm2.parent_system = hrm1.id where hrm1.name ILIKE %s;',
                (self.system_id.name + '%',))
            for item in self._cr.fetchall():
                list_id.append(item[0])
            self._cr.execute(
                'select * from hrm_companies where hrm_companies.system_id in %s;',
                (tuple(list_id),))
            list_id.clear()
            for item in self._cr.fetchall():
                list_id.append(item[0])
            return {'domain': {'company': [('id', 'in', list_id)]}}
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

    @api.constrains("email")
    def _check_email_valid(self):
        """
            hàm kiểm tra email có hợp lệ không
        """
        for rec in self:
            if rec.email:
                if not re.match(r'^[a-z0-9]+$', rec.email):
                    raise ValidationError("Email chỉ được chứa chữ cái thường và số.")

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

        message_body = f"Chờ Duyệt => Đã Phê Duyệt Tài Khoản - {self.name}"
        self.message_post(body=message_body, subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'))

        return orders.write({
            'state': 'approved'
        })

    def action_refuse(self, reason_refusal=None):
        # Khi ấn button Từ chối sẽ chuyển từ pending sang draft
        if reason_refusal:
            # nếu có lý do từ chối thì gán lý do từ chối vào trường reason_refusal
            self.reason_refusal = reason_refusal
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
        # Khi ấn button Gửi duyệt sẽ chuyển từ draft sang pending
        orders = self.filtered(lambda s: s.state == 'draft')
        records = self.env['hrm.approval.flow.object'].search([('block_id', '=', self.block_id.id)])
        approved_id = None
        if records:
            # Nếu có ít nhất 1 cấu hình cho khối của hồ sơ đang thuộc
            if self.block_id.name == constraint.BLOCK_COMMERCE_NAME:
                # nếu là khối thương mại
                # Danh sách công ty cha con
                list_company = self.get_all_parent('hrm_companies', 'parent_company', self.company.id)
                approved_id = self.find_company(records, list_company)
                # Nếu không có cấu hình cho công ty
                if not approved_id:
                    # Danh sách hệ thống cha con
                    list_system = self.get_all_parent('hrm_systems', 'parent_system', self.system_id.id)
                    # Trả về bản ghi là cấu hình cho hệ thống
                    approved_id = self.find_system(list_system, records)
            else:
                # Nếu là khối văn phòng
                # Danh sách các phòng ban cha con
                list_dept = self.get_all_parent('hrm_departments', 'superior_department', self.department_id.id)
                # Trả về bản ghi là cấu hình cho phòng ban
                approved_id = self.find_department(list_dept, records)
            # Nếu không tìm thấy cấu hình nào từ phòng ban, hệ thống, công ty thì lấy khối
            if not approved_id:
                approved_id = self.find_block(records)
        # Nếu tìm được cấu hình
        if approved_id:
            self.approved_name = approved_id.id
            # Clear cấu hình cũ
            self.env['hrm.approval.flow.profile'].search([('profile_id', '=', self.id)]).unlink()

            # Tạo danh sách chứa giá trị dữ liệu từ approval_flow_link
            approved_link_data = approved_id.approval_flow_link.mapped(lambda rec: {
                'profile_id': self.id,
                'step': rec.step,
                'approve': rec.approve.id,
                'obligatory': rec.obligatory,
                'excess_level': rec.excess_level,
                'approve_status': 'pending',
                'time': False,
            })

            # Sử dụng phương thức create để chèn danh sách dữ liệu vào tab trạng thái
            self.approved_link.create(approved_link_data)

            # đè base thay đổi lịch sử theo  mình
            message_body = "Đã Gửi Phê Duyệt"
            self.message_post(body=message_body, subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'))
            return orders.write({'state': 'pending'})
        else:
            raise ValidationError("LỖI KHÔNG TÌM THẤY LUỒNG")

    def get_all_parent(self, table_name, parent, starting_id):
        query = f"""
            WITH RECURSIVE search AS (
                SELECT id, {parent} FROM {table_name} WHERE id = {starting_id}
                UNION ALL
                SELECT t.id, t.{parent} FROM {table_name} t
                INNER JOIN search ch ON t.id = ch.{parent}
            )
            SELECT id FROM search;
            """
        self._cr.execute(query)
        result = self._cr.fetchall()
        return result

    def find_block(self, records):
        for approved in records:
            if not approved.department_id and not approved.system_id:
                return approved

    def find_system(self, systems, records):
        # systems là danh sách id hệ thống có quan hệ cha con
        # EX : systems = [(66,) (67,),(68,)]
        # records là danh sách bản ghi cấu hình luồng phê duyệt
        # Duyệt qua 2 danh sách
        for sys in systems:
            for rec in records:
                # Nếu cấu hình không có công ty
                # Hệ thống có trong cấu hình luồng phê duyệt nào thì trả về bản ghi cấu hình luồng phê duyệt đó
                if sys[0] in rec.system_id.ids and self.find_child_company(rec):
                    return rec

    def find_department(self, list_dept, records):
        # list_dept là danh sách id hệ thống có quan hệ cha con
        # records là danh sách bản ghi cấu hình luồng phê duyệt
        # Duyệt qua 2 danh sách
        for dept in list_dept:
            for rec in records:
                # Phòng ban có trong cấu hình luồng phê duyệt nào thì trả về bản ghi cấu hình luồng phê duyệt đó
                if dept[0] in rec.department_id.ids:
                    return rec

    def find_company(self, records, lis_company):
        for company_id in lis_company:
            for cf in records:
                if company_id[0] == cf.company.id:
                    return cf

    def find_child_company(self, record):
        # record là 1 hàng trong bảng cấu hình luồng phê duyệt
        name_company_profile = self.company.name.split('.')
        if record.company:
            for comp in record.company:
                names = comp.name.split('.')
                for rec in record.system_id:
                    name_in_rec = rec.name.split('.')
                    if name_in_rec[0] == names[1] == name_company_profile[1]:
                        return False
                return True
        else:
            return True

    # hàm này để hiển thị lịch sử lưu trữ
    def toggle_active(self):
        for record in self:
            record.active = not record.active
            if not record.active:
                record.message_post(body="Đã lưu trữ")
            else:
                record.message_post(body="Bỏ lưu trữ")


