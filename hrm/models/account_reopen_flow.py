from odoo import fields, models, api
from . import constraint
from odoo.exceptions import ValidationError, AccessDenied


class ApprovalAccountFlow(models.Model):
    _name = 'hrm.account.reopen.flow'
    _description = 'Luồng mở lại tài khoản'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string="Tên luồng mở lại", required=True, tracking=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, tracking=True)
    check_blocks = fields.Char(default=lambda self: self.env.user.block_id)
    check_company = fields.Char(default=lambda self: self.env.user.company)

    """Lấy tất cả công ty user được cấu hình trong thiết lập"""

    def get_child_company(self):
        list_child_company = []
        if self.env.user.company:
            list_child_company = self.env['hrm.utils'].get_child_id(self.env.user.company, 'hrm_companies',
                                                                    'parent_company')
        elif not self.env.user.company and self.env.user.system_id:
            func = self.env['hrm.utils']
            for sys in self.env.user.system_id:
                list_child_company += func._system_have_child_company(sys.id)
        elif self.env.user.block_id in ['full', constraint.BLOCK_COMMERCE_NAME]:
            return list_child_company
        return [('id', 'in', list_child_company)]

    company = fields.Many2many('hrm.companies', string="Công ty", tracking=True, domain=get_child_company)
    department_id = fields.Many2many('hrm.departments', string='Phòng/Ban')
    system_id = fields.Many2many('hrm.systems', string='Hệ thống')


class ApproveAccount(models.Model):
    _name = 'hrm.approval.account'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    approval_acc = fields.Many2one('hrm.account.reopen.flow')
    step = fields.Integer(string='Bước', default=1, order='step')
    approval_person = fields.Many2one('res.users', string='Người phê duyệt', required=True, tracking=True)
    imperative = fields.Boolean(string='Bắt buộc')
    pass_level = fields.Boolean(string='Vượt cấp')

class ApprovalReopen(models.Model):
    _name = 'hrm.approval.reopen.account'
    _inherit = 'hrm.approval.account'

    account_id = fields.Many2one('hrm.employee.profile')
    approve_status = fields.Selection(constraint.APPROVE_STATUS, default='pending', string='Trạng thái')
    time = fields.Datetime(string='Thời gian')