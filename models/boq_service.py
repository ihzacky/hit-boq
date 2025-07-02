from odoo import models, fields, api
from math import ceil

class BoqServiceLine(models.Model):
    _name = 'boq.service.line'
    _description = 'BoQ Satuan Pekerjaan - Jasa'
    _order = "sequence, id"
    _inherit = "mail.thread"

    service_name = fields.Char(string='Nama Jasa', tracking=True, compute="_get_attributes_from_product")
    service_unit = fields.Char(string='Unit jasa')
    service_price = fields.Float(string='Final Price', compute='_compute_service_price_final')
    service_pre_price = fields.Monetary(string='Price After Profit', currency_field='currency_id', compute='_compute_service_price')
    service_base_price = fields.Monetary(string='Base Price', currency_field='currency_id', compute='_get_attributes_from_product')
    

    service_quantity = fields.Float(string='Quantity', default=1)

    sequence = fields.Integer(string="Sequence", default="1")

    work_unit_id = fields.Many2one(
        comodel_name='boq.work_unit', 
        string='Satuan Pekerjaan Root'
    )

    product_id = fields.Many2one(
        comodel_name="product.product", 
        string="Product", 
        domain=[
            ('type', '=', 'service'),
            ('is_service', '=', 'True')
        ],
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

    product_tag_ids = fields.Many2many(
        comodel_name='product.tag',
        string='Tags',
        related='product_id.product_tag_ids',
        readonly=True
    )

    # Tags that need profit calculation
    PROFIT_TAGS = [
        'Material Instalasi',
        'Sertifikasi',
        'Mobilisasi'
    ]

    @api.depends('product_id', 'product_id.lst_price')
    def _get_attributes_from_product(self):
        for record in self:
            record.service_base_price = record.product_id.lst_price if record.product_id else 0.0
            record.service_name = record.product_id.name if record.product_id else "Unavailable"
    
    @api.depends('service_base_price', 'service_quantity', 'product_tag_ids', 'work_unit_id.profit_percentage')
    def _compute_service_price(self):
        for record in self:
            # Get service tags
            tags = record.product_tag_ids.mapped('name')
            
            # Check if any tag needs profit calculation
            needs_profit = any(tag in self.PROFIT_TAGS for tag in tags)
            
            if needs_profit:
                profit_decimal = record.work_unit_id.profit_percentage / 100
                base_calculation = record.service_base_price / (1 - profit_decimal)
                unit_price = ceil(base_calculation / 100) * 100
                
                record.service_pre_price = unit_price
            else:
                record.service_pre_price = record.service_base_price

    @api.depends('service_base_price', 'service_quantity', 'service_pre_price')
    def _compute_service_price_final(self):
        for record in self:
            record.service_price = record.service_pre_price * record.service_quantity

    
    def recompute_service_price(self):
        for record in self:
            record._compute_service_price()
            record._compute_service_price_final()


