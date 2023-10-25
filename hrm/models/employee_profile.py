from builtins import list

from odoo import models, fields, api
import re
from odoo.exceptions import ValidationError, AccessDenied
from . import constraint
from lxml import etree
import json


class EmployeeProfile(models.Model):
    _name = 'hrm.employee.profile'
    _description = 'Bảng thông tin nhân viên'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    date_receipt = fields.Date(string='Ngày được nhận chính thức', required=True,
                               default=lambda self: self._get_server_date())
    name = fields.Char(string='Họ và tên nhân sự', required=True, tracking=True)
    check_blocks = fields.Char(default=lambda self: self.env.user.block_id)
    check_company = fields.Boolean(default=lambda self: self.env.user.company)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True,
                               default=lambda self: self.default_block_profile(),
                               tracking=True)
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
    def _default_team(self):
        return [('id', '=', 0)]
    team_marketing = fields.Many2one('hrm.teams', string='Đội ngũ marketing', tracking=True, domain=_default_team)
    team_sales = fields.Many2one('hrm.teams', string='Đội ngũ bán hàng', tracking=True, domain=_default_team)

    manager_id = fields.Many2one('res.users', string='Quản lý', related="department_id.manager_id", tracking=True)
    rank_id = fields.Many2one('hrm.ranks', string='Cấp bậc')
    auto_create_acc = fields.Boolean(string='Tự động tạo tài khoản', default=True)
    reason = fields.Char(string='Lý Do Từ Chối')
    acc_id = fields.Integer(string='Id tài khoản đăng nhập')
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
    document_declaration = fields.One2many('hrm.document_declaration', 'profile_id', tracking=True)

    document_config = fields.Many2one('hrm.document.list.config', compute='compute_documents_list')
    document_list = fields.One2many(related='document_config.document_list')

    can_see_approved_record = fields.Boolean()
    can_see_button_approval = fields.Boolean()
    see_record_with_config = fields.Boolean()

    require_team_marketing = fields.Boolean(default=False)
    require_team_sale = fields.Boolean(default=False)

    apply_document_config = fields.Boolean(default=False)

    def _see_record_with_config(self):
        """Nhìn thấy tất cả bản ghi trong màn hình tạo mới hồ sơ theo cấu hình quyền"""
        self.env['hrm.employee.profile'].sudo().search([('see_record_with_config', '=', True)]).write(
            {'see_record_with_config': False})
        user = self.env.user
        # Tim tat ca cac cong ty, he thong, phong ban con
        company_config = self.env['hrm.utils'].get_child_id(user.company, 'hrm_companies', "parent_company")
        system_config = self.env['hrm.utils'].get_child_id(user.system_id, 'hrm_systems', "parent_system")
        department_config = self.env['hrm.utils'].get_child_id(user.department_id, 'hrm_departments',
                                                               "superior_department")
        block_config = user.block_id

        domain = []
        # Lay domain theo cac truong
        if not user.has_group("hrm.hrm_group_create_edit"):
            if company_config:
                domain.append(('company', 'in', company_config))
            elif system_config:
                domain.append(('system_id', 'in', system_config))
            elif department_config:
                domain.append(('department_id', 'in', department_config))
            elif block_config:
                # Neu la full thi domain = []
                if block_config != 'full':
                    block_id = self.env['hrm.blocks'].search([('name', '=', block_config)], limit=1)
                    if block_id:
                        domain.append(('block_id', '=', block_id.id))

            self.env['hrm.employee.profile'].sudo().search(domain).write({'see_record_with_config': True})

    def see_own_approved_record(self):
        """Nhìn thấy những hồ sơ user được cấu hình"""
        profile = self.env['hrm.employee.profile'].sudo().search([('state', '!=', 'draft')])
        for p in profile:
            if self.env.user.id in p.approved_link.approve.ids:
                p.can_see_approved_record = True
            else:
                p.can_see_approved_record = False

    def logic_button(self):
        """Nhìn thấy button khi đến lượt phê duyệt"""
        profile = self.env['hrm.employee.profile'].sudo().search([('state', '=', 'pending')])
        for p in profile:
            # list_id lưu id người đang đến lượt
            query = f"""
                    SELECT approve
                    FROM hrm_approval_flow_profile where profile_id = {p.id}
                    AND (
                      (step = (
                        SELECT MIN(step)
                        FROM hrm_approval_flow_profile
                        WHERE approve_status = 'pending' AND profile_id = {p.id}
                      ))
                      OR
                      (excess_level = true AND step = (
                        SELECT MIN(step)
                        FROM hrm_approval_flow_profile
                        WHERE approve_status = 'pending' AND profile_id = {p.id}
                        AND excess_level = true
                      ))
                    );
                """
            self._cr.execute(query)
            list_id = self._cr.fetchall()
            list_id_last = [i[0] for i in list_id]
            if self.env.user.id in list_id_last:
                p.can_see_button_approval = True
            else:
                p.can_see_button_approval = False

    def get_child_company(self):
        """ lấy tất cả công ty user được cấu hình trong thiết lập """
        list_child_company = []
        if self.env.user.company:
            # nếu user đc cấu hình công ty thì lấy list id công ty con của công ty đó
            list_child_company = self.env['hrm.utils'].get_child_id(self.env.user.company, 'hrm_companies',
                                                                    "parent_company")
        elif not self.env.user.company and self.env.user.system_id:
            # nếu user chỉ đc cấu hình hệ thống
            # lấy list id công ty con của hệ thống đã chọn
            func = self.env['hrm.utils']
            for sys in self.env.user.system_id:
                list_child_company += func._system_have_child_company(sys.id)
        return [('id', 'in', list_child_company)]

    company = fields.Many2one('hrm.companies', string="Công ty", tracking=True, domain=get_child_company)

    def _default_system(self):
        """ tạo bộ lọc cho trường hệ thống user có thể cấu hình """
        if not self.env.user.company.ids and self.env.user.system_id.ids:
            list_systems = self.env['hrm.utils'].get_child_id(self.env.user.system_id, 'hrm_systems', "parent_system")
            return [('id', 'in', list_systems)]
        if self.env.user.company.ids and self.env.user.block_id == constraint.BLOCK_COMMERCE_NAME:
            # nếu có công ty thì không hiển thị hệ thống
            return [('id', '=', 0)]
        return []

    system_id = fields.Many2one('hrm.systems', string="Hệ thống", tracking=True, domain=_default_system)

    def _get_server_date(self):
        # Lấy ngày hiện tại theo múi giờ của máy chủ
        server_date = fields.Datetime.now()
        return server_date

    # lý do từ chối
    reason_refusal = fields.Char(string='Lý do từ chối', index=True, ondelete='restrict', tracking=True)

    def auto_create_account_employee(self):
        # hàm tự tạo tài khoản và gán id tài khoản cho acc_id
        self.ensure_one()
        user_group = self.env.ref('hrm.hrm_group_own_edit')
        values = {
            'name': self.name,
            'login': self.email,
            'groups_id': [(6, 0, [user_group.id])],

        }
        new_user = self.env['res.users'].sudo().create(values)
        self.acc_id = new_user.id
        return {
            'name': "User Created",
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'res_id': new_user.id,
            'view_mode': 'form',
        }

    @api.model
    def create(self, vals):
        # Call the create method of the super class to create the record
        record = super(EmployeeProfile, self).create(vals)

        # Perform your custom logic here
        if record:
            # Assuming you want to call the auto_create_account_employee function
            record.auto_create_account_employee()
        return record

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(EmployeeProfile, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                           submenu=submenu)
        self._see_record_with_config()
        self.see_own_approved_record()
        self.logic_button()

        # Kiểm tra xem view_type có phải là 'form' và user_id có tồn tại
        if view_id:
            view = self.env['ir.ui.view'].browse(view_id)
            view_name = view.name
        if view_type == 'form' and not self.id and view_name == 'hrm.employee.profile.form':
            user_id = self.env.user.id
            # Kiểm tra trạng thái của bản ghi
            record_id = self.env.context.get('params', {}).get('id')
            if record_id:
                record = self.browse(record_id)
                if record.state != 'draft':
                    res['arch'] = res['arch'].replace(
                        '<form string="Tạo mới hồ sơ" create="false" edit="true" modifiers="{}">',
                        '<form string="Tạo mới hồ sơ" create="false" edit="false" modifiers="{}">')

            # Tạo một biểu thức domain mới để xác định xem nút có nên hiển thị hay không
            # Thuộc tính của trường phụ thuộc vào modifiers
            res['arch'] = res['arch'].replace(
                '<button name="action_send" string="Gửi duyệt" type="object" class="btn-primary"/>',
                f'<button name="action_send" string="Gửi duyệt" type="object" class="btn-primary" modifiers=\'{{"invisible":["|",["state","in",["pending","approved"]],["create_uid", "!=", {user_id}]]}}\'/>'
            )
            res['arch'] = res['arch'].replace(
                '<button name="action_cancel" string="Hủy" type="object"/>',
                f'<button name="action_cancel" string="Hủy" type="object" style="background-color: #FD5050; border-radius: 5px;color:#fff;" modifiers=\'{{"invisible":["|",["state","!=","pending"],["create_uid", "!=", {user_id}]]}}\'/>'
            )

            doc = etree.XML(res['arch'])

            """Đoạn code dưới để readonly các trường nếu acc_id bản ghi đó != user.id """
            # Truy cập và sửa đổi modifier của trường 'name' trong form view
            has_group_readonly = self.env.user.has_group("hrm.hrm_group_read_only")
            has_group_config = self.env.user.has_group("hrm.hrm_group_config_access")
            config_group = doc.xpath("//group")
            if config_group and not has_group_readonly:
                # nếu user login không có quyền chỉ đọc thì update lại các thuộc tính readonly
                cf = config_group[0]
                for field in cf.xpath("//field[@name]"):
                    modifiers = field.attrib.get('modifiers', '')
                    modifiers = json.loads(modifiers) if modifiers else {}
                    if field.get("name") not in ['employee_code_new', 'document_config', 'document_list']:
                        modifiers.update({'readonly': ["|", ['id', '!=', False], ['create_uid', '!=', user_id],
                                                       ['state', '!=', 'draft']]})
                    if field.get("name") in ['phone_num', 'email', 'identifier']:
                        modifiers.update({'readonly': ["|", ["id", "!=", False],
                                                       ["create_uid", "!=", user_id], ['state', '=', 'pending']]})
                    field.attrib['modifiers'] = json.dumps(modifiers)
            elif config_group and has_group_readonly:
                # nếu user login có quyền chỉ đọc thì set các field readonly
                cf = config_group[0]
                for field in cf.xpath("//field[@name]"):
                    modifiers = field.attrib.get('modifiers', '')
                    modifiers = json.loads(modifiers) if modifiers else {}
                    modifiers.update({'readonly': [[1, '=', 1]]})
                    field.attrib['modifiers'] = json.dumps(modifiers)
            # Gán lại 'arch' cho res với các thay đổi mới
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def default_block_profile(self):
        """kiểm tra điều kiện giữa khối văn phòng và thương mại"""
        if self.env.user.block_id == constraint.BLOCK_OFFICE_NAME:
            return self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_OFFICE_NAME)])
        else:
            return self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_COMMERCE_NAME)])

    @api.depends('system_id', 'block_id')
    def render_code(self):
        # Nếu khối được chọn có tên là Văn phòng chạy qua các hàm lấy mã nhân viên cuối và render ra mã tiếp
        if self.block_id.name == constraint.BLOCK_OFFICE_NAME:
            last_employee_code = self._get_last_employee_code('like', 'BH')
            self.employee_code_new = self._generate_employee_code('BH', last_employee_code)
        # Ngược lại không phải khối văn phòng
        else:
            # Nếu đã chọn hệ thống chạy qua các hàm lấy mã nhân viên cuối và render ra mã tiếp
            if self.system_id.name and not self.id.origin:
                name = str.split(self.system_id.name, '.')[0]
                last_employee_code = self._get_last_employee_code('like', name)
                self.employee_code_new = self._generate_employee_code(name, last_employee_code)
            # Ngược lại chưa chọn hệ thống ra mã là rỗng
            elif not self.employee_code_new:
                self.employee_code_new = ''

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

    @api.onchange('company')
    def _onchange_company(self):
        """decorator này tạo hồ sơ nhân viên, chọn cty cho hồ sơ đó
             sẽ tự hiển thị đội ngũ mkt và sale nó thuộc vào
        """
        self.team_marketing = self.team_sales = False
        if self.company:
            list_team_marketing = self.env['hrm.teams'].search(
                [('company', '=', self.company.id), ('type_team', '=', 'marketing')])
            list_team_sale = self.env['hrm.teams'].search(
                [('company', '=', self.company.id), ('type_team', 'in', ('sale', 'resale'))])

            return {
                'domain': {
                    'team_marketing': [('id', 'in', list_team_marketing.ids)],
                    'team_sales': [('id', 'in', list_team_sale.ids)]
                }
            }
        else:
            return {}
        self.system_id = self.company.system_id



    @api.onchange('system_id')
    def _onchange_system_id(self):
        """
            decorator này khi tạo hồ sơ nhân viên, chọn 1 hệ thống nào đó
            khi ta chọn cty nó sẽ hiện ra tất cả những cty có trong hệ thống đó
        """
        if self.system_id != self.company.system_id:  # khi đổi hệ thống thì clear company
            self.position_id = self.company = self.team_sales = self.team_marketing = False
        if self.system_id:
            if not self.env.user.company:
                func = self.env['hrm.utils']
                list_id = func._system_have_child_company(self.system_id.id)
                return {'domain': {'company': [('id', 'in', list_id)]}}
            else:
                self.company = False
                return {'domain': {'company': self.get_child_company()}}

    @api.onchange('block_id')
    def _onchange_block_id(self):
        """
            decorator này khi tạo hồ sơ nhân viên, chọn 1 vị trí nào đó
            khi ta vị trí nó sẽ hiện ra tất cả những vị trí có trong khối đó
        """
        self.position_id = self.system_id = self.company = self.team_sales = self.team_marketing = self.department_id \
            = self.manager_id = self.rank_id = False
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
        """
        Khi thay đổi vị trí sẽ check loại đội ngũ là gì.
        """
        self.require_team_marketing = self.require_team_sale = False
        if self.position_id.team_type == 'marketing':
            self.require_team_marketing = True
        elif self.position_id.team_type == "sale":
            self.require_team_sale = True


    def action_confirm(self):
        # Khi ấn button Phê duyệt sẽ chuyển từ pending sang approved
        orders = self.sudo().filtered(lambda s: s.state in ['pending'])
        id_access = self.env.user.id
        step = 0  # step đến lượt
        step_excess_level = 0  # step vượt cấp
        for rec in orders.approved_link:
            if rec.approve.id == id_access and rec.excess_level == False:
                step = rec.step
            elif rec.approve.id == id_access and rec.excess_level == True:
                step_excess_level = rec.step
        for rec in orders.approved_link:
            if (step and rec.step <= step and rec.approve_status == 'pending') or step_excess_level == rec.step:
                rec.approve_status = 'confirm'
                rec.time = fields.Datetime.now()
            elif step_excess_level and rec.step < step_excess_level and rec.approve_status == 'pending':
                # nếu là duyệt vượt cấp thì các trạng thái trước đó là pending chuyển qua confirm_excess_level
                rec.approve_status = 'confirm_excess_level'
                rec.time = fields.Datetime.now()

        message_body = f"Chờ Duyệt => Đã Phê Duyệt Tài Khoản - {self.name}"
        self.sudo().message_post(body=message_body,
                                 subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'))
        query = f"""
                SELECT MAX(step) FROM hrm_approval_flow_profile
                WHERE profile_id = {orders.id} AND obligatory = true;
                """
        self._cr.execute(query)
        max_step = self._cr.fetchone()
        state = 'pending'
        if max_step[0] <= step or max_step[0] <= step_excess_level:
            state = 'approved'
        orders.write({'state': state})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

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
        orders.write({'state': 'draft'})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_send(self):
        # Khi ấn button Gửi duyệt sẽ chuyển từ draft sang pending
        orders = self.filtered(lambda s: s.state == 'draft')
        records = self.env['hrm.approval.flow.object'].sudo().search([('block_id', '=', self.block_id.id)])
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
            self.env['hrm.approval.flow.profile'].sudo().search([('profile_id', '=', self.id)]).unlink()

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
            self.sudo().approved_link.create(approved_link_data)

            # đè base thay đổi lịch sử theo  mình
            message_body = "Đã gửi phê duyệt."
            self.message_post(body=message_body, subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'))
            orders.sudo().write({'state': 'pending'})
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        else:
            raise ValidationError("Lỗi không tìm thấy luồng!")

    def action_cancel(self):
        """Hàm này để hủy bỏ hồ sơ khi đang ở trạng thái chờ phê duyệt"""
        if self.state == "pending":
            self.sudo().write({'state': 'draft'})
            self.message_post(body="Hủy bỏ phê duyệt.",
                              subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'))

    def _default_departments(self):
        """Hàm này để hiển thị ra các phòng ban mà tài khoản có thể làm việc"""
        if self.env.user.department_id:
            func = self.env['hrm.utils']
            list_department = func.get_child_id(self.env.user.department_id, 'hrm_departments',
                                                'superior_department')
            return [('id', 'in', list_department)]

    department_id = fields.Many2one('hrm.departments', string='Phòng/Ban', tracking=True, domain=_default_departments)

    def _default_position_block(self):
        if self.env.user.block_id == constraint.BLOCK_COMMERCE_NAME and not self.department_id:
            position = self.env['hrm.position'].search([('block', '=', self.env.user.block_id)])
            return [('id', 'in', position.ids)]
        elif self.env.user.block_id == constraint.BLOCK_OFFICE_NAME and self.department_id:
            position = self.env['hrm.position'].search([('block', '=', self.env.user.block_id)])
            return [('id', 'in', position.ids)]
        else:
            return []

    position_id = fields.Many2one('hrm.position', string='Vị trí', tracking=True, domain=_default_position_block)

    def get_all_parent(self, table_name, parent, starting_id):
        query = f"""
            WITH RECURSIVE search AS (
                SELECT id, {parent} FROM {table_name} WHERE id = {starting_id}
                UNION ALL
                SELECT t.id, t.{parent} FROM {table_name} t
                INNER JOIN search ch ON t.id = ch.{parent}
            )
            SELECT id FROM search;"""
        # Lấy từ nhỏ -> lớn
        self._cr.execute(query)
        temp = self._cr.fetchall()
        result = []
        for res in temp:
            result.append(res[0])
        return result

    def find_block(self, records):
        for approved in records:
            if not approved.department_id and not approved.system_id:
                return approved

    def find_department(self, list_dept, records):
        # list_dept là danh sách id hệ thống có quan hệ cha con
        # records là danh sách bản ghi cấu hình luồng phê duyệt
        # Duyệt qua 2 danh sách
        for dept in list_dept:
            for rec in records:
                # Phòng ban có trong cấu hình luồng phê duyệt nào thì trả về bản ghi cấu hình luồng phê duyệt đó
                if dept in rec.department_id.ids:
                    return rec

    def find_block(self, records):
        for approved in records:
            if not approved.department_id and not approved.system_id:
                return approved

    def find_system(self, systems, records):
        # systems là danh sách id hệ thống có quan hệ cha con
        # records là danh sách bản ghi cấu hình luồng phê duyệt
        # Duyệt qua 2 danh sách
        for sys in systems:
            for rec in records:
                # Nếu cấu hình không có công ty
                # Hệ thống có trong cấu hình luồng phê duyệt nào thì trả về bản ghi cấu hình luồng phê duyệt đó
                if not rec.company and sys in rec.system_id.ids:
                    return rec

    def find_company(self, records, lis_company):
        for company_id in lis_company:
            for cf in records:
                if cf.company and company_id in cf.company.ids:
                    return cf

    # hàm này để hiển thị lịch sử lưu trữ
    def toggle_active(self):
        """
            Hàm này để hiển thị lịch sử lưu trữ
        """
        for record in self:
            record.active = not record.active
            if not record.active:
                record.message_post(body="Đã lưu trữ")
            else:
                record.message_post(body="Bỏ lưu trữ")

    def write(self, vals):
        # print(vals)
        if 'email' in vals:
            login = vals['email']
            user = self.env['res.users'].sudo().search([("id", "=", self.acc_id)])
            user.write({
                'login': login
            })
        return super(EmployeeProfile, self).write(vals)

    @api.constrains("name", "date_receipt", "block_id", "position_id", "    work_start_date", "employee_code_old",
                    "employee_code_new", "email", "phone_num", "identifier", "team_marketing", "team_sales",
                    "manager_id",
                    "rank_id", "auto_create_acc", "reason", "acc_id", "approved_name", "approved_link", "company",
                    "system_id")
    def check_permission(self):
        """ kiểm tra xem user có quyền cấu hình khối, hệ thống, cty, văn phòng hay không"""
        func = self.env['hrm.utils']
        if self.env.user.block_id == constraint.BLOCK_OFFICE_NAME:
            # nếu là khối văn phòng và có cấu hình phòng ban
            if self.env.user.department_id.ids:
                list_department = func.get_child_id(self.env.user.department_id, 'hrm_departments',
                                                    'superior_department')
                for depart in self.department_id:
                    if depart.id not in list_department:
                        raise AccessDenied(f"Bạn không có quyền cấu hình phòng ban {depart.name}")
            if self.block_id.name == constraint.BLOCK_COMMERCE_NAME:
                raise AccessDenied("Bạn không có quyền cấu hình khối thương mại.")
        elif self.env.user.block_id == constraint.BLOCK_COMMERCE_NAME:
            if self.env.user.company:
                list_company = func.get_child_id(self.env.user.company, 'hrm_companies', 'parent_company')
                if self.company.id not in list_company:
                    raise AccessDenied(f"Bạn không có quyền cấu hình công ty {self.company.name}")
            elif self.env.user.system_id and not self.env.user.company:
                list_system = func.get_child_id(self.env.user.system_id, 'hrm_systems', 'parent_system')
                if self.system_id.id not in list_system:
                    raise AccessDenied(f"Bạn không có quyền cấu hình hệ thống {self.system_id.name}")

    def compute_documents_list(self):
        # Tìm cấu hình dựa trên block_id
        records = self.env['hrm.document.list.config'].sudo().search([('block_id', '=', self.block_id.id)])
        if records:
            if self.block_id.name == constraint.BLOCK_COMMERCE_NAME:
                # Tìm id danh sách tài liệu theo vị trí của khối.
                document_id = self.env['hrm.document.list.config'].sudo().search(
                    [('position_id', '=', self.position_id.id), ('block_id', '=', self.block_id.id)])
                if not document_id:
                    # Không tìm được theo vị trí thì tìm theo công ty cha con
                    list_company = self.get_all_parent('hrm_companies', 'parent_company', self.company.id)
                    document_id = self.find_document_list(list_company, "company")
                    if not document_id:
                        # Không tìm được theo công ty thì tìm theo hệ thống cha con
                        list_system = self.get_all_parent('hrm_systems', 'parent_system', self.system_id.id)
                        document_id = self.find_document_list(list_company, "system_id")
            else:
                # Nếu là khối văn phòng
                # Tìm theo vị trí của phòng ban
                document_id = self.env['hrm.document.list.config'].sudo().search(
                    [('position_id', '=', self.position_id.id), ('block_id', '=', self.block_id.id),
                     ('department_id', '=', self.department_id.id)])
                if not document_id:
                    # Không tìm được vị trí thì tìm theo phòng ban cha con
                    list_dept = self.get_all_parent('hrm_departments', 'superior_department', self.department_id.id)
                    document_id = self.find_document_list(list_dept, "department_id")

            if document_id:
                # Tìm bản ghi dựa vào id tìm được
                self.document_config = document_id
            else:
                # Nếu không tìm được id nào thì tìm theo khối.
                self.document_config = self.env['hrm.document.list.config'].sudo().search(
                    [('block_id', '=', self.block_id.id), ('company', '=', False), ('system_id', '=', False),
                     ('department_id', '=', False)])
        else:
            self.document_config = False

    @api.onchange("document_declaration")
    def check_duplicate_document_declaration(self):
        if self.document_declaration:
            for doc1 in self.document_declaration:
                for doc2 in self.document_declaration:
                    if doc1.name.lower() == doc2.name.lower() and doc1.employee_id.id == doc2.employee_id.id \
                            and doc1.type_documents == doc2.type_documents and doc1.id != doc2.id:
                        raise ValidationError("Không được chọn tài liệu khai báo trùng nhau")

    @api.onchange('department_id')
    def _default_position(self):
        if self.env.user.block_id == constraint.BLOCK_OFFICE_NAME:
            if self.department_id:
                position = self.env['hrm.position'].search([('department', '=', self.department_id.id)])
                return {'domain': {'position_id': [('id', 'in', position.ids)]}}

    def find_document_list(self, object_list, colum_name):
        """Hàm này để tìm id tài liệu được cấu hình theo thứ tự ưu tiên từ con đến cha"""
        query = f"""
            DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'query_hrm_document_list_config') THEN
                        DROP FUNCTION query_hrm_document_list_config(integer[]);
                END IF;
            END $$;
            CREATE FUNCTION query_hrm_document_list_config(object_list integer[])
            RETURNS TABLE (id integer) AS $$
            DECLARE
                object_id integer;
            BEGIN
                FOREACH object_id IN ARRAY object_list
                LOOP
                    RETURN QUERY SELECT dlc.id FROM hrm_document_list_config dlc WHERE dlc.{colum_name} = object_id;
                END LOOP;
            END;
            $$ LANGUAGE plpgsql;

            SELECT * FROM query_hrm_document_list_config(ARRAY{object_list});
        """
        self._cr.execute(query)
        records = self._cr.fetchall()
        if records:
            # [0] : Để lấy phần tử đầu tiên tìm thấy và phần tử có dạng (id,) nên cần dùng thêm [0]
            return self.env['hrm.document.list.config'].sudo().search([('id', '=', records[0][0])])
        else:
            return None
