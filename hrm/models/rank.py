import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Ranks(models.Model):
    _name = 'hrm.ranks'
    _description = 'Cấp bậc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Tên cấp bậc', required=True)
    abbreviations = fields.Char(string='Tên viết tắt')
    active = fields.Boolean(string='Hoạt Động', default=True)

    @api.constrains('name', 'abbreviations')
    def check_duplicate(self):
        """ Kiểm tra trùng lặp dữ liệu không phân biệt hoa thường """
        for record in self:
            name = self.search([('id', '!=', record.id), ('active', 'in', (True, False))])
            for n in name:
                if n['name'].lower() == record.name.lower() and n.department == self.department:
                    raise ValidationError(constraint.DUPLICATE_RECORD % 'Cấp bậc')
                if (self.abbreviations and n['abbreviations'] and
                        n['abbreviations'].lower() == record.abbreviations.lower() and n.department == self.department):
                    raise ValidationError(constraint.DUPLICATE_RECORD % 'Tên viết tắt')

    def _default_department(self):
        if self.env.user.department_id:
            list_department = self.env['hrm.utils'].get_child_id(self.env.user.department_id,
                                                                 'hrm_departments', "superior_department")
            return [('id', 'in', list_department)]

    department_id = fields.Many2one('hrm.departments', string='Phòng/ban', tracking=True, required=True,
                                 domain=_default_department)

    def find_department(self, list_dept, records):
        for dept in list_dept:
            for rec in records:
                if dept[0] in rec.department_id.ids:
                    return rec
