from odoo import models, fields, api
from . import constraint


class Users(models.Model):
    _inherit = 'res.users'

    block_id = fields.Selection(selection=[
        (constraint.BLOCK_OFFICE_NAME, constraint.BLOCK_OFFICE_NAME),
        (constraint.BLOCK_COMMERCE_NAME, constraint.BLOCK_COMMERCE_NAME)], string="Khối", required=True)
    department_id = fields.Many2many('hrm.departments', string='Phòng/Ban', tracking=True)
    system_id = fields.Many2many('hrm.systems', string='Hệ thống', tracking=True)
    company_id = fields.Many2many('hrm.companies', string='Công ty', tracking=True)
