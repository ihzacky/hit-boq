from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    is_boq = fields.Boolean(compute='_compute_is_boq', default=lambda self: self._compute_is_boq, store=True)
    boq_id = fields.Many2one('boq.root', default=None, store=True)
    boq_name = fields.Char(related='boq_id.boq_name', readonly=True, store=True)
    
    purchase_order_ids = fields.One2many(
        comodel_name='purchase.order', 
        inverse_name='sale_order_id', 
    )
    purchase_order_count = fields.Integer(
        compute='_compute_purchase_order_count'
    )

    @api.depends('boq_id')
    def _compute_is_boq(self):
        for record in self:
            record.is_boq = bool(record.boq_id)
    
    def action_create_rfq_wizard(self):
        if not self.boq_id:
            return {'type': 'ir.actions.act_window_close'}
            
        return {
            'name': 'Create RFQ',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.create.rfq.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_boq_id': self.boq_id.id,
            }
        }

    def action_view_pos(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'POs for {self.name}',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('origin', '=', self.name), ],
    }

    # Problem: angka ga keluar
    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)
            _logger.debug(f"Computing purchase order count for Sale Order: {record.id}, Count: {len(record.purchase_order_ids)}")