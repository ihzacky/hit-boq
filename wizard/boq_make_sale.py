from odoo import models, fields, api

class BoqAdapterSale(models.TransientModel):
    _name = 'boq.adapter.sale'
    _description = 'Boq Adapter to Sale Order'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        required=True, change_default=True, index=True,
        check_company=True
    )
    payment_term_id = fields.Many2one(comodel_name='account.payment.term',
        string="Payment Terms",
        store=True, readonly=False, precompute=True, check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    company_id = fields.Many2one(
        'res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    boq_id = fields.Many2one(
        comodel_name='boq.root',
        required=True
    )
    
    def create_sale_order(self):
        sale_order = self.env['sale.order'].create({
            'origin': f'BoQ {self.boq_id.boq_code}',
            'date_order': fields.Datetime.now(),
            'partner_id': self.partner_id.id,
            'payment_term_id': self.payment_term_id.id,
            'state': 'draft',
            'boq_id': self.boq_id.id,
            'boq_name': self.boq_id.boq_name
        })

        self.create_sale_order_line(sale_order.id)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'create': False}
        }

    def create_sale_order_line(self, sale_order_ids):
        product = self.env['product.product'].search([
            ('name', '=', 'BoQ Work Unit'),
            ('type', '=', 'service')
        ], limit=1)

        if not product:
            product = self.env['product.product'].create({
                'name': 'BoQ Work Unit',
                'type': 'service',
                'detailed_type': 'service', 
            })

        for line in self.boq_id.work_unit_line_ids:
            if line.display_type:
                # section or note lines
                vals = {
                    'order_id': sale_order_ids,
                    'display_type': line.display_type,
                    'name': line.name,
                    'sequence': line.sequence,
                    'product_id': False,
                    'product_uom_qty': 0,
                    'price_unit': 0,
                    'product_uom': False,
                }
            else:
                # regular lines
                vals = {
                    'order_id': sale_order_ids,
                    'display_type': line.display_type,
                    'sequence': line.sequence,
                    'name': line.name,
                    'product_id': product.id,
                    'product_uom': line.work_unit_line_uom.id,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.final_price,
                }
            
            self.env['sale.order.line'].create(vals)


