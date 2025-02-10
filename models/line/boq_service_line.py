from odoo import models, fields, api

class BoqServiceLine(models.Model):
    _name = 'boq.service.line'
    _description = 'BoQ Satuan Pekerjaan - Jasa Line'
    # _rec_name = 'boq_jasa'

    service_name = fields.Char(string='Nama Jasa')
    service_unit = fields.Char(string='Unit jasa')
    service_price = fields.Monetary(string='Harga Final Jasa', currency_field='currency_id')
    service_base_price = fields.Float(string='Service Base Price', compute='_compute_service_base_price', store=True)
    service_quantity = fields.Float(string='Quantity', default=1)

    sequence = fields.Integer(string="Sequence", default="10")

    work_unit_id = fields.Many2one(comodel_name='boq.work_unit', string='Satuan Pekerjaan Root')
    product_id = fields.Many2one(
        comodel_name="product.product", 
        string="Product", 
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency", 
        string="Currency", 
        default=lambda self: self.env.ref('base.IDR'),
        readonly=True,
    )

    @api.depends('product_id', 'product_id.lst_price')
    def _compute_service_base_price(self):
        for record in self:
            record.service_base_price = record.product_id.lst_price if record.product_id else 0.0
