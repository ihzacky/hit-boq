from odoo import models, fields

class BoqWorkUnitProfit(models.Model):
    _name = 'boq.work_unit.profit'
    _description = 'BoQ Harga Satuan Pekerjaan - Profit Percentage'

    profit_percentage = fields.Float(string="Persentase Keuntungan")

    # work_unit_ids = fields.One2many(
    #     comodel_name="boq.work_unit", 
    #     inverse_name="work_unit_profit_id", 
    #     string="Harga satuan pekerjaan"
    # )
    
    