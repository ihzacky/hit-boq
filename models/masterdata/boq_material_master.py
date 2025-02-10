from odoo import models, fields, api

class BoqMasterMaterial(models.Model):
    _name = 'boq.material.master'
    _inherits = {'product.template': 'product_tmpl_id'}
    _description = 'BOQ Master Material'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template', 
        string='Product Template', 
        required=True, 
        ondelete='cascade'
    )
    material_code = fields.Char(string='Material Code')
    material_description = fields.Text(string='Material Description')
    material_unit = fields.Selection([
        ('ea', 'Each'),
        ('lot', 'Lot'),
        ('kg', 'Kilogram'),
        ('m', 'Meter'),
        ('l', 'Liter'),
    ], string='Material Unit', required=True, default='ea')

    # Add related fields for easier access
    list_price = fields.Float(related='product_tmpl_id.list_price', string='Sales Price', readonly=False)
    standard_price = fields.Float(related='product_tmpl_id.standard_price', string='Cost', readonly=False)
    uom_id = fields.Many2one(related='product_tmpl_id.uom_id', string='Unit of Measure', readonly=False)
    categ_id = fields.Many2one(related='product_tmpl_id.categ_id', string='Product Category', readonly=False)

    variant_ids = fields.One2many(
        comodel_name='boq.material.variant', 
        inverse_name='material_master_id', 
        string='Material Variants'
    )
    material_line_ids = fields.One2many(
        comodel_name="boq.material.line",
        inverse_name="material_master_id",
        string="Material Line"
    )

