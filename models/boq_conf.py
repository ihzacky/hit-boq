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
        conf = self.search([], limit=1)
        if not conf:
            conf = self.create({})
        return conf