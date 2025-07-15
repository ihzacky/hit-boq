from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import defaultdict

class BoqAdapterPo(models.TransientModel):
    _name = 'boq.adapter.po'
    _description = 'BOQ Adapter for Purchase Order'

    boq_id = fields.Many2one('boq.root', string='BOQ', required=True, readonly=True)
    # The partner_id field is no longer needed here as it's determined automatically.

    def _get_products_and_vendors(self):
        """
        Gathers all unique, purchasable products from the BoQ lines,
        determines their vendors, and groups them.

        Returns two values:
        1. A dict of products grouped by vendor:
           {vendor_id: {product_id: {'quantity': ..., 'uom_id': ..., 'name': ...}}}
        2. A set of product names that are missing a configured vendor.
        """
        products_by_vendor = defaultdict(lambda: defaultdict(lambda: {'quantity': 0}))
        products_missing_vendor = set()

        boq_lines = self.boq_id.work_unit_line_ids.filtered(
            lambda line: not line.is_duplicate and not line.display_type
        )
        work_units = boq_lines.mapped('work_unit_id')

        all_products_lines = []
        for unit in work_units:
            for line in unit.material_line:
                if line.product_id:
                    all_products_lines.append({
                        'product': line.product_id,
                        'quantity': line.material_quantity,
                        'uom': line.material_uom
                    })
            # for line in unit.service_line:
            #     if line.product_id and line.product_id.purchase_ok:
            #         all_products_lines.append({
            #             'product': line.product_id,
            #             'quantity': line.service_quantity,
            #             'uom': line.service_uom
            #         })

        for item in all_products_lines:
            product = item['product']
            # The seller_ids are on the product.template model
            vendor = product.with_company(self.env.company)._select_seller(quantity=item['quantity'])

            if not vendor:
                products_missing_vendor.add(product.display_name)
                continue

            vendor_id = vendor.partner_id.id
            
            # Aggregate quantities for the same product under the same vendor
            agg_data = products_by_vendor[vendor_id][product.id]
            agg_data['quantity'] += item['quantity']
            agg_data['name'] = product.display_name
            agg_data['uom_id'] = item['uom'].id
            agg_data['price_unit'] = vendor.price

        return products_by_vendor, products_missing_vendor

    def action_create_po(self):
        self.ensure_one()
        
        products_by_vendor, products_missing_vendor = self._get_products_and_vendors()

        if products_missing_vendor:
            missing_products_str = "\n".join(f"- {name}" for name in sorted(list(products_missing_vendor)))
            raise UserError(
                _("Operation Aborted. The following products do not have a vendor assigned under the 'Purchase' tab. Please configure a vendor for them:\n\n%s") % missing_products_str
            )

        if not products_by_vendor:
            raise UserError(_("There are no purchasable products in this BoQ to create a Purchase Order for."))

        created_po_ids = []
        for vendor_id, products_data in products_by_vendor.items():
            po_lines = []
            for product_id, data in products_data.items():
                po_lines.append((0, 0, {
                    'product_id': product_id,
                    'name': data['name'],
                    'product_qty': data['quantity'],
                    'product_uom': data['uom_id'],
                    'price_unit': data.get('price_unit', 0.0),
                    'date_planned': fields.Datetime.now(),
                }))
            
            po = self.env['purchase.order'].create({
                'partner_id': vendor_id,
                'origin': self.boq_id.boq_code,
                'order_line': po_lines,
            })
            created_po_ids.append(po.id)

        # Return an action to open the newly created POs
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Generated Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_po_ids)],
        }
        if len(created_po_ids) == 1:
            action.update({'res_id': created_po_ids[0], 'view_mode': 'form'})
            
        return action