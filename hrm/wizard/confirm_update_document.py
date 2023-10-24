from odoo import models, fields, api


class ConfirmUpdateDocument(models.TransientModel):
    _name = 'hrm.confirm_update_document'
    _description = 'Xác nhận cập nhật tài liệu'

