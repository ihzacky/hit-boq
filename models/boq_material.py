from odoo import models, fields, api
from math import ceil

class BoqMaterial(models.Model):
    _name = 'boq.material'
    _description = 'BoQ Satuan Pekerjaan - Material'
    _order = "sequence"
    # _rec_name = 'boq_materials'

    material_code = fields.Char(string='Kode Material')
    material_description = fields.Text(string='Deskripsi Material')
    material_unit = fields.Char(string='Unit dari Material')
    material_price_final = fields.Monetary(string="Harga Final Material", currency_field="currency_id", compute="_compute_material_price_final")
    material_quantity = fields.Float(string="Quantity", default=1)
    
    sequence = fields.Integer(string="Sequence", default="10")

    product_id = fields.Many2one(
        comodel_name="product.product", 
        string="Product",
        domain=[('type', '=', 'consu')], 
    )
    
    work_unit_id = fields.Many2one(
        comodel_name="boq.work_unit", 
        string="Work Unit", 
    )
    
    currency_id = fields.Many2one(
        comodel_name="res.currency", 
        string="Currency", 
        default=lambda self: self.env.ref('base.IDR'),
        readonly=True,
    )    

    material_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit",
        related="product_id.uom_id",
        readonly=True
    )

    # pull price from master product
    material_base_price = fields.Float(
        string="Product Base Price",
        compute='_get_material_base_price',
        store=True
    )

    material_price = fields.Float(
        string="Price After Profit",
        compute='_compute_material_price',
        store=True
    )

    @api.depends('product_id', 'product_id.lst_price')
    def _get_material_base_price(self):
        for record in self:
            record.material_base_price = record.product_id.lst_price if record.product_id else 0.0

    @api.depends('material_base_price', 'work_unit_id.profit_percentage')
    def _compute_material_price(self):
        for record in self:
            profit_decimal = record.work_unit_id.profit_percentage / 100
            base_calculation = record.material_base_price / (1 - profit_decimal)
            record.material_price = ceil(base_calculation / 100) * 100

    @api.depends('material_quantity', 'material_base_price')
    def _compute_material_price_final(self):
        for record in self:
            record.material_price_final = record.material_quantity * record.material_price



