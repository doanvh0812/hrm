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
        list_user_approve = [record.approve for record in self.approval_flow_link]
        seen = set()
        for item in list_user_approve:
            if item in seen:
                raise ValidationError(f'Người dùng tên {item.name} đã có trong luồng duyệt')
            else:
                seen.add(item)
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

    @api.onchange('system_id')
    def _onchange_system_id(self):
        """ decorator này khi tạo hồ sơ nhân viên, chọn 1 hệ thống nào đó
            khi ta chọn cty nó sẽ hiện ra tất cả những cty có trong hệ thống đó
            """
        if self.system_id:
            companies = self.env['hrm.companies'].search([('system_id', '=', self.system_id.id)])
            return {'domain': {'company': [('id', 'in', companies.ids)]}}
        else:
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
