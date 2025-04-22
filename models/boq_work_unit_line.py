from odoo import models, fields, api
from math import ceil

class BoqWorkUnitLine(models.Model):
    _name = 'boq.work_unit.line'
    _description = 'BoQ Work Unit Line'
    _order = 'sequence'

    
    sequence = fields.Integer(string="Sequence", default=1)
    is_duplicate = fields.Boolean(compute='_get_duplicate_status', store=True)
    name = fields.Char(string='Nama Pekerjaan', compute='_get_work_unit_components', store=True, readonly=False, required=True)
    code = fields.Char(string='Kode Pekerjaan', compute='_get_work_unit_components', readonly=False, store=True)
    quantity = fields.Float(string='Quantity', default=1)

    # Before Margin
    material_base_price = fields.Monetary(string='Material Base Price', currency_field='currency_id', compute='_get_base_price', store=True)
    material_price_final = fields.Monetary(string='Material Price', currency_field='currency_id', compute='_compute_components_price_final', store=True)
    
    service_base_price = fields.Monetary(string='Service Base Price', currency_field='currency_id', compute='_get_base_price', store=True)
    service_price_final = fields.Monetary(string='Service Price', currency_field='currency_id', compute='_compute_components_price_final', store=True)
    
    others_base_price = fields.Monetary(string='Others Base Price', currency_field='currency_id', compute='_get_base_price', inverse='_inverse_others_base_price', store=True)
    others_price_final = fields.Monetary(string='Others Price', currency_field='currency_id', compute='_compute_components_price_final', store=True)
    
    # After Margin 
    material_margin_base = fields.Monetary(string='Material Base Price After Margin', currency_field='currency_id', compute='_compute_components_price_after_margin', store=True)
    material_margin_final = fields.Monetary(string='Material Price After Margin', currency_field='currency_id', compute='_compute_components_price_after_margin_final', store=True)

    service_margin_base = fields.Monetary(string='Service Base Price After Margin', currency_field='currency_id', compute='_compute_components_price_after_margin', store=True)
    service_margin_final = fields.Monetary(string='Service Price After Margin', currency_field='currency_id', compute='_compute_components_price_after_margin_final', store=True)

    final_price = fields.Monetary(string='Final Price', currency_field='currency_id', compute='_compute_components_price_after_margin_final', store=True, readonly=True)

    master_price = fields.Monetary(string='Price', currency_field='currency_id', compute='_get_base_price', store=True, readonly=True)
    override_price = fields.Monetary(string='Override Base Price', currency_field='currency_id', default=0, readonly=False)

    work_unit_id = fields.Many2one(
        comodel_name='boq.work_unit',
        string='Satuan Pekerjaan',
        domain=[
            ('state', '=', 'approved'),
            ('is_duplicate', '=', False)
        ]
    )
    
    boq_root_id = fields.Many2one(
        comodel_name='boq.root',
        string='BoQ Root',
        ondelete='cascade'
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency", 
        string="Currency", 
        default=lambda self: self.env.ref('base.IDR'),
        readonly=True,
    )

    work_unit_line_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit",
        help="Unit of Measure for the work unit line"
    )

    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ], default=False
    )
    
    @api.model_create_multi
    def create(self, vals_list):
            for vals in vals_list:
                if vals.get('display_type', self.default_get(['display_type'])['display_type']):
                    vals.update(work_unit_id=False, quantity=0, work_unit_line_uom=False)
            return super().create(vals_list)
    
    # before margin
    @api.depends('work_unit_id', 'work_unit_id.material_total', 'work_unit_id.service_total', 'work_unit_id.others_price', 'override_price')
    def _get_base_price(self):
        for record in self:
            # Round up to nearest thousand
            if record.override_price:
                # Check work unit code prefix
                if record.code and record.code.startswith('MNT'):
                    record.others_base_price = record.override_price
                    record.service_base_price = 0
                    record.material_base_price = 0
                elif record.code and record.code.startswith('INST'):
                    record.others_base_price = 0
                    record.service_base_price = record.override_price
                    record.material_base_price = 0
            
                record.master_price = record.work_unit_id.price_unit
            
            elif record.override_price == 0:
                record.material_base_price = ceil(record.work_unit_id.material_total / 1000) * 1000
                record.service_base_price = ceil(record.work_unit_id.service_total / 1000) * 1000
                record.others_base_price = ceil(record.work_unit_id.others_price / 1000) * 1000

                record.master_price = record.work_unit_id.price_unit

    def _inverse_others_base_price(self):
        for record in self:
            default_val = ceil(record.work_unit_id.others_price / 1000) * 1000
            
            if record.others_base_price != default_val:
                record.override_price = record.others_base_price
            else:
                record.override_price = 0

    @api.depends('quantity', 'material_base_price', 'service_base_price', 'others_base_price')
    def _compute_components_price_final(self):
        for record in self:
            record.material_price_final = record.material_base_price * record.quantity
            record.service_price_final = record.service_base_price * record.quantity
            record.others_price_final = record.others_base_price * record.quantity

    # after margin
    @api.depends(
        'material_base_price', 'service_base_price', 
        'boq_root_id.material_margin', 'boq_root_id.installation_margin',
        'work_unit_id.material_total', 'work_unit_id.service_total',
        'override_price', 'code', 'quantity'
    )
    def _compute_components_price_after_margin(self):
        for record in self:
            record.material_margin_base = 0.0
            record.service_margin_base = 0.0

            margin_mat = record.boq_root_id.material_margin or 1.0
            margin_service = record.boq_root_id.installation_margin or 1.0

            if record.code and record.code.startswith('INST') and record.override_price:
                record.service_margin_base = record.override_price
            else:
                if record.material_base_price:
                    material_price = record.material_base_price / margin_mat
                    record.material_margin_base = ceil(material_price/1000) * 1000

                if record.service_base_price:
                    service_price = record.service_base_price / margin_service
                    record.service_margin_base = ceil(service_price/1000) * 1000

    @api.depends('material_margin_base', 'service_margin_base', 'others_base_price')
    def _compute_components_price_after_margin_final(self):
        for record in self:
            record.material_margin_final = 0.0
            record.service_margin_final = 0.0

            if record.material_margin_base:
                record.material_margin_final = record.material_margin_base * record.quantity
            
            if record.service_margin_base:
                record.service_margin_final = record.service_margin_base * record.quantity

            record.final_price = sum([record.material_margin_base, record.service_margin_base, record.others_base_price])   

    @api.depends('work_unit_id', 'work_unit_id.code', 'work_unit_id.name', 'display_type')
    def _get_work_unit_components(self):
        for record in self:
            record.name = record.work_unit_id.name
            record.code = record.work_unit_id.code

    @api.depends('work_unit_id', 'work_unit_id.is_duplicate')
    def _get_duplicate_status(self):
        for record in self:
            record.is_duplicate = record.work_unit_id.is_duplicate if record.work_unit_id else False

    @api.onchange('override_price')
    def _onchange_work_unit_line_price_override(self):
        for record in self:
            if record.code and record.code.startswith('MNT'):
                record.others_base_price = record.override_price
                record.service_base_price = 0
                record.material_base_price = 0
            elif record.code and record.code.startswith('INST'):
                record.others_base_price = 0
                record.service_base_price = record.override_price
                record.material_base_price = 0

    @api.onchange('work_unit_id')
    def _onchange_work_unit_id(self):
        for record in self:
            if record.work_unit_id and record.work_unit_id.uom_id:
                record.work_unit_line_uom = record.work_unit_id.uom_id