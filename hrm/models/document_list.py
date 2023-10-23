from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessDenied
from . import constraint


class DocumentListConfig(models.Model):
    _name = 'hrm.document.list.config'
    _description = 'Cấu hình danh sách tài liệu'

    name = fields.Char(string='Tên hiển thị', required=True)
    block_id = fields.Many2one('hrm.blocks', string='Khối', required=True, default=lambda self: self._default_block(),
                               tracking=True)
    check_blocks = fields.Char(default=lambda self: self.env.user.block_id)
    check_company = fields.Char(default=lambda self: self.env.user.company)
    document_list = fields.One2many('hrm.document.list', 'document_id', string='Danh sách tài liệu')
    related = fields.Boolean(compute='_compute_related_')
    can_see_approved_record = fields.Boolean()
    can_see_button_approval = fields.Boolean()
    see_record_with_config = fields.Boolean()

    def _see_record_with_config(self):
        """Nhìn thấy tất cả bản ghi trong màn hình tạo mới hồ sơ theo cấu hình quyền"""
        self.env['hrm.document.list.config'].sudo().search([('see_record_with_config', '=', True)]).write(
            {'see_record_with_config': False})
        user = self.env.user
        # Tim tat ca cac cong ty, he thong, phong ban con
        company_config = self.env['hrm.utils'].get_child_id(user.company, 'hrm_companies', "parent_company")
        system_config = self.env['hrm.utils'].get_child_id(user.system_id, 'hrm_systems', "parent_system")
        department_config = self.env['hrm.utils'].get_child_id(user.department_id, 'hrm_departments',
                                                               "superior_department")
        block_config = user.block_id

        domain = []
        # Lay domain theo cac truong
        if not user.has_group("hrm.hrm_group_create_edit"):
            if company_config:
                domain.append(('company', 'in', company_config))
            elif system_config:
                domain.append(('system_id', 'in', system_config))
            elif department_config:
                domain.append(('department_id', 'in', department_config))
            elif block_config:
                # Neu la full thi domain = []
                if block_config != 'full':
                    block_id = self.env['hrm.blocks'].search([('name', '=', block_config)], limit=1)
                    if block_id:
                        domain.append(('block_id', '=', block_id.id))

            self.env['hrm.document.list.config'].sudo().search(domain).write({'see_record_with_config': True})

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
        list_child_company = []
        if self.env.user.company:
            list_child_company = self.env['hrm.utils'].get_child_id(self.env.user.company, 'hrm_companies',
                                                                    "parent_company")
        elif not self.env.user.company and self.env.user.system_id:
            for sys in self.env.user.system_id:
                list_child_company += self._system_have_child_company(sys.id)
        return [('id', 'in', list_child_company)]

    company = fields.Many2one('hrm.companies', string="Công ty", tracking=True, domain=get_child_company)

    def _default_system(self):
        if not self.env.user.company.ids and self.env.user.system_id.ids:
            list_systems = self.env['hrm.utils'].get_child_id(self.env.user.system_id, 'hrm_systems', 'parent_system')
            return [('id', 'in', list_systems)]
        if self.env.user.company.ids and self.env.user.block_id == constraint.BLOCK_COMMERCE_NAME:
            return [('id', '=', 0)]
        return []

    system_id = fields.Many2one('hrm.systems', string="Hệ thống", tracking=True, domain=_default_system)

    def _default_department(self):
        if self.env.user.department_id.id:
            list_department = self.env['hrm.utils'].get_child_id(self.env.user.department_id,
                                                                 'hrm_departments', "superior_department")
            return [('id', 'in', list_department)]

    department_id = fields.Many2one('hrm.departments', string='Phòng ban', tracking=True, domain=_default_department)

    def _default_position_block(self):
        if self.env.user.block_id == constraint.BLOCK_COMMERCE_NAME and not self.department_id:
            position = self.env['hrm.position'].search([('block', '=', self.env.user.block_id)])
            return [('id', 'in', position.ids)]
        elif self.env.user.block_id == constraint.BLOCK_OFFICE_NAME and self.department_id:
            position = self.env['hrm.position'].search([('block', '=', self.env.user.block_id)])
            return [('id', 'in', position.ids)]
        else:
            return []

    position_id = fields.Many2one('hrm.position', string='Vị trí', domain=_default_position_block)

    def _default_block(self):
        if self.env.user.block_id == constraint.BLOCK_OFFICE_NAME:
            return self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_OFFICE_NAME)])
        else:
            return self.env['hrm.blocks'].search([('name', '=', constraint.BLOCK_COMMERCE_NAME)])

    @api.depends('block_id')
    def _compute_related_(self):
        # Lấy giá trị của trường related để check điều kiện hiển thị
        for record in self:
            record.related = record.block_id.name == constraint.BLOCK_OFFICE_NAME

    @api.onchange('block_id')
    def _onchange_block(self):
        self.company = self.department_id = self.system_id = self.position_id = False
        if self.block_id:
            position = self.env['hrm.position'].search([('block', '=', self.block_id.name)])
            return {'domain': {'position_id': [('id', 'in', position.ids)]}}
        else:
            return {'domain': {'position_id': []}}

    @api.onchange('department_id')
    def _default_position(self):
        if self.department_id:
            position = self.env['hrm.position'].search([('department', '=', self.department_id.id)])
            return {'domain': {'position_id': [('id', 'in', position.ids)]}}

    @api.onchange('company')
    def _onchange_company(self):
        if not self.company:
            return
        self.system_id = self.company.system_id

    @api.onchange('system_id')
    def _onchange_system(self):
        if self.system_id != self.company.system_id:
            self.position_id = self.company = False
        if self.system_id:
            if not self.env.user.company:
                list_id = self._system_have_child_company(self.system_id.id)
                return {'domain': {'company': [('id', 'in', list_id)]}}
            else:
                self.company = False
                return {'domain': {'company': self.get_child_company()}}

    def find_block(self, records):
        for approved in records:
            if not approved.department_id and not approved.system_id:
                return approved

    def find_system(self, systems, records):
        for sys in systems:
            for rec in records:
                if sys[0] in rec.system_id.ids and self.find_child_company(rec):
                    return rec

    def find_department(self, list_dept, records):
        for dept in list_dept:
            for rec in records:
                if dept[0] in rec.department_id.ids:
                    return rec

    def find_company(self, record, list_company):
        for company_id in list_company:
            for cf in record:
                if cf.company and company_id[0] in cf.company.ids:
                    return cf

    @api.onchange('document_list')
    def set_sequence(self):
        i = 1
        for document in self.document_list:
            document.sequence = i
            i += 1

    @api.onchange('document_list')
    def _check_duplicate_document(self):
        list_document = [record.doc for record in self.document_list]
        seen = set()
        for item in list_document:
            if item in seen:
                raise ValidationError(f'Hồ sơ {item.name} đã có trong danh sách tài liệu')
            else:
                seen.add(item)

    def unlink(self):
        for record in self:
            document = self.env['hrm.employee.profile'].sudo().search([('document_config', '=', record.id)])
            if document:
                raise AccessDenied("Không thể xoá " + record.name)
        return super(DocumentListConfig, self).unlink()

    @api.constrains('document_list')
    def check_approval_flow_link(self):
        if not self.document_list:
            raise ValidationError('Không thể tạo khi không có tài liệu nào trong danh sách tài liệu.')
        else:
            list_check = []
            for item in self.document_list:
                if item.obligatory:
                    list_check.append(True)
            if not any(list_check):
                raise ValidationError('Cần có ít nhất một tài liệu bắt buộc.')


class DocumentList(models.Model):
    _name = 'hrm.document.list'
    _description = 'Danh sách tài liệu'

    document_id = fields.Many2one('hrm.document.list.config')
    sequence = fields.Integer(string="STT")
    doc = fields.Many2one('hrm.documents', string='Tên tài liệu')
    name = fields.Char(related='doc.name')
    obligatory = fields.Boolean(string='Bắt buộc')
