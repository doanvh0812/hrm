import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Teams(models.Model):
    _name = 'hrm.ranks'
    _description = 'Cấp bậc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Tên cấp bậc', required=True)
    abbreviations = fields.Char(string='Tên viết tắt')
    department = fields.Many2one('hrm.departments', string='Phòng/Ban', required=True)
    active = fields.Boolean(string='Hoạt Động', default=True)
