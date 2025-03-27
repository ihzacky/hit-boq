from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_material = fields.Boolean(string="Is Material", default=False)
    is_service = fields.Boolean(string="Is Service", default=False)

    @api.constrains('product_tmpl_id.type')
    def _compute_flags(self):
        for record in self:
            if record.product_tmpl_id.type == 'consu':
                record.is_material = True
                record.is_service = False
            elif record.product_tmpl_id.type == 'service':
                record.is_material = False
                record.is_service = True
            else:
                record.is_material = False
                record.is_service = False
    
    @api.constrains('product_tmpl_id.product_tag_ids')
    def _check_product_tags(self):
        for record in self:
            if record.is_service:
                product_tags = record.product_tmpl_id.product_tag_ids
                if not product_tags:
                    raise ValidationError("Please select at least one product tag on the Product Template.")