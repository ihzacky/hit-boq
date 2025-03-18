from odoo import models, fields

class BoqConst(models.Model):
    _name = 'boq.const'
    _description = 'BoQ Price Dependency'

    profit_percentage = fields.Float(string="Persentase Keuntungan")
    material_margin = fields.Float(string='Material Margin')
    installation_margin = fields.Float(string='Installation Margin')

    boq_root_ids = fields.One2many(
        comodel_name="boq.root",
        inverse_name="boq_const_id"
    )
    
    work_unit_ids = fields.One2many(
        comodel_name = "boq.work_unit",
        inverse_name = "boq_const_id"
    )