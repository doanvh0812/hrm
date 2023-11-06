from odoo import api, fields, models


class Multiple_Image(models.Model):
    _name = 'hrm.multi.image'
    _description = "Upload Multi Image"

    document_declaration = fields.Many2one('hrm.document_declaration')
    attachment_ids = fields.Many2many('ir.attachment')

    def action_save_images(self):
        image = self.env['hrm.image']
        i = 0
        for img in self.attachment_ids:
            i += 1
            self.document_declaration.sudo().write({
                "picture_ids": [(0, 0, {
                    'name': f'img-{i}',
                    'image': img.datas
                })]
            })
