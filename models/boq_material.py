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
    material_price = fields.Monetary(string="Harga Material", currency_field="currency_id")
    
    sequence = fields.Integer(string="Sequence", default="10")

    # price_unit = fields.Float(
    #     string="Unit Price",
    #     compute='_compute_price_unit',
    #     digits='Product Price',
    #     store=True, readonly=False, required=True, precompute=True)

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

    product_lst_price = fields.Float(
        string="Product Price",
        compute='_compute_product_lst_price',
        store=True
    )

    @api.depends('product_id', 'product_id.lst_price')
    def _compute_product_lst_price(self):
        for record in self:
            record.product_lst_price = record.product_id.lst_price if record.product_id else 0.0

    # @api.depends('product_id', 'product_uom', 'product_uom_qty')
    # def _compute_price_unit(self):
    #     for line in self:
    #         # check if there is already invoiced amount. if so, the price shouldn't change as it might have been
    #         # manually edited
    #         # if line.qty_invoiced > 0 or (line.product_id.expense_policy == 'cost' and line.is_expense):
    #         #     continue
    #         # if not line.product_uom or not line.product_id:
    #         #     line.price_unit = 0.0

    #         # override
    #         if work_unit_id.material_ids:
    #             temp_price = 0
    #             for material in work_unit_id.material_ids:
    #                 temp_price += material.material_price
    #             line.price_unit = temp_price

    #         # else:
    #         #     line = line.with_company(line.company_id)
    #         #     price = line._get_display_price()
    #         #     line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
    #         #         price,
    #         #         line.currency_id or line.order_id.currency_id,
    #         #         product_taxes=line.product_id.taxes_id.filtered(
    #         #             lambda tax: tax.company_id == line.env.company
    #         #         ),
    #         #         fiscal_position=line.order_id.fiscal_position_id,
    #         #     )


