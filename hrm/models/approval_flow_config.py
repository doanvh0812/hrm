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

    # lost_reason = fields.Text(string='Lý do từ chối', tracking=True)

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

    # def action_open_lost_reason_popup(self):
    #     self.ensure_one()
    #     return {
    #         'name': ('Lý do từ chối'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'hrm.approval.flow.object',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('hrm.view_blocks_form').id,
    #         'target': 'new',
    #         'context': {
    #             'default_lost_reason': self.lost_reason,  # Truyền giá trị hiện tại của lý do từ chối (nếu có)
    #         },
    #     }
    #
    # def action_save_lost_reason(self):
    #     self.ensure_one()
    #     # Lưu lý do từ chối vào trường 'lost_reason'
    #     self.write({'lost_reason': self.lost_reason})
    #     return {'type': 'ir.actions.act_window_close'}

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
                self._cr.execute(
                    'select * from hrm_systems as hrm1 left join hrm_systems as hrm2 on hrm2.parent_system = hrm1.id where hrm1.name ILIKE %s;',
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
