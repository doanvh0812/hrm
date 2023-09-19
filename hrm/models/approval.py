from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Approval(models.Model):
    _name = 'hrm.approval'
    _inherit = 'hrm.employee.profile'

    status = fields.Selection([('draft', 'Nháp'), ('pending', 'Chờ duyệt')])
