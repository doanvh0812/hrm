from odoo import api, fields, models, tools, _

class RealEstateImage(models.Model):
    _name = 'see.image'
    _description = "See Image"

    upload_image = fields.Binary(string='upload')
    upload_image_ids = fields.Many2one('hrm.document_declaration')


