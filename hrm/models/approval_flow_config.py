from . import constraint
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Approval_flow_object(models.Model):
    _name = "hrm.approval.flow.object"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Tên luồng phê duyệt', required=True, tracking=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, tracking=True)
    department_id = fields.One2many('hrm.departments', 'approval_id', string='Phòng/Ban', tracking=True)
    system_id = fields.One2many('hrm.systems', 'approval_id', string='Hệ thống', tracking=True)
    company = fields.One2many('hrm.companies', 'approval_id', string='Công ty con', tracking=True)
    approval_flow_link = fields.One2many('hrm.approval.flow', 'approval_id', tracking=True)
    related = fields.Boolean(compute='_compute_related_')

    @api.onchange('approval_flow_link')
    def _check_duplicate_approval(self):
        list_user_approve = [record.approve for record in self.approval_flow_link]
        seen = set()
        for item in list_user_approve:
            if item in seen:
                raise ValidationError(f'Người dùng tên {item.name} đã có trong luồng duyệt')
            else:
                seen.add(item)

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block_id.name == constraint.BLOCK_OFFICE_NAME

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


class ApproveProfile(models.Model):
    _name = 'hrm.approval.flow.profile'
    _inherit = 'hrm.approval.flow'

    profile_id = fields.Many2one('hrm.employee.profile')
    approve_status = fields.Selection(constraint.APPROVE_STATUS, default='pending', string="Trạng thái")
    time = fields.Datetime(string="Thời gian")
