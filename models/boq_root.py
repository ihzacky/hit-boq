from odoo import models, fields, api

class BoqRoot(models.Model):
    _name = 'boq.root'
    _description = 'BoQ Root'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'boq_code'

    boq_code = fields.Char(string='Kode BoQ')
    boq_name = fields.Char(string='Nama')
    material_margin = fields.Float(string='Material Margin')
    installation_margin = fields.Float(string='Installation Margin')
    updated_date = fields.Datetime(string="Updated Date") 
    updated_by = fields.Char(string="Updated By")

    material_price_total = fields.Monetary(string='Total Harga Material', currency_field='currency_id', compute="_compute_boq_price", tracking=True)
    installation_price_total = fields.Monetary(string='Total Harga Instalasi', currency_field='currency_id', compute="_compute_boq_price", tracking=True)
    # service_price_total = fields.Monetary(string='Total Harga Service', currency_field='currency_id', compute="_compute_boq_price", tracking=True)
    maintenance_price_total = fields.Monetary(string='Total Harga Maintenance', currency_field='currency_id', compute="_compute_boq_price")
    price_final = fields.Monetary(string='Total Seluruh Harga', currency_field='currency_id', compute="_compute_boq_price", tracking=True)

    # tambahin status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
    ], string='Status', default='draft', tracking=True)

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
        'material_price_total',
        'installation_price_total',
        'maintenance_price_total',
        'price_final',
    )
    def _compute_boq_price(self):
        for record in self:
            material_total = 0.0
            installation_total = 0.0
            maintenance_total = 0.0
            
            for line in record.work_unit_line_ids:
                material_total += line.material_price_final or 0.0
                if line.work_unit_line_code.startswith('MNT'):
                    maintenance_total += line.service_price_final or 0.0
                else:
                    installation_total += line.service_price_final or 0.0
                    
            record.material_price_total = material_total
            record.installation_price_total = installation_total
            record.maintenance_price_total = maintenance_total
            record.price_final = material_total + installation_total + maintenance_total
