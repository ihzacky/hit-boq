from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class BoqWorkUnitLine(models.Model):
    _name = 'boq.work_unit.line'
    _description = 'BoQ Work Unit Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string="Sequence", default=1)
    is_duplicate = fields.Boolean(compute='_get_duplicate_status')
    work_unit_line_code = fields.Char(string='Kode Pekerjaan', compute='_get_work_unit_components', store=True)
    work_unit_line_name = fields.Char(string='Nama Pekerjaan', compute='_get_work_unit_components', store=True)
    work_unit_line_quantity = fields.Float(string='Quantity', default=1)
    work_unit_line_notes = fields.Text(string="Work Unit Notes")

    # Before Margin
    material_base_price = fields.Monetary(string='Material Base Price', currency_field='currency_id', compute='_get_base_price', store=True)
    material_price_final = fields.Monetary(string='Material Price', currency_field='currency_id', compute='_compute_components_price_final', store=True)
    
    service_base_price = fields.Monetary(string='Service Base Price', currency_field='currency_id', compute='_get_base_price', store=True)
    service_price_final = fields.Monetary(string='Service Price', currency_field='currency_id', compute='_compute_components_price_final', store=True)
    
    others_base_price = fields.Monetary(string='Others Base Price', currency_field='currency_id', compute='_get_base_price', store=True)
    others_price_final = fields.Monetary(string='Others Price', currency_field='currency_id', compute='_compute_components_price_final', store=True)
    
    # After Margin 
    material_base_price_after_margin = fields.Monetary(string='Material Base Price After Margin', currency_field='currency_id', compute='_compute_components_price_after_margin', store=True)
    material_price_after_margin_final = fields.Monetary(string='Material Price After Margin', currency_field='currency_id', compute='_compute_components_price_after_margin_final', store=True)

    service_base_price_after_margin = fields.Monetary(string='Service Base Price After Margin', currency_field='currency_id', compute='_compute_components_price_after_margin', store=True)
    service_price_after_margin_final = fields.Monetary(string='Service Price After Margin', currency_field='currency_id', compute='_compute_components_price_after_margin_final', store=True)
    
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
        string='BoQ Root'
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
        required=True,
        help="Unit of Measure for the work unit line"
    )

    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ], default=False
    )
    
    # before margin
    @api.depends('work_unit_id')
    def _get_base_price(self):
        for record in self:
            record.material_base_price = record.work_unit_id.materials_price
            record.service_base_price = record.work_unit_id.services_price
            record.others_base_price = record.work_unit_id.others_price
        
    @api.depends('material_base_price', 'service_base_price', 'others_base_price', 'work_unit_line_quantity')
    def _compute_components_price_final(self):
        for record in self:
            record.material_price_final = record.material_base_price * record.work_unit_line_quantity
            record.service_price_final = record.service_base_price * record.work_unit_line_quantity
            record.others_price_final = record.others_base_price * record.work_unit_line_quantity

    # after margin
    @api.depends('material_base_price', 'service_base_price', 'boq_root_id.material_margin', 'boq_root_id.installation_margin')
    def _compute_components_price_after_margin(self):
        for record in self:
            record.material_base_price_after_margin = 0.0
            record.service_base_price_after_margin = 0.0

            margin_mat = record.boq_root_id.material_margin or 1.0
            margin_service = record.boq_root_id.installation_margin or 1.0

            if record.material_base_price:
                material_price = record.material_base_price / margin_mat
                record.material_base_price_after_margin = round(material_price/1000) * 1000

            if record.service_base_price:
                service_price = record.service_base_price / margin_service
                record.service_base_price_after_margin = round(service_price/1000) * 1000

    @api.depends('material_base_price_after_margin', 'service_base_price_after_margin', 'work_unit_line_quantity')
    def _compute_components_price_after_margin_final(self):
        for record in self:
            record.material_price_after_margin_final = 0.0
            record.service_price_after_margin_final = 0.0

            if record.material_base_price_after_margin:
                record.material_price_after_margin_final = record.material_base_price_after_margin * record.work_unit_line_quantity
            
            if record.service_base_price_after_margin:
                record.service_price_after_margin_final = record.service_base_price_after_margin * record.work_unit_line_quantity

    @api.depends('work_unit_id')
    def _get_work_unit_components(self):
        for record in self:
            record.work_unit_line_code = f"{record.work_unit_id.work_unit_code}"
            record.work_unit_line_name = f"{record.work_unit_id.work_unit_name}"

    @api.depends('work_unit_id')
    def _get_duplicate_status(self):
        for record in self:
            record.is_duplicate = record.work_unit_id.is_duplicate