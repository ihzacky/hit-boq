from odoo import models, fields, api

class BoqOthers(models.Model):
    _name = 'boq.others'
    _description = 'BoQ Satuan Pekerjaan - Lainnya'
    # _rec_name = 'boq_others'

    others_profit = fields.Monetary(string="Keuntungan", currency_fields="currency_id")
    others_others = fields.Monetary(string="Lain-lain (Kendaraan, dll)", currency_fields="currency_id", compute="")

    # work_unit_id = fields.Many2one(comodel_name="boq.work_unit", string="Work Unit", compute="compute_others", inverse="stage_inverse")
    work_unit_id = fields.Many2one(comodel_name="boq.work_unit", string="Work Unit")
    # others_ids = fields.One2many(comodel_name='boq.work_unit', inverse_name='others_id')

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

    # @api.depends('others_ids')
    # def compute_others(self):
    #     if len(self.others_ids) > 0:
    #         self.work_unit_id = self.others_ids[0]

    # def stage_inverse(self):
    #     if len(self.others_ids) > 0:
    #         # delete previous reference
    #         stage = self.env['hr.job'].browse(self.others_ids[0].id)
    #         asset.other_id = False
    #     # set new reference
    #     self.work_unit_id.other_id = self

    

