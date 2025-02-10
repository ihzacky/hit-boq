from odoo import models, fields, api

class BoqMasterMaterial(models.Model):
    _name = 'boq.master_material'
    _inherits = {'product.product': 'product_id'}
    _description = 'BOQ Master Material'

    material_code = fields.Char(string='Material Code')
    material_description = fields.Text(string='Material Description')
    material_unit = fields.Selection([
        ('ea', 'Each'),
        ('lot', 'Lot'),
        ('kg', 'Kilogram'),
        ('m', 'Meter'),
        ('l', 'Liter'),
    ], string='Material Unit', required=True, default='ea')

    material_line_ids = fields.One2many(
        comodel_name="boq.material.line",
        inverse_name="master_material_id",
        string="Material Line"
    )
    
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True, ondelete="cascade")

