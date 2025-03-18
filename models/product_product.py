from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_material = fields.Boolean(string="Is Material", default=False)
    is_service = fields.Boolean(string="Is Service", default=False)

    def _compute_flags(self):
        for record in self:
            if record.type == 'consu':
                record.is_material = True
                record.is_service = False
            elif record.type == 'service':
                record.is_material = False
                record.is_service = True
            else:
                record.is_material = False
                record.is_service = False

