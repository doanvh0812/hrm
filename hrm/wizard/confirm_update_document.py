from odoo import models, fields


class ConfirmUpdateDocument(models.TransientModel):
    _name = 'hrm.confirm_update_document'
    _description = 'Xác nhận cập nhật tài liệu'

    UPDATE_CONFIRM_DOCUMENT = [
        ('all', 'Áp dụng tất cả hồ sơ.'),
        ('not_approved_and_new', 'Áp dụng cho hồ sơ chưa được phê duyệt và hồ sơ mới.'),
        ('new', 'Áp dụng cho hồ sơ mới.')
    ]

    update_confirm_document = fields.Selection(selection=UPDATE_CONFIRM_DOCUMENT, string="Cập nhật tài liệu")

    # def action_confirm_update_document(self):
    #     # lấy bản ghi đang được chọn và gọi action duyệt
    #     leads = self.env['hrm.employee.profile'].sudo().browse(self.env.context.get('active_ids'))
    #     if self.update_confirm_document == 'all':
    #         print(leads)
    #         # return leads.write()
    #     elif self.update_confirm_document == 'not_approved_and_new':
    #         print(leads)
            # return leads.write()
