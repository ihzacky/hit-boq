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

    material_price_total = fields.Monetary(string='Total Harga Material', currency_field='currency_id', compute="_compute_boq_price", tracking=True, store=True)
    installation_price_total = fields.Monetary(string='Total Harga Instalasi', currency_field='currency_id', compute="_compute_boq_price", tracking=True, store=True)
    maintenance_price_total = fields.Monetary(string='Total Harga Maintenance', currency_field='currency_id', compute="_compute_boq_price", tracking=True, store=True)
    price_total = fields.Monetary(string='Total Seluruh Harga', currency_field='currency_id', compute="_compute_boq_price", tracking=True, store=True)


    material_price_final = fields.Monetary(string="Total Harga Material sesudah margin", currency_field="currency_id", compute="_compute_boq_price", store=True)
    installation_price_final = fields.Monetary(string="Total Harga Instalasi sesudah margin", currency_field="currency_id", compute="_compute_boq_price", store=True)
    maintenance_price_final = fields.Monetary(string="Total Harga Maintenance sesudah margin", currency_field="currency_id", compute="_compute_boq_price", store=True)
    price_final = fields.Monetary(string="Total Seluruh Harga sesudah margin", currency_field="currency_id", compute="_compute_boq_price", store=True)


    notes_work_unit = fields.Html(string="Work Unit Notes")
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
        tracking=True,
        domain=[('is_duplicate', '=', False)]
        
    )

    work_unit_line_before_margin_ids = fields.One2many(
        comodel_name='boq.work_unit.line',
        related='work_unit_line_ids',
        string='Work Unit Lines Before Margin',
        readonly=True
    )

    work_unit_line_after_margin_ids = fields.One2many(
        comodel_name='boq.work_unit.line',
        related='work_unit_line_ids',
        string='Work Unit Lines After Margin',
        readonly=True
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
        return total, final

    def _calculate_service_prices(self, lines):
        # calculate installation and maintenance prices
        installation_total = installation_final = 0.0
        maintenance_total = maintenance_final = 0.0

        for line in lines:
            if line.work_unit_line_code.startswith('MNT'):
                maintenance_total += line.service_price_final or 0.0
                maintenance_final += line.service_price_after_margin_final or 0.0
            else:
                installation_total += line.service_price_final or 0.0
                installation_final += line.service_price_after_margin_final or 0.0

        return (installation_total, installation_final, maintenance_total, maintenance_final)

    @api.depends(
        'work_unit_line_ids',
        'work_unit_line_ids.material_price_final',
        'work_unit_line_ids.service_price_final',
        'work_unit_line_ids.material_price_after_margin_final',
        'work_unit_line_ids.service_price_after_margin_final',
        'boq_const_id.material_margin',
        'boq_const_id.installation_margin'
    )
    def _compute_boq_price(self):
        for record in self:
            lines = record.work_unit_line_ids
            material_prices = record._calculate_material_prices(lines)
            service_prices = record._calculate_service_prices(lines)
            record._update_price_fields(material_prices, service_prices)


    def _update_price_fields(self, material_prices, service_prices):
        # update all price fields
        material_total, material_final = material_prices
        (installation_total, installation_final, maintenance_total, maintenance_final) = service_prices

        self.material_price_total = material_total
        self.installation_price_total = installation_total
        self.maintenance_price_total = maintenance_total
        self.price_total = material_total + installation_total + maintenance_total

        self.material_price_final = material_final
        self.installation_price_final = installation_final
        self.maintenance_price_final = maintenance_final
        self.price_final = material_final + installation_final + maintenance_final

    @api.depends('boq_const_id')
    def _compute_const(self):
        for record in self:
            if record.boq_const_id:
                record.material_margin = record.boq_const_id.material_margin
                record.installation_margin = record.boq_const_id.installation_margin
            else:
                record.material_margin, record.installation_margin = 0.0

    # '''TO DO: Automate-kan function ini'''
    # def recompute_all(self):
    #     for record in self:
    #         lines = record.work_unit_line_ids
            
    #         record._compute_const()
    #         material_prices = record._calculate_material_prices(lines)
    #         service_prices = record._calculate_service_prices(lines)
    #         record._update_price_fields(material_prices, service_prices)
        
    #         # force recompute on work unit lines
    #         record.work_unit_line_ids.mapped('material_price_final')
    #         record.work_unit_line_ids.mapped('service_price_final')
            

    def action_print_report(self):
        return self.env.ref('hit_boq.action_report_boq').report_action(self)
