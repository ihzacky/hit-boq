from odoo import models, fields, api, Command
from odoo.exceptions import ValidationError


class SaleOrderCreateRfqWizard(models.TransientModel):
    _name = 'sale.order.create.rfq.wizard'
    _description = 'Create RFQ'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    boq_id = fields.Many2one('boq.root', string='BoQ', required=True)
    work_unit_line_ids = fields.One2many(
        'sale.order.create.rfq.wizard.line', 
        'wizard_id', 
        string='Work Units'
    )
    select_all = fields.Boolean(string='Select All', default=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'sale_order_id' in res and 'boq_id' in res:
            sale_order = self.env['sale.order'].browse(res['sale_order_id'])
            boq = self.env['boq.root'].browse(res['boq_id'])
            
            # Get work units from BoQ through work_unit_line_ids
            work_unit_lines = []
            for work_unit_line in boq.work_unit_line_ids:
                work_unit = work_unit_line.work_unit_id
                if work_unit and work_unit.material_line:
                    work_unit_lines.append(Command.create({
                        'work_unit_id': work_unit.id,
                        'selected': False,
                    }))
            res['work_unit_line_ids'] = work_unit_lines
        return res

    @api.onchange('select_all')
    def _onchange_select_all(self):
        for line in self.work_unit_line_ids:
            line.selected = self.select_all

    def action_create_rfq(self):
        selected_lines = self.work_unit_line_ids.filtered('selected')
        if not selected_lines:
            raise ValidationError("Please select at least one work unit.")

        default_vendor = None
        order_lines = []
        vendors = set()
        
        for line in selected_lines:
            work_unit = line.work_unit_id
            for material_line in work_unit.material_line:
                if material_line.product_id:

                    product_vendor = None
                    if material_line.product_id.seller_ids:
                        
                        # for now use the first (latest/top) vendor from vendor list
                        product_vendor = material_line.product_id.seller_ids[0].partner_id
                        vendors.add(product_vendor.id)
                    
                    order_line_vals = {
                        'product_id': material_line.product_id.id,
                        'name': material_line.material_description or material_line.product_id.name,
                        'product_qty': material_line.material_quantity,
                        'product_uom': material_line.material_uom.id,
                        'price_unit': material_line.material_base_price,
                    }
                    order_lines.append(Command.create(order_line_vals))
        
        if not vendors:
            raise ValidationError(
                "No vendors found for the selected materials. "
                "Please ensure all products have suppliers defined before creating RFQ."
            )
        
        default_vendor = list(vendors)[0]

        rfq_vals = {
            'partner_id': default_vendor,
            'origin': self.sale_order_id.name,
            'order_line': order_lines,
            'sale_order_id': self.sale_order_id.id,
        }

        rfq = self.env['purchase.order'].create(rfq_vals)
        rfq.write({'sale_order_id': self.sale_order_id.id})

        return {
            'name': 'Request for Quotation',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': rfq.id,
            'target': 'current',
        }

class SaleOrderCreateRfqWizardLine(models.TransientModel):
    _name = 'sale.order.create.rfq.wizard.line'
    _description = 'Create RFQ Wizard Line'

    wizard_id = fields.Many2one('sale.order.create.rfq.wizard', string='Wizard')
    work_unit_id = fields.Many2one('boq.work_unit', string='Work Unit', required=True)
    work_unit_name = fields.Char(related='work_unit_id.name', string='Work Unit Name')
    work_unit_code = fields.Char(related='work_unit_id.code', string='Work Unit Code')
    material_count = fields.Integer(string='Material Count', compute='_compute_material_count')
    selected = fields.Boolean(string='Select', default=False)

    @api.depends('work_unit_id.material_line')
    def _compute_material_count(self):
        for record in self:
            record.material_count = len(record.work_unit_id.material_line)
