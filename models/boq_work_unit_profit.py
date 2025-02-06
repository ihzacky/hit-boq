from odoo import models, fields

class BoqWorkUnitProfit(models.Model):
    _name = 'boq.work_unit.profit'
    _description = 'BoQ Harga Satuan Pekerjaan - Profit Percentage'

    work_unit_profit_percentage = fields.Integer(string="Persentase Keuntungan")

    work_unit_id = fields.Oney2many(comodel_name="boq.work_unit", inverse_name="work_unit_profit_id", string="Harga satuan pekerjaan")
    
    