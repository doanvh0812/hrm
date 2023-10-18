import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import constraint


class Teams(models.Model):
    _name = 'hrm.teams'
    _description = 'Đội ngũ'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Tên hiển thị', compute='_compute_name_team', store=True)
    team_name = fields.Char(string='Tên team', required=True)
    type_team = fields.Selection(selection=constraint.SELECT_TYPE_TEAM, string='Loại hình đội ngũ', required=True)
    system_id = fields.Many2one('hrm.systems', string='Hệ thống', required=True)
    active = fields.Boolean(string='Hoạt Động', default=True)
    change_system_id = fields.Many2one('hrm.systems', string="Hệ thống", default=False)

    @api.onchange('company_id')
    def _onchange_company(self):
        """ decorator này  chọn cty
            sẽ tự hiển thị hệ thống mà công ty đó thuộc vào
        """
        company_system = self.company_id.system_id
        if company_system:
            self.system_id = company_system
        elif self.change_system_id:
            self.system_id = self.change_system_id
        else:
            self.system_id = False

    @api.constrains("team_name")
    def _check_valid_name(self):
        """
            kiểm tra trường name không có ký tự đặc biệt.
            \W là các ký tự ko phải là chữ, dấu cách _
        """
        for rec in self:
            if rec.team_name:
                if re.search(r"[\W]+", rec.team_name.replace(" ", "")) or "_" in rec.team_name:
                    raise ValidationError(constraint.ERROR_NAME % 'Đội Ngũ')

    @api.depends('team_name', 'company_id')
    def _compute_name_team(self):

        for rec in self:
            name_prefix = ""

            if rec.type_team == 'marketing':
                name_prefix = 'TeamMKT'
            elif rec.type_team == 'sale':
                name_prefix = 'TeamSale'
            elif rec.type_team == 'resale':
                name_prefix = 'TeamUCA'

            team_name = rec.team_name and rec.team_name or ''
            name_company = rec.company_id and rec.company_id.name or ''

            name_parts = [part for part in [name_prefix, team_name, name_company] if part]
            rec.name = '_'.join(name_parts)

    @api.constrains('name', 'type_company')
    def _check_name_combination(self):
        # Kiểm tra sự trùng lặp dựa trên kết hợp của name và type_company
        for record in self:
            name = self.search([('id', '!=', record.id), ('active', 'in', (True, False))])
            for n in name:
                if n['name'].lower() == record.name.lower() and n.type_team == self.type_team:
                    raise ValidationError(constraint.DUPLICATE_RECORD % "Đội ngũ")

    def toggle_active(self):
        """hàm này để hiển thị lịch sử lưu trữ"""
        for record in self:
            record.active = not record.active
            if not record.active:
                record.message_post(body="Đã lưu trữ")
            else:
                record.message_post(body="Bỏ lưu trữ")

    def _system_have_child_company(self, system_id):
        """
        Kiểm tra hệ thống có công ty con hay không
        Nếu có thì trả về list tên công ty con
        """
        self._cr.execute(
            r"""
                select hrm_companies.id from hrm_companies where hrm_companies.system_id in 
                    (WITH RECURSIVE subordinates AS (
                    SELECT id, parent_system
                    FROM hrm_systems
                    WHERE id = %s
                    UNION ALL
                    SELECT t.id, t.parent_system
                    FROM hrm_systems t
                    INNER JOIN subordinates s ON t.parent_system = s.id
                    )
            SELECT id FROM subordinates);
            """, (system_id,)
        )
        # kiểm tra company con của hệ thống cần tìm
        # nếu câu lệnh có kết quả trả về thì có nghĩa là hệ thống có công ty con
        list_company = self._cr.fetchall()
        if len(list_company) > 0:
            return [com[0] for com in list_company]
        return []

    def get_child_company(self):
        """ lấy tất cả công ty user được cấu hình trong thiết lập """
        list_child_company = []
        if self.env.user.company:
            # nếu user đc cấu hình công ty thì lấy list id công ty con của công ty đó
            list_child_company = self.env['hrm.utils'].get_child_id(self.env.user.company, 'hrm_companies',
                                                                    "parent_company")
        elif not self.env.user.company and self.env.user.system_id:
            # nếu user chỉ đc cấu hình hệ thống
            # lấy list id công ty con của hệ thống đã chọn
            for sys in self.env.user.system_id:
                list_child_company += self._system_have_child_company(sys.id)
        elif not self.env.user.system_id or self.env.user.block == 'full':
            # nếu k được cấu hình công ty và hệ thống thì sẽ lấy tất cả công ty
            list_child_company = self.env['hrm.companies'].search([]).ids
        return [('id', 'in', list_child_company)]

    company_id = fields.Many2one('hrm.companies', string='Công ty', required=True, domain=get_child_company)
