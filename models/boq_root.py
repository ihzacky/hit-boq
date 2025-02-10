from odoo import models, fields, api

class BoqRoot(models.Model):
    _name = 'boq.root'
    _description = 'BoQ Root'

    boq_code = fields.Char(string='BoQ Code', required=True)
    boq_name = fields.Char(string='BoQ Name', required=True)
    material_margin = fields.Float(string='Material Margin (%)', default=0.0)
    installation_margin = fields.Float(string='Installation Margin (%)', default=0.0)
    price_final = fields.Float(string='Final Price', compute='_compute_price_final', store=True)
    work_unit_id = fields.One2many(
        comodel_name='boq.work_unit',
        inverse_name='boq_root_id',
        string='Work Units'
    )

    @api.depends('work_unit_id', 'material_margin', 'installation_margin')
    def _compute_price_final(self):
        for record in self:
            base_price = sum(record.work_unit_id.mapped('price_unit'))
            material_margin = base_price * (record.material_margin / 100)
            installation_margin = base_price * (record.installation_margin / 100)
            record.price_final = base_price + material_margin + installation_margin



