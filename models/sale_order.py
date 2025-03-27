from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    is_boq = fields.Boolean(compute='_compute_is_boq', default=lambda self: self._compute_is_boq, store=True)
    boq_id = fields.Many2one('boq.root', default=None, store=True)
    boq_name = fields.Char(related='boq_id.boq_name', readonly=True, store=True)
   
    @api.depends('boq_id')
    def _compute_is_boq(self):
        for record in self:
            record.is_boq = bool(record.boq_id)  