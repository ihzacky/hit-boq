from odoo import models, fields, api 
from odoo.fields import Command

class BoqWorkUnit(models.Model):
    _name = 'boq.work_unit'
    _description = 'BoQ Satuan Pekerjaan - Root'
    _inherit = 'mail.thread', 'mail.activity.mixin'
    _rec_name = 'code'
    _order = 'sequence, id'

    is_locked = fields.Boolean(string="Locked", default=False, compute="_compute_is_locked")
    is_duplicate = fields.Boolean(default=False, store=True)

    sequence = fields.Integer(string="Sequence", default="1")
    code = fields.Char(string='Kode Pekerjaan')
    name = fields.Char(string='Nama Pekerjaan')
    
    last_update = fields.Datetime(string="Updated Date") 
    modified_by = fields.Char(string="Updated By")
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting for Confirmation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="State", default='draft', readonly=True, tracking=True)
    
    status = fields.Char(string="Status", compute="_compute_status", readonly=True, store=True)
    revision_count = fields.Integer(default=0, readonly=True, store=True)

    price_unit = fields.Monetary(string="Total Harga Pekerjaan", currency_field="currency_id", compute="_compute_price_unit",  tracking=True, store=True)
    
    material_ids = fields.One2many(comodel_name='boq.material', inverse_name="work_unit_id", string='Satuan Pekerjaan - Material')
    material_total = fields.Monetary(string="Harga Material", currency_field="currency_id", compute="_compute_component_prices", tracking=True, store=True)
    material_notes = fields.Text(string="Material Note  ")

    service_ids = fields.One2many(comodel_name='boq.service', inverse_name="work_unit_id", string='Satuan Pekerjaan - Jasa')
    service_total = fields.Monetary(string="Harga Instalasi", currency_field="currency_id", compute="_compute_component_prices", tracking=True, store=True)
    service_notes = fields.Text(string="Services Note")

    others_ids = fields.One2many(comodel_name="boq.others", inverse_name="work_unit_id", string="Satuan Pekerjaan - Lain-Lain")
    others_price = fields.Monetary(string="Harga Lain-Lain", currency_field="currency_id", compute="_compute_component_prices", tracking=True, store=True)

    profit_percentage = fields.Float(string="Profit Percentage", tracking=True, compute="_compute_const")    
    
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

    boq_conf_id = fields.Many2one(
        comodel_name="boq.conf",
        string="BoQ Conf",
        default=lambda self: self.env['boq.conf'].get_conf().id,
        required=True
    )
    
    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit",
        tracking=True,
        required=True
    )

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid, order=order)

    @api.depends('material_total', 'service_total', 'others_price')
    def _compute_price_unit(self):
        for line in self:
            material_total = line.material_total or 0.0
            service_total = line.service_total or 0.0
            others_price = line.others_price or 0.0
            
            # calculate total price
            line.price_unit = material_total + service_total + others_price
    
    @api.depends('material_ids.product_id', 'service_ids.product_id', 'others_ids.product_id',
                 'material_ids.material_price', 'service_ids.service_price', 'others_ids.others_price_final')
    def _compute_component_prices(self):
        for record in self:
            record.material_total = sum(line.material_price for line in record.material_ids)
            record.service_total = sum(line.service_price for line in record.service_ids)
            record.others_price = sum(line.others_price_final for line in record.others_ids)
            
    # automatically create others data when code is set
    @api.onchange('code')
    def _onchange_work_unit_code(self):
        if self.code and not self.others_ids:
            self.others_ids = [
                Command.create({'others_name': 'Keuntungan'}),
                Command.create({'others_name': 'Lain-lain'}),
            ]

    def action_save(self):
        self.ensure_one()
        self.write({
            'last_update': fields.Datetime.now(),
            'modified_by': self.env.user.name
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

    def action_state_approved(self):
        self.ensure_one()
        self.write({'state': 'approved'})

    def action_state_rejected(self):
        self.ensure_one()
        self.write({'state': 'rejected'})

    def action_send_to_revision(self):
        self.ensure_one()
        self.write({'state': 'draft'})

    @api.depends('state', 'revision_count')
    def _compute_status(self):
        for record in self:
            base_status = {
                'draft': 'Draft',
                'waiting': 'Waiting for Confirmation',
                'approved': 'Approved',
                'rejected': 'Rejected'
            }.get(record.state, '')
            
            if record.revision_count > 0:
                record.status = f"Revision-{record.revision_count} ({base_status})"
            else:
                record.status = base_status

    @api.depends('state')
    def _compute_is_locked(self):
        for record in self:
            record.is_locked = record.state == 'approved'

    @api.depends('boq_conf_id')
    def _compute_const(self):
        for record in self:
            if record.boq_conf_id.exists():
                record.profit_percentage = record.boq_conf_id.profit_percentage or 0.0
            else:
                record.profit_percentage = 0.0

    def write(self, vals):
        # increment revision count
        if 'state' in vals:
            if vals['state'] == 'draft' and self.state in ['approved', 'rejected']:
                vals['revision_count'] = self.revision_count + 1
                
        # create duplicate when record is approved
        if vals.get('state') == 'approved' and not self.env.context.get('skipping_duplicate'):
            self.with_context(skipping_duplicate=True).action_duplicate_on_approval()
                
        return super().write(vals)

    # creates a duplicate record with the same components and marked as a duplicate
    @api.depends('material_ids', 'service_ids', 'others_ids')
    def action_duplicate_on_approval(self):
        for record in self:
            existing_duplicate = self.search([
                ('code', '=', record.code),
                ('is_duplicate', '=', True),
                ('state', '=', 'approved'),
            ], limit=1)
            
            if existing_duplicate:
                # Clear existing records in duplicate
                existing_duplicate.material_ids.unlink()
                existing_duplicate.service_ids.unlink()
                existing_duplicate.others_ids.unlink()
                
                # Create new copies for materials
                for material in record.material_ids:
                    material.copy({
                        'work_unit_id': existing_duplicate.id
                    })
                
                # Create new copies for services
                for service in record.service_ids:
                    service.copy({
                        'work_unit_id': existing_duplicate.id
                    })
                
                # Create new copies for others
                for other in record.others_ids:
                    other.copy({
                        'work_unit_id': existing_duplicate.id
                    })
                
                # Update other fields
                existing_duplicate.with_context(skipping_duplicate=True).write({
                    'status': record.status,
                    'state': 'approved',
                    'modified_by': record.modified_by,
                    'last_update': record.last_update
                })
            
            else:
                # Create new duplicate record
                duplicated_record = record.copy({
                    'is_duplicate': True,
                    'state': 'approved'
                })
                
                # Copy materials
                for material in record.material_ids:
                    material.copy({
                        'work_unit_id': duplicated_record.id
                    })
                
                # Copy services
                for service in record.service_ids:
                    service.copy({
                        'work_unit_id': duplicated_record.id
                    })
                
                # Copy others
                for other in record.others_ids:
                    other.copy({
                        'work_unit_id': duplicated_record.id
                    })

    def action_revert_to_previous(self):
        # reverts the current data to its previous approved version by copying/overwite all values
        for record in self:
            previous_version = self.search([
                ('code', '=', record.code),
                ('is_duplicate', '=', True),
                ('state', '=', 'approved')
            ], limit=1)
            
            if previous_version:              
                materials_to_create = []
                for material in previous_version.material_ids:
                    materials_to_create.append({
                        'work_unit_id': record.id,
                        'product_id': material.product_id.id,
                        'material_quantity': material.material_quantity,
                        'material_uom': material.material_uom.id,
                    })
                
                services_to_create = []
                for service in previous_version.service_ids:
                    services_to_create.append({
                        'work_unit_id': record.id,
                        'product_id': service.product_id.id,
                        'service_quantity': service.service_quantity,
                    })
                
                others_to_create = []
                for other in previous_version.others_ids:
                    others_to_create.append({
                        'work_unit_id': record.id,
                        'others_name': other.others_name,
                        'others_base_price': other.others_base_price,
                    })
                
                if record.material_ids:
                    record.material_ids.unlink()
                if record.service_ids:
                    record.service_ids.unlink()
                if record.others_ids:
                    record.others_ids.unlink()
                
                # Create new records
                for vals in materials_to_create:
                    self.env['boq.material'].create(vals)
                for vals in services_to_create:
                    self.env['boq.service'].create(vals)
                for vals in others_to_create:
                    self.env['boq.others'].create(vals)

                
                return True

    def unlink(self):
        for record in self:
            if not record.is_duplicate:
                # Find and delete the duplicate record
                duplicate = self.search([
                    ('code', '=', record.code),
                    ('is_duplicate', '=', True)
                ])
                if duplicate:
                    duplicate.with_context(skip_unlink_check=True).unlink()
            elif self.env.context.get('skip_unlink_check'):
                # Allow deletion of duplicate when called from parent deletion
                return super().unlink()
            else:
                # Prevent direct deletion of duplicates
                raise models.ValidationError('Cannot delete duplicate records directly. Delete the original record instead.')
                
        return super().unlink()


