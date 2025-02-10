from odoo import models, fields, api

class BoqMaterialLine(models.Model):
    _name = 'boq.material.line'
    _description = 'BoQ Satuan Pekerjaan - Material Line'
    _order = "sequence"

    material_master_id = fields.Many2one(
        comodel_name='boq.material.master',
        string='Master Material',
        required=True
    )
    material_variant_id = fields.Many2one(
        comodel_name='boq.material.variant',
        string='Material Variant',
        domain="[('material_master_id', '=', material_master_id)]"  # Only show variants of selected master
    )
    
    material_name = fields.Char(
        string='Material Name',
        related='material_master_id.name',
        store=True
    )
    
    material_price = fields.Monetary(
        string="Harga Final Material", 
        currency_field="currency_id", 
        compute="_compute_material_price"
    )
    material_quantity = fields.Float(string="Quantity", default=1)
    material_description = fields.Text(string="Deskripsi Material")
    sequence = fields.Integer(string="Sequence", default=10)

    work_unit_id = fields.Many2one(
        comodel_name="boq.work_unit", 
        string="Work Unit"
    )

    uom_id = fields.Many2one(
        comodel_name="uom.uom", 
        string="Unit of Measure",
        related="material_master_id.uom_id",
        store=True,
        readonly=True
    )
    
    currency_id = fields.Many2one(
        comodel_name="res.currency", 
        string="Currency", 
        default=lambda self: self.env.ref('base.IDR'),
        readonly=True
    )    

    product_base_price = fields.Float(
        string="Product Base Price",
        compute='_compute_product_base_price',
        store=True
    )

    # Add a helper compute field to determine which price to use
    active_price = fields.Float(
        string="Active Price",
        compute='_compute_active_price',
        store=True
    )
    
    @api.depends('material_master_id', 'material_variant_id', 
                'material_master_id.product_tmpl_id.standard_price',
                'material_variant_id.product_id.lst_price')
    def _compute_active_price(self):
        for record in self:
            if record.material_variant_id and record.material_variant_id.product_id:
                # Use variant price if variant is selected
                record.active_price = record.material_variant_id.product_id.lst_price
            elif record.material_master_id and record.material_master_id.product_tmpl_id:
                # Fallback to master material price
                record.active_price = record.material_master_id.product_tmpl_id.standard_price
            else:
                record.active_price = 0.0

    @api.depends('active_price')
    def _compute_product_base_price(self):
        for record in self:
            record.product_base_price = record.active_price

    @api.depends('material_quantity', 'product_base_price')
    def _compute_material_price(self):
        for record in self:
            record.material_price = record.material_quantity * record.product_base_price

    @api.onchange('material_master_id')
    def _onchange_material_master(self):
        """Clear variant when master changes"""
        self.material_variant_id = False


