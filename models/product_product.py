from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Optional custom flags if needed
    is_material = fields.Boolean(string="Is Material", default=False)
    is_service = fields.Boolean(string="Is Service", default=False)

