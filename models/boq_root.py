from odoo import models, fields, api


class BoqRoot(models.Model):
    _name = 'boq.root'
    _description = 'BoQ Root'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'boq_code'

    boq_code = fields.Char(string='Kode BoQ')
    boq_name = fields.Char(string='Nama')
    
    updated_date = fields.Datetime(string="Updated Date") 
    updated_by = fields.Char(string="Updated By")
    
    material_margin = fields.Float(string='Material Margin', compute="_compute_const", store=True)
    installation_margin = fields.Float(string='Installation Margin', compute="_compute_const", store=True)
    updated_date = fields.Datetime(string="Updated Date") 
    updated_by = fields.Char(string="Updated By")

    # before margin
    material_price_total = fields.Monetary(string='Total Harga Material', currency_field='currency_id', compute="_compute_boq_price", tracking=True, store=True)
    installation_price_total = fields.Monetary(string='Total Harga Instalasi', currency_field='currency_id', compute="_compute_boq_price", tracking=True, store=True)
    
    maintenance_price_inst_total = fields.Monetary(currency_field='currency_id', compute="_compute_maintenance_price", tracking=True, store=True)
    maintenance_price_others_total = fields.Monetary(currency_field='currency_id', compute="_compute_maintenance_price", tracking=True, store=True)
    maintenance_price_total = fields.Monetary(string='Total Harga Maintenance', currency_field='currency_id', compute="_compute_maintenance_price", tracking=True, store=True)
    
    price_total = fields.Monetary(string='Total Seluruh Harga', currency_field='currency_id', compute="_compute_boq_price", tracking=True, store=True)

    # after margin
    material_price_final = fields.Monetary(string="Total Harga Material sesudah margin", currency_field="currency_id", compute="_compute_boq_price", store=True)
    installation_price_final = fields.Monetary(string="Total Harga Instalasi sesudah margin", currency_field="currency_id", compute="_compute_boq_price", store=True)
    
    maintenance_price_inst_final = fields.Monetary(currency_field="currency_id", compute="_compute_maintenance_price", store=True)
    maintenance_price_others_final = fields.Monetary(currency_field="currency_id", compute="_compute_maintenance_price", store=True)
    maintenance_price_final = fields.Monetary(string="Total Harga Maintenance sesudah margin", currency_field="currency_id", compute="_compute_maintenance_price", store=True)
    
    price_final = fields.Monetary(string="Total Seluruh Harga sesudah margin", currency_field="currency_id", compute="_compute_boq_price", store=True)

    notes_general = fields.Html(string="BoQ Notes")
    notes_exclude = fields.Html(string="Exclude Notes")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
    ], string='Status', default='draft', tracking=True)

    work_unit_line_ids = fields.One2many(
        comodel_name='boq.work_unit.line',
        inverse_name='boq_root_id',
        string='Work Unit Lines',
        domain=[('is_duplicate', '=', False)]
    )

    work_unit_line_before_margin_ids = fields.One2many(
        comodel_name='boq.work_unit.line',
        string='Work Unit Lines Before Margin',
        compute='_compute_work_unit_line_before_margin_ids'
    )

    work_unit_line_after_margin_ids = fields.One2many(
        comodel_name='boq.work_unit.line',
        string='Work Unit Lines After Margin',
        compute='_compute_work_unit_line_after_margin_ids'
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency", 
        string="Currency", 
        default=lambda self: self.env.ref('base.IDR'),
        readonly=True,
    )

    boq_const_id = fields.Many2one(
        comodel_name="boq.const", 
        string="BoQ Const",
        default=1
    )
    
    def write(self, vals):
        vals.update({
            'updated_date': fields.Datetime.now(),
            'updated_by': self.env.user.name,
        })
        return super(BoqRoot, self).write(vals)

    def _calculate_material_prices(self, lines):
        # calculate material prices before and after margin
        total = sum(line.material_price_final or 0.0 for line in lines)
        final = sum(line.material_price_after_margin_final or 0.0 for line in lines)
        return (total, final)

    def _calculate_installation_prices(self, lines):
        installation_total = sum(
            line.service_price_final or 0.0
            for line in lines
            if line.work_unit_line_code and not line.work_unit_line_code.startswith('MNT')
        )
        installation_final = sum(
            line.service_price_after_margin_final or 0.0
            for line in lines
            if line.work_unit_line_code and not line.work_unit_line_code.startswith('MNT')
        )
        return (installation_total, installation_final)      


    @api.depends(
        'work_unit_line_ids',
        'work_unit_line_ids.material_price_final',
        'work_unit_line_ids.service_price_final',
        'work_unit_line_ids.others_price_final',
        'work_unit_line_ids.material_price_after_margin_final',
        'work_unit_line_ids.service_price_after_margin_final',
        'work_unit_line_ids.work_unit_line_code',
    )
    def _compute_boq_price(self):
        for record in self:
            lines = record.work_unit_line_ids

            (material_total, material_final) = record._calculate_material_prices(lines)
            (installation_total, installation_final) = record._calculate_installation_prices(lines)

            record.material_price_total = material_total
            record.installation_price_total = installation_total
            record.price_total = sum([material_total, installation_total])

            record.material_price_final = material_final
            record.installation_price_final = installation_final
            record.price_final = sum([material_final, installation_final])

    @api.depends(
        'work_unit_line_ids', 
        'work_unit_line_ids.service_price_final', 
        'work_unit_line_ids.others_price_final',
        'work_unit_line_ids.service_price_after_margin_final',
        'work_unit_line_ids.work_unit_line_code'  # Add this dependency
    )
    def _compute_maintenance_price(self):
        for record in self:
            lines = record.work_unit_line_ids

            record.maintenance_price_inst_total = sum(
                line.service_price_final or 0.0 
                for line in lines 
                if line.work_unit_line_code and line.work_unit_line_code.startswith('MNT')
            )
            record.maintenance_price_others_total = sum(
                line.others_price_final or 0.0 
                for line in lines 
                if line.work_unit_line_code and line.work_unit_line_code.startswith('MNT')
            )
            record.maintenance_price_total = record.maintenance_price_inst_total + record.maintenance_price_others_total

            record.maintenance_price_inst_final = sum(
                line.service_price_after_margin_final or 0.0 
                for line in lines 
                if line.work_unit_line_code and line.work_unit_line_code.startswith('MNT')
            )
            record.maintenance_price_others_final = sum(
                line.others_price_final or 0.0 
                for line in lines 
                if line.work_unit_line_code and line.work_unit_line_code.startswith('MNT')
            )
            record.maintenance_price_final = record.maintenance_price_inst_final + record.maintenance_price_others_final

    @api.depends('boq_const_id.material_margin', 'boq_const_id.installation_margin')
    def _compute_const(self):
        for record in self:
            if record.boq_const_id:
                record.material_margin = record.boq_const_id.material_margin
                record.installation_margin = record.boq_const_id.installation_margin
            else:
                record.material_margin, record.installation_margin = 0.0

    @api.depends('work_unit_line_ids')
    def _compute_work_unit_line_before_margin_ids(self):
        for record in self:
            record.work_unit_line_before_margin_ids = record.work_unit_line_ids.filtered(
                lambda line: not line.display_type
            )

    @api.depends('work_unit_line_ids')
    def _compute_work_unit_line_after_margin_ids(self):
        for record in self:
            record.work_unit_line_after_margin_ids = record.work_unit_line_ids.filtered(
                lambda line: not line.display_type
            )

    def _compute_preview_html(self):
        for record in self:
            record.preview_html = self.env['ir.qweb']._render(
                'hit_boq.report_boq', {'docs': record}
            )

    preview_html = fields.Html(compute="_compute_preview_html", sanitize=False)

    def preview_pdf(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'views': [(self.env.ref('hit_boq.view_boq_root_preview_form').id, 'form')],
            'context': {
                'default_print_preview': True,
            }
        }

    def action_print_report(self):
        return self.env.ref('hit_boq.action_report_boq').report_action(self)
