from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    work_unit_ids = fields.Many2many(
        'boq.work_unit', 
        'purchase_order_work_unit_rel',  # Add explicit relation table
        'purchase_order_id',             # Add explicit column names
        'work_unit_id',
        string='Work Units'
    )
    sale_order_id = fields.Many2one('sale.order', string='Source Sale Order', help='Sale order that created this RFQ')
