from odoo import models, fields, api

class BoqRoot(models.Model):
    _name = 'boq.root'
    _description = 'BoQ Root'


    boq_code = fields.Char(string='Kode BoQ')
    boq_name = fields.Char(string='Nama')
    material_margin = fields.Float(string='Material Margin')
    installation_margin = fields.Float(string='Installation Margin')
    updated_date = fields.Datetime(string="Updated Date") 
    updated_by = fields.Char(string="Updated By")

    material_price_total = fields.Monetary(string='Total Harga Material', currency_field='currency_id', compute="_compute_boq_price")
    installation_price_total = fields.Monetary(string='Total Harga Instalasi', currency_field='currency_id', compute="_compute_boq_price")
    service_price_total = fields.Monetary(string='Total Harga Service', currency_field='currency_id', compute="_compute_boq_price")
    maintenance_price_total = fields.Monetary(string='Total Harga Maintenance', currency_field='currency_id', compute="_compute_boq_price")
    price_final = fields.Monetary(string='Total Seluruh Harga', currency_field='currency_id', compute="_compute_boq_price")

    # tambahin status

    # work_unit_id = fields.Many2many(
    #     comodel_name='boq.work_unit',
    #     string='Work Unit Root'
    # )

    work_unit_line_ids = fields.One2many(
        comodel_name='boq.work_unit.line',
        inverse_name='boq_root_id',
        string='Work Unit Lines'
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency", 
        string="Currency", 
        default=lambda self: self.env.ref('base.IDR'),
        readonly=True,
    )

    @api.depends(
        'work_unit_line_ids', 
        'work_unit_line_ids.material_price_final', 
        'work_unit_line_ids.service_price_final', 
        'work_unit_line_ids.others_price_after_margin_final',
        'work_unit_line_ids.material_price_after_margin_final',
        'work_unit_line_ids.service_price_after_margin_final',

        'material_price_total',
        'installation_price_total',
        'service_price_total',
        'maintenance_price_total',
        'price_final',
        )
    def _compute_boq_price(self):
        for record in self:
            material_price_total = sum(record.work_unit_line_ids.mapped('material_price_final'))
            installation_price_total = sum(record.work_unit_line_ids.mapped('service_price_final'))
            maintenance_price_total = sum(record.work_unit_line_ids.mapped('others_price_after_margin_final'))

            record.material_price_total = material_price_total
            record.installation_price_total = installation_price_total
            record.maintenance_price_total = maintenance_price_total

            record.price_final = material_price_total + installation_price_total + maintenance_price_total
