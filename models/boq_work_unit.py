from odoo import models, fields, api 
import logging

_logger = logging.getLogger(__name__)

class BoqWorkUnit(models.Model):
    _name = 'boq.work_unit'
    _description = 'BoQ Satuan Pekerjaan - Root'
    # _rec_name = 'boq_satuan_pekerjaan'

    work_unit_code = fields.Char(string='Kode Pekerjaan')
    work_unit_name = fields.Char(string='Nama Pekerjaan')
    updated_date = fields.Datetime(string="Updated Date") 
    updated_by = fields.Char(string="Updated By")
    
    price_unit = fields.Monetary(string="Harga Satuan Pekerjaan", currency_field="currency_id", compute="_compute_price_unit")
    
    material_ids = fields.One2many(
        comodel_name='boq.material', 
        inverse_name="work_unit_id", 
        string='Satuan Pekerjaan - Material'
    )
    materials_price = fields.Monetary(string="Harga Material", currency_field="currency_id", compute="_compute_component_prices", store=True)

    service_ids = fields.One2many(
        comodel_name='boq.service', 
        inverse_name="work_unit_id", 
        string='Satuan Pekerjaan - Jasa'
    )
    services_price = fields.Monetary(string="Harga Jasa", currency_field="currency_id", compute="_compute_component_prices", store=True)

    others_ids = fields.One2many(
        comodel_name="boq.others", 
        inverse_name="work_unit_id", 
        string="Satuan Pekerjaan - Lain-Lain"
    )
    others_price = fields.Monetary(string="Harga Lain-Lain", currency_field="currency_id", compute="_compute_component_prices", store=True)

    profit_percentage = fields.Integer(string="Profit Percentage", tracking=True, default=15)    

    currency_id = fields.Many2one(
        comodel_name="res.currency", 
        string="Currency", 
        default=lambda self: self.env.ref('base.IDR'),
        readonly=True,
    )
    
    boq_root_id = fields.Many2many(
        comodel_name='boq.root',
        string='BOQ Roots'
    )
    
    @api.depends('materials_price', 'services_price', 'others_price')
    def _compute_price_unit(self):
        for line in self:
            # Ensure we have valid float values for all components
            materials_price = line.materials_price or 0.0
            services_price = line.services_price or 0.0
            others_price = line.others_price or 0.0
            
            # Calculate total price
            line.price_unit = materials_price + services_price + others_price
    
    @api.depends('material_ids', 'service_ids', 'others_ids')
    def _compute_component_prices(self):
        for line in self:
            _logger.info(f"Currency: {self.currency_id}")
            # Compute material price
            line.materials_price = sum(line.material_ids.mapped('material_price')) if line.material_ids else 0.0
            
            # Compute service price
            line.services_price = sum(line.service_ids.mapped('service_price')) if line.service_ids else 0.0
            
            # Compute others price
            line.others_price = sum(line.others_ids.mapped('others_profit')) if line.others_ids else 0.0

    def action_refresh(self):
        

    def action_save(self):
        self.ensure_one()
        # Update the updated_date and updated_by fields
        self.write({
            'updated_date': fields.Datetime.now(),
            'updated_by': self.env.user.name
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'main',
        }





    
