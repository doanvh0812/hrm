from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Approval_flow_object(models.Model):
    _name = "hrm.approval.flow.object"

    name = fields.Char(string='Tên luồng phê duyệt', required=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True)
    department_id = fields.One2many('hrm.departments', string='Phòng/Ban')
    system_id = fields.One2many('hrm.systems', string='Hệ thống')
    company = fields.One2many('hrm.companies', string='Công ty con')
    approval_flow_link = fields.One2many()


class Approver(models.Model):
    _name = 'hrm.approval.flow'

    step = fields.Integer(string='Bước duyệt', default=1)
    approver = fields.Many2one('res.users', string='Người phê duyệt')
    obligatory = fields.Boolean(string='Vượt cấp')
    excess_level = fields.Boolean(string='Duyệt vượt cấp')