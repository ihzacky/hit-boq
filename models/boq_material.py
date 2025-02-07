from odoo import models, fields, api

class BoqMaterial(models.Model):
    _name = 'boq.material'
    _description = 'BoQ Satuan Pekerjaan - Material'
    _order = "sequence"
    # _rec_name = 'boq_materials'

    material_name = fields.Char(string='Nama Material')
    material_code = fields.Char(string='Kode Material')
    material_description = fields.Text(string='Deskripsi Material')
    material_unit = fields.Char(string='Unit dari Material')
    # material final price
    material_price = fields.Monetary(string="Harga Final Material", currency_field="currency_id", compute="_compute_material_price")
    material_quantity = fields.Float(string="Quantity", default=1)
    
    sequence = fields.Integer(string="Sequence", default="10")

    product_id = fields.Many2one(
        comodel_name="product.product", 
        string="Product", 
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

    # pull price from master product
    product_base_price = fields.Float(
        string="Product Base Price",
        compute='_compute_product_base_price',
        store=True
    )

    @api.depends('product_id', 'product_id.lst_price')
    def _compute_product_base_price(self):
        for record in self:
            record.product_lst_price = record.product_id.lst_price if record.product_id else 0.0

    @api.depends('material_quantity', 'product_lst_price')
    def _compute_material_price(self):
        for record in self:
            record.material_price = record.material_quantity * record.producprot_lst_price


