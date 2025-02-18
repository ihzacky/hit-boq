from odoo import models, fields, api 
import logging

_logger = logging.getLogger(__name__)

class BoqWorkUnit(models.Model):
    _name = 'boq.work_unit'
    _description = 'BoQ Satuan Pekerjaan - Root'
    _inherit = 'mail.thread', 'mail.activity.mixin'
    _rec_name = 'work_unit_code'
    _order = 'sequence, id'

    sequence = fields.Integer(string="Sequence", default="1")
    work_unit_code = fields.Char(string='Kode Pekerjaan')
    work_unit_name = fields.Char(string='Nama Pekerjaan')
    updated_date = fields.Datetime(string="Updated Date") 
    updated_by = fields.Char(string="Updated By")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting for Confirmation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="State", default='draft', readonly=True, tracking=True)
    status = fields.Char(string="Status", compute="_compute_status", readonly=True, store=True)
    revision_count = fields.Integer(string="Revision Count", compute="_compute_status", readonly=True, store=True)

    price_unit = fields.Monetary(string="Harga Pekerjaan", currency_field="currency_id", compute="_compute_price_unit",  tracking=True)
    
    material_ids = fields.One2many(
        comodel_name='boq.material', 
        inverse_name="work_unit_id", 
        string='Satuan Pekerjaan - Material'
    )
    materials_price = fields.Monetary(string="Harga Material", currency_field="currency_id", compute="_compute_component_prices", tracking=True, store=True)

    service_ids = fields.One2many(
        comodel_name='boq.service', 
        inverse_name="work_unit_id", 
        string='Satuan Pekerjaan - Jasa'
    )
    services_price = fields.Monetary(string="Harga Instalasi", currency_field="currency_id", compute="_compute_component_prices", tracking=True, store=True)

    others_ids = fields.One2many(
        comodel_name="boq.others", 
        inverse_name="work_unit_id", 
        string="Satuan Pekerjaan - Lain-Lain"
    )
    others_price = fields.Monetary(string="Harga Lain-Lain", currency_field="currency_id", compute="_compute_component_prices", tracking=True, store=True)

    profit_percentage = fields.Integer(string="Profit Percentage", tracking=True, default=15)    

    currency_id = fields.Many2one(
        comodel_name="res.currency", 
        string="Currency", 
        default=lambda   self: self.env.ref('base.IDR'),
        readonly=True,
    )

    work_unit_line_ids = fields.One2many(
        comodel_name='boq.work_unit.line',
        inverse_name='work_unit_id',
        string='BOQ Work Unit Lines',
        tracking=True,
    )
    
    @api.depends('materials_price', 'services_price', 'others_price')
    def _compute_price_unit(self):
        for line in self:
            materials_price = line.materials_price or 0.0
            services_price = line.services_price or 0.0
            others_price = line.others_price or 0.0
            
            # calculate total price
            line.price_unit = materials_price + services_price + others_price
    
    @api.depends('material_ids', 'service_ids', 'others_ids')
    def _compute_component_prices(self):
        for line in self:
            _logger.info(f"Currency: {self.currency_id}")
            line.materials_price = sum(line.material_ids.mapped('material_price')) if line.material_ids else 0.0
            line.services_price = sum(line.service_ids.mapped('service_price')) if line.service_ids else 0.0
            line.others_price = sum(line.others_ids.mapped('others_price_final')) if line.others_ids else 0.0

    @api.onchange('work_unit_code')
    def _onchange_work_unit_code(self):
        if self.work_unit_code and not self.others_ids:
            self.others_ids = [
                (0, 0, {'others_name': 'Keuntungan'}),
                (0, 0, {'others_name': 'Lain-lain'}),
            ]

    def action_refresh(self):
        self.ensure_one()
        self.material_ids.recompute_material_price()
        self.service_ids.recompute_service_price
        self.others_ids.recompute_others_price()
        self._compute_component_prices() 
        self._compute_price_unit()
        return True 

    def action_save(self):
        self.ensure_one()
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

    def action_state_waiting(self):
        self.ensure_one()
        self.write({'state': 'waiting'})
        return True 

    def action_state_approved(self):
        self.ensure_one()
        self.write({'state': 'approved'})
        return True

    def action_state_rejected(self):
        self.ensure_one()
        self.write({'state': 'rejected'})
        return True

    def action_send_to_revision(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        return True

    @api.depends('state', 'message_ids')
    def _compute_status(self):
        for record in self:
            # Get all tracked changes for the state field
            state_changes = record.message_ids.filtered(
                lambda m: m.tracking_value_ids.filtered(
                    lambda t: t.field_groups == 'state' and t.old_value_char in ['approved', 'rejected'] and t.new_value_char in ['draft']
                )
            )
            revision_count = len(state_changes)
            
            base_status = {
                'draft': 'Draft',
                'waiting': 'Waiting for Confirmation',
                'approved': 'Approved',
                'rejected': 'Rejected'
            }.get(record.state, '')

            if revision_count > 0:
                record.status = f"Revision-{revision_count} ({base_status})"
            else:
                record.status = base_status


