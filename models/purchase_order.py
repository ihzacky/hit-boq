from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    # All work_unit_id related code has been removed as per the code change suggestion
