from odoo import models, fields, api

class BoqService(models.Model):
    _name = 'boq.service'
    _description = 'BoQ Satuan Pekerjaan - Jasa'
    # _rec_name = 'boq_jasa'

    service_name = fields.Char(string='Nama Jasa')
    service_unit = fields.Char(string='Unit jasa')
    service_price = fields.Float(string='Harga Final Jasa', compute='_compute_service_price')
    service_base_price = fields.Float(string='Service Base Price', compute='_get_service_base_price')
    service_quantity = fields.Float(string='Quantity', default=1)

    sequence = fields.Integer(string="Sequence", default="10")

    work_unit_id = fields.Many2one(
        comodel_name='boq.work_unit', 
        string='Satuan Pekerjaan Root'
    )

    product_id = fields.Many2one(
        comodel_name="product.product", 
        string="Product", 
        domain=[('type', '=', 'service')],
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency", 
        string="Currency", 
        default=lambda self: self.env.ref('base.IDR'),
        readonly=True,
    )

    service_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit",
        related="product_id.uom_id",
        readonly=True
    )

    additional_product_tag_ids = fields.Many2many(
        comodel_name='product.tag',
        string='Tags',
        related='product_id.product_tag_ids',
        readonly=True
    )

    @api.depends('product_id', 'product_id.lst_price')
    def _get_service_base_price(self):
        for record in self:
            record.service_base_price = record.product_id.lst_price if record.product_id else 0.0
    
    @api.depends('service_base_price', 'service_quantity')
    def _compute_service_price(self):
        for record in self:
            record.service_price = record.service_base_price * record.service_quantity

    # compute installation material price
    # @api.depends('service_base_price', 'service_quantity')

