from . import constraint
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Approval_flow_object(models.Model):
    _name = "hrm.approval.flow.object"
    _description = "Luồng phê duyệt"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Tên luồng phê duyệt', required=True, tracking=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True,tracking=True)
    department_id = fields.Many2many('hrm.departments', string='Phòng/Ban', tracking=True)
    system_id = fields.Many2many('hrm.systems', string='Hệ thống', tracking=True)
    company = fields.Many2many('hrm.companies', string='Công ty con', tracking=True)
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

    @api.model
    def create(self, vals_list):
        """Decorator này để check xem khi tạo luồng phê duyệt có người duyệt hay không"""
        if vals_list['approval_flow_link'] == []:
            raise ValidationError('Không thể tạo luồng phê duyệt khi không có người phê duyệt trong luồng.')
        else:
            list_check = []
            # Đoạn này để check xem khi có ngươời duyệt thì đã được tích duyệt bắt buộc hay chưa
            for i in vals_list['approval_flow_link']:
                list_check.append(i[2]['obligatory'])
            if True not in list_check:
                raise ValidationError('Luồng phê duyệt cần có ít nhất một người bắt buộc phê duyệt.')
            else:
                return super(Approval_flow_object, self).create(vals_list)

    def write(self, vals):
        if 'approval_flow_link' in vals:
            approval_flow_link = vals['approval_flow_link']
            if approval_flow_link == []:
                raise ValidationError('Không thể tạo luồng phê duyệt khi không có người phê duyệt trong luồng.')
            else:
                list_check = []
                print(approval_flow_link)
                for item in approval_flow_link:
                    if item[2] and 'obligatory' in item[2]:
                        list_check.append(item[2]['obligatory'])
                if True not in list_check:
                    raise ValidationError('Luồng phê duyệt cần có ít nhất một người bắt buộc phê duyệt.')
        return super(Approval_flow_object, self).write(vals)

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

        def system_have_child_company(system_name):
            """
            Kiểm tra hệ thống có công ty con hay không
            Nếu có thì trả về list tên công ty con
            """
            self._cr.execute(
                r"""select * from hrm_companies where hrm_companies.system_id in 
                    (select hrm1.id from hrm_systems as hrm1 left join hrm_systems as hrm2 
	                on hrm2.parent_system = hrm1.id
	                where hrm1.name ILIKE %s);""",
                (system_name + '%',)
            )
            # kiểm tra company con của hệ thống cần tìm
            # nếu câu lệnh có kết quả trả về thì có nghĩa là hệ thống có công ty con
            list_company_id = self._cr.fetchall()
            if len(list_company_id) > 0:
                return [item[5] for item in list_company_id]
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
            system_configured = []
            for system in self.system_id:
                list_name_company = [company.name for company in self.company]
                # print("Công ty đã được chọn", list_name_company)
                # print("công ty con của hệ thống đã chọn", system.name, "là", system_have_child_company(system.name))
                # print("Hệ thống", system.name, "không được cấu hình trong bản ghi này", any(elem in system_have_child_company(system.name) for elem in list_name_company))
                # nếu hệ thống được chọn không có công ty con trong công ty đã chọn thì mới tiếp tục kiểm tra
                if not any(elem in system_have_child_company(system.name) for elem in list_name_company):
                    # tìm các cấu hình hệ thống đã có trong hệ thống được chọn
                    record_temp_configured = [(rec["name"], rec["system_id"], rec["company"]) for rec in
                                              self.env["hrm.approval.flow.object"].search([("id", "!=", self.id), ("system_id", "=", system.name)])]
                    for record in record_temp_configured:
                        list_name_company = [company.name for company in record[2]]
                        for sys in record[1]:
                            # nếu hệ thống không có công ty con trong các bản ghi khác là đã cấu hình
                            if sys.id == system.id and not any(elem in system_have_child_company(sys.name) for elem in list_name_company):
                                raise ValidationError(f"Luồng phê duyệt cho {sys.name} đã tồn tại trong cấu hình {record[0]}.")
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
                raise ValidationError(f"Luồng phê duyệt cho {self.block_id.name} đã tồn tại trong {block_configured[0].name}.")

    @api.onchange('block_id')
    def _onchange_block(self):
        self.company = self.department_id = self.system_id = False

    @api.onchange('company')
    def _onchange_company(self):
        if not self.system_id:
            self.system_id = self.company.system_id

    @api.onchange('system_id')
    def _onchange_system_id(self):
        """ decorator này khi chọn 1 hệ thống nào đó sẽ hiện ra tất cả những cty có trong hệ thống đó
            """
        selected_systems = self.system_id.ids  # Danh sách các hệ thống được chọn
        company_to_remove = self.company.filtered(lambda c: c.system_id.id not in selected_systems)
        # Bỏ chọn các công ty không thuộc các hệ thống đã chọn
        company_to_remove.write({'approval_id': [(5, 0, 0)]})

        if self.system_id:
            list_company_id = []
            list_systems_id = []
            for sys in self.system_id:
                # Lấy tất cả các hệ thống có quan hệ cha con
                self._cr.execute(
                    'select * from hrm_systems as hrm1 left join hrm_systems as hrm2 on hrm2.parent_system = hrm1.id '
                    'where hrm1.name ILIKE %s;',
                    (sys.name + '%',))
                for item in self._cr.fetchall():
                    list_systems_id.append(item[0])
                self._cr.execute(
                    'select * from hrm_companies where hrm_companies.system_id in %s;',
                    (tuple(list_systems_id),))
                for item in self._cr.fetchall():
                    list_company_id.append(item[0])

            return {'domain': {'company': [('id', 'in', list_company_id)]}}
        else:
            self.company = False
            return {'domain': {'company': []}}


class Approve(models.Model):
    _name = 'hrm.approval.flow'

    approval_id = fields.Many2one('hrm.approval.flow.object')
    step = fields.Integer(string='Bước', default=1, order='step')
    approve = fields.Many2one('res.users', string='Người phê duyệt', required=True)
    obligatory = fields.Boolean(string='Bắt buộc')
    excess_level = fields.Boolean(string='Vượt cấp')

""""""


class ApproveProfile(models.Model):
    _name = 'hrm.approval.flow.profile'
    _inherit = 'hrm.approval.flow'

    profile_id = fields.Many2one('hrm.employee.profile')
    approve_status = fields.Selection(constraint.APPROVE_STATUS, default='pending', string="Trạng thái")
    time = fields.Datetime(string="Thời gian")



