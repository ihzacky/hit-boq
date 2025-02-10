from odoo import models, fields, api

class BoQMaterialVariant(models.Model):
    _name = 'boq.material.variant'
    _inherits = {'product.product': 'product_id'}
    _description = 'BoQ Material - Variant'

    product_id = fields.Many2one(
        'product.product',
        'Product Variant',
        required=True,
        ondelete='cascade'
    )
    material_master_id = fields.Many2one(
        'boq.material.master',
        'Master Material',
        required=True,
        ondelete='cascade'
    )
    variant_code = fields.Char(string='Variant Code')
    variant_description = fields.Text(string='Variant Description')
