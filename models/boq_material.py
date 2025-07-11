from odoo import models, fields, api
from math import ceil

class BoqMaterialLine(models.Model):
    _name = 'boq.material.line'
    _description = 'BoQ Satuan Pekerjaan - Material Line'
    _inherit = "mail.thread"
    _order = "sequence, id"

    material_code = fields.Char(string='Kode Material')
    material_description = fields.Text(string='Deskripsi Material')
    material_unit = fields.Char(string='Unit dari Material')
    material_price = fields.Monetary(string="Harga Final Material", currency_field="currency_id", compute="_compute_material_price_final")
    material_quantity = fields.Float(string="Quantity", default=1)
    
    sequence = fields.Integer(string="Sequence", default="1")

    product_id = fields.Many2one(
        comodel_name="product.product", 
        string="Product",
        domain=[
            ('type', '=', 'consu'),
            ('is_material', '=', 'True')
        ], 
        tracking=True,
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
        readonly=True,
        tracking=True,
    )

    # pull price from master product
    material_base_price = fields.Monetary(
        string="Product Base Price",
        currency_field='currency_id',
        compute='_get_material_base_price',
        store=True,
        tracking=True,
    )

    material_pre_price = fields.Monetary(
        string="Price After Profit",
        currency_field='currency_id',
        compute='_compute_material_price',
        store=True,
        tracking=True,
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
            record.material_pre_price = ceil(base_calculation / 100) * 100

    @api.depends('material_quantity', 'material_base_price')
    def _compute_material_price_final(self):
        for record in self:
            record.material_price = record.material_quantity * record.material_pre_price

    def recompute_material_price(self):
        for record in self:
            record._compute_material_price()
            record._compute_material_price_final()

