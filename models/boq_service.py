from odoo import models, fields, api
from math import ceil

class BoqService(models.Model):
    _name = 'boq.service'
    _description = 'BoQ Satuan Pekerjaan - Jasa'
    # _rec_name = 'boq_jasa'

    service_name = fields.Char(string='Nama Jasa')
    service_unit = fields.Char(string='Unit jasa')
    service_price = fields.Float(string='Final Price', compute='_compute_service_price')
    service_pre_price = fields.Float(
        string='Price After Profit', 
        compute='_compute_service_price',
        help="Price after profit calculation, before quantity multiplication. Only shown for services with profit tags."
    )
    service_base_price = fields.Float(string='Base Price', compute='_get_service_base_price')
    

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

    # Tags that need profit calculation
    PROFIT_TAGS = [
        'Material Instalasi',
        'Sertifikasi',
        'Mobilisasi'
    ]

    @api.depends('product_id', 'product_id.lst_price')
    def _get_service_base_price(self):
        for record in self:
            record.service_base_price = record.product_id.lst_price if record.product_id else 0.0
    
    @api.depends('service_base_price', 'service_quantity', 'additional_product_tag_ids', 'work_unit_id.profit_percentage')
    def _compute_service_price(self):
        for record in self:
            # Get service tags
            tags = record.additional_product_tag_ids.mapped('name')
            
            # Check if any tag needs profit calculation
            needs_profit = any(tag in self.PROFIT_TAGS for tag in tags)
            
            if needs_profit:
                # Apply profit calculation
                profit_decimal = record.work_unit_id.profit_percentage / 100
                base_calculation = record.service_base_price / (1 - profit_decimal)
                unit_price = ceil(base_calculation / 100) * 100
                
                # Store pre-quantity price
                record.service_pre_price = unit_price
                # Calculate final price with quantity
                record.service_price = unit_price * record.service_quantity
            else:
                # Set pre_price to False for non-profit services
                # record.service_pre_price = False
                record.service_pre_price = record.service_base_price
                # Regular price calculation
                record.service_price = record.service_base_price * record.service_quantity


