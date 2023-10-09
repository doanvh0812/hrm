from . import constraint
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Approval_flow_object(models.Model):
    _name = "hrm.approval.flow.object"
    _description = "Luồng phê duyệt"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Tên luồng phê duyệt', required=True, tracking=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, tracking=True
                               , default=lambda self: self.env['hrm.utils'].default_block_())
    check_blocks = fields.Char(default=lambda self: self.env.user.block_id)
    check_company = fields.Char(default=lambda self: self.env.user.company)
    approval_flow_link = fields.One2many('hrm.approval.flow', 'approval_id', tracking=True)
    related = fields.Boolean(compute='_compute_related_')

    @api.onchange('approval_flow_link')
    def _check_duplicate_approval(self):
        """decorator này để check trùng nhân viên tham gia luồng phê duyệt"""
        list_user_approve = [record.approve for record in self.approval_flow_link]
        seen = set()
        for item in list_user_approve:
            if item in seen:
                raise ValidationError(f'Người dùng tên {item.name} đã có trong luồng duyệt')
            else:
                seen.add(item)

    @api.constrains('approval_flow_link')
    def check_approval_flow_link(self):
        for record in self:
            if not record.approval_flow_link:
                raise ValidationError('Không thể tạo luồng phê duyệt khi không có người phê duyệt trong luồng.')
            else:
                list_check = []
                for item in record.approval_flow_link:
                    if item.obligatory:
                        list_check.append(True)
                if not any(list_check):
                    raise ValidationError('Luồng phê duyệt cần có ít nhất một người bắt buộc phê duyệt.')

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block_id.name == constraint.BLOCK_OFFICE_NAME

    @api.constrains("block_id", "department_id", "system_id", "company")
    def _check_duplicate_config_office(self):
        """ Kiểm tra trùng lặp cấu hình """

        def get_list_configured(data):
            """ Trả về danh sách id các đối tượng được cấu hình trong danh sách tất cả id """
            return [i.id for d in data if d for i in d]

        def check_duplicate_for_object(objects, field_name):
            """ kiểm tra trùng lặp cấu hình cho một đối tượng """
            configured_objects = [rec[field_name] for rec in
                                  self.env["hrm.approval.flow.object"].search([("id", "!=", self.id)])]
            for obj in objects:
                if obj.id in get_list_configured(configured_objects):
                    raise ValidationError(f"Luồng phê duyệt cho {obj.name} đã tồn tại.")

        def system_have_child_company(system_id):
            """
            Kiểm tra hệ thống có công ty con hay không
            Nếu có thì trả về list tên công ty con
            """
            self._cr.execute(
                r"""
                    select hrm_companies.name from hrm_companies where hrm_companies.system_id in 
                        (WITH RECURSIVE subordinates AS (
                        SELECT id, parent_system
                        FROM hrm_systems
                        WHERE id = %s
                        UNION ALL
                        SELECT t.id, t.parent_system
                        FROM hrm_systems t
                        INNER JOIN subordinates s ON t.parent_system = s.id
                        )
                SELECT id FROM subordinates);
                """, (system_id,)
            )
            # kiểm tra company con của hệ thống cần tìm
            # nếu câu lệnh có kết quả trả về thì có nghĩa là hệ thống có công ty con
            list_company = self._cr.fetchall()
            if len(list_company) > 0:
                return [com[0] for com in list_company]
            return []

        if self.department_id:
            # Nếu có chọn cấu hình phòng ban thì chỉ cần check theo phòng ban
            check_duplicate_for_object(self.department_id, "department_id")
            return
        elif self.company:
            # Nếu có chọn cấu hình công ty thì chỉ cần check theo công ty
            check_duplicate_for_object(self.company, "company")
        if self.system_id:
            # Nếu hệ thống không có công ty con thì mới đc cấu hình
            for system in self.system_id:
                list_name_company = [company.name for company in self.company]
                # nếu hệ thống được chọn không có công ty con trong công ty đã chọn thì mới tiếp tục kiểm tra
                if not any(elem in system_have_child_company(system.id) for elem in list_name_company):
                    # tìm các cấu hình hệ thống đã có trong hệ thống được chọn
                    record_temp_configured = [(rec["name"], rec["system_id"], rec["company"]) for rec in
                                              self.env["hrm.approval.flow.object"].search(
                                                  [("id", "!=", self.id), ("system_id", "=", system.name)])]
                    for record in record_temp_configured:
                        list_name_company = [company.name for company in record[2]]
                        for sys in record[1]:
                            # nếu hệ thống không có công ty con trong các bản ghi khác là đã cấu hình
                            if sys.id == system.id and not any(
                                    elem in system_have_child_company(sys.id) for elem in list_name_company):
                                raise ValidationError(
                                    f"Luồng phê duyệt cho {sys.name} đã tồn tại trong cấu hình {record[0]}.")
        elif self.block_id:
            # Kiểm tra bản ghi cấu hình cho khối văn phòng hoặc thương mại đã được cấu hình hay chưa
            # nếu có thì block_configured sẽ có kết quả sau đó raise thông báo
            block_configured = self.env["hrm.approval.flow.object"].search([
                ("id", "!=", self.id),
                ("block_id", "=", self.block_id.id),
                ("department_id", "=", False),
                ("company", "=", False),
                ("system_id", "=", False)
            ])
            if block_configured:
                raise ValidationError(
                    f"Luồng phê duyệt cho {self.block_id.name} đã tồn tại trong {block_configured[0].name}.")

    @api.onchange('block_id')
    def _onchange_block(self):
        self.company = self.department_id = self.system_id = False

    @api.onchange('company')
    def _onchange_company(self):
        if not self.system_id:
            self.system_id = self.company.system_id
        if not self.company:
            self.system_id = False

    @api.onchange('system_id')
    def _onchange_system_id(self):
        """
            Decorator này khi chọn 1 hệ thống nào đó sẽ hiện ra tất cả những cty có trong hệ thống đó
            Xoá bỏ công ty nếu trong trường hệ thống không có hệ thống công ty đó thuộc
        """
        if self.system_id:
            if not self.env.user.company:
                list_id = []
                for sys_id in self.system_id.ids:
                    list_id += self._system_have_child_company(sys_id.id)
                return {'domain': {'company': [('id', 'in', list_id)]}}
            else:
                return {'domain': {'company': self.get_child_company()}}

    def _default_departments(self):
        """Hàm này để hiển thị ra các phòng ban mà tài khoản có thể làm việc"""
        if self.env.user.department_id:
            func = self.env['hrm.utils']
            list_department = func.get_child_id(self.env.user.department_id, 'hrm_departments',
                                                'superior_department')
            return [('id', 'in', list_department)]

    department_id = fields.Many2many('hrm.departments', string='Phòng/Ban', tracking=True, domain=_default_departments)

    def _system_have_child_company(self, system_id):
        """
        Kiểm tra hệ thống có công ty con hay không
        Nếu có thì trả về list tên công ty con
        """
        self._cr.execute(
            r"""
                select hrm_companies.id from hrm_companies where hrm_companies.system_id in
                    (WITH RECURSIVE subordinates AS (
                    SELECT id, parent_system
                    FROM hrm_systems
                    WHERE id = %s
                    UNION ALL
                    SELECT t.id, t.parent_system
                    FROM hrm_systems t
                    INNER JOIN subordinates s ON t.parent_system = s.id
                    )
            SELECT id FROM subordinates);
            """, (system_id,)
        )
        # kiểm tra company con của hệ thống cần tìm
        # nếu câu lệnh có kết quả trả về thì có nghĩa là hệ thống có công ty con
        list_company = self._cr.fetchall()
        if len(list_company) > 0:
            return [com[0] for com in list_company]
        return []

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
            for sys in self.env.user.system_id:
                list_child_company += self._system_have_child_company(sys.id)
        return [('id', 'in', list_child_company)]

    company = fields.Many2many('hrm.companies', string="Công ty con", tracking=True, domain=get_child_company)

    def _default_system(self):
        """ tạo bộ lọc cho trường hệ thống user có thể cấu hình """
        if not self.env.user.company.ids and self.env.user.system_id.ids:
            list_systems = self.env['hrm.utils'].get_child_id(self.env.user.system_id, 'hrm_systems', "parent_system")
            return [('id', 'in', list_systems)]
        if self.env.user.company.ids and self.env.user.block_id == constraint.BLOCK_COMMERCE_NAME:
            # nếu có công ty thì không hiển thị hệ thống
            return [('id', '=', 0)]
        return []

    system_id = fields.Many2many('hrm.systems', string="Hệ thống", tracking=True, domain=_default_system)


class Approve(models.Model):
    _name = 'hrm.approval.flow'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    approval_id = fields.Many2one('hrm.approval.flow.object')
    step = fields.Integer(string='Bước', default=1, order='step')
    approve = fields.Many2one('res.users', string='Người phê duyệt', required=True, tracking=True)
    obligatory = fields.Boolean(string='Bắt buộc')
    excess_level = fields.Boolean(string='Vượt cấp')


class ApproveProfile(models.Model):
    _name = 'hrm.approval.flow.profile'
    _inherit = 'hrm.approval.flow'

    profile_id = fields.Many2one('hrm.employee.profile')
    approve_status = fields.Selection(constraint.APPROVE_STATUS, default='pending', string="Trạng thái")
    time = fields.Datetime(string="Thời gian")
