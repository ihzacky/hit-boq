from odoo import models, fields, api

class BoqConf(models.Model):
    _name = 'boq.conf'
    _description = 'BoQ Price Configuration'

    profit_percentage = fields.Float(string="Persentase Keuntungan", default=15)
    material_margin = fields.Float(string='Material Margin', default=0.95)
    installation_margin = fields.Float(string='Installation Margin', default=0.95)

    boq_root_ids = fields.One2many(
        comodel_name="boq.root",
        inverse_name="boq_conf_id"
    )
    
    work_unit_ids = fields.One2many(
        comodel_name="boq.work_unit",
        inverse_name="boq_conf_id"
    )

    # Singleton
    @api.model
    def get_conf(self):
        
        return self.env.ref('hit_boq.default_boq_conf', raise_if_not_found=False) or self.create({})