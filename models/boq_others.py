from odoo import models, fields, api

class BoqOthers(models.Model):
    _name = 'boq.others'
    _description = 'BoQ Satuan Pekerjaan - Lainnya'
    _rec_name = 'others_name'

    others_name = fields.Char(string="Nama Lain-Lain")
    others_base_price = fields.Monetary(string="Harga/Unit", currency_fields="currency_id", compute="_compute_others_base_price")
    others_price_final = fields.Monetary(string="Harga", currency_fields="currency_id", compute="_compute_others_price_final")
    others_quantity = fields.Float(string="Quantity", default=0)
    others_uom = fields.Char(string="Unit", default="%", readonly=True)

    work_unit_id = fields.Many2one(comodel_name="boq.work_unit", string="Work Unit")

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

    @api.depends('work_unit_id', 'others_name')
    def _compute_others_base_price(self):
        for record in self:
            # If the record name is "lain-lain", check for the previous record named "keuntungan"
            if record.others_name and record.others_name.lower() == 'Lain-lain':
                keuntungan_rec = self.search(
                    [('id', '<', record.id), ('others_name', '=', 'Keuntungan')],
                    order='id desc',    
                    limit=1
                )
                if keuntungan_rec:
                    record.others_base_price = keuntungan_rec.others_base_price
                    continue
            if record.work_unit_id:
                record.others_base_price = record.work_unit_id.materials_price + record.work_unit_id.services_price
            else:
                record.others_base_price = 0

    @api.depends('others_base_price', 'others_quantity')
    def _compute_others_price_final(self):
        for record in self:
            record.others_price_final = record.others_base_price * record.others_quantity * 1/100

    def recompute_others_price(self):
        for record in self:
            record._compute_others_base_price()
            record._compute_others_price_final()
