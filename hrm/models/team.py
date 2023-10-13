import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Teams(models.Model):
    _name = 'hrm.teams'
    _description = 'Đội ngũ'

    name = fields.Char(string='Tên hiển thị')
    name_team = fields.Char(string='Tên team', required=True)
    type_team = fields.Selection(selection=constraint.SELECT_TYPE_TEAM, string='Loại hình đội ngũ', required=True)
    system_id = fields.Many2one('hrm.systems', string='Hệ thống', required=True)
    company_id = fields.Many2one('hrm.companies', string='Công ty', required=True)
    active = fields.Boolean(string='Hoạt Động', default=True)
