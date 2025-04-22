from odoo.tests.common import TransactionCase
from odoo.tools import float_compare
from math import ceil

class TestBoqWorkUnitLine(TransactionCase):
    def setUp(self):
        super(TestBoqWorkUnitLine, self).setUp()
        self._setup_configuration()
        self._setup_products()
        self._setup_work_units()
        self._setup_boq_components()
        
    def _setup_configuration(self):

        self.boq_conf = self.env['boq.conf'].create({
            'profit_percentage': 15,
            'material_margin': 0.95,
            'installation_margin': 0.95,
        })
        
        self.boq_root = self.env['boq.root'].create({
            'boq_code': 'BOQ-TEST-001',
            'boq_name': 'Test BoQ',
            'boq_conf_id': self.boq_conf.id,
        })
        
        self.uom = self.env.ref('uom.product_uom_unit')
        self.currency = self.env.ref('base.IDR')
    
    def _setup_products(self):

        self.upah_tag = self.env['product.tag'].search([('name', '=', 'Upah')], limit=1)
        if not self.upah_tag:
            self.upah_tag = self.env['product.tag'].create({
                'name': 'Upah'
            })
        
        self.material_instalasi_tag = self.env['product.tag'].search([('name', '=', 'Material Instalasi')], limit=1)
        if not self.material_instalasi_tag:
            self.material_instalasi_tag = self.env['product.tag'].create({
                'name': 'Material Instalasi'
            })
        
        self.product_service = self.env['product.product'].create({
            'name': 'Network Engineer',
            'lst_price': 1_218_000,
            'type': 'service',
            'is_service': True,
            'product_tag_ids': [(6, 0, [self.upah_tag.id])]
        })

        self.product_material = self.env['product.product'].create({
            'name': 'ICOM model MA510TR (VHF Antenna + GPS + Cabling)',
            'lst_price': 15_500_000,
            'type': 'consu',
            'is_material': True,
        })
    
    def _setup_work_units(self):

        self.work_unit_ais = self.env['boq.work_unit'].create({
            'code': 'INST-084',
            'name': 'Installasi AIS',
            'uom_id': self.uom.id,
            'boq_conf_id': self.boq_conf.id,
            'state': 'approved',
            # 'material_total': 18_235_300,
            # 'service_total': 6_363_000,
            'others_price': 0,
        })

        self.work_unit_pc_server = self.env['boq.work_unit'].create({
            'code': 'INST-085B',
            'name': 'Installasi PC Server AIS',
            'uom_id': self.uom.id,
            'boq_conf_id': self.boq_conf.id,
            'state': 'approved',
            'material_total': 22_911_000,
            'service_total': 1_503_000,
            'others_price': 0,
        })

        self.work_unit_cctv = self.env['boq.work_unit'].create({
            'code': 'INST-097',
            'name': 'Instalasi Perangkat CCTV HIKVISION MINI PTZ COLORVU 4MP',
            'uom_id': self.uom.id,
            'boq_conf_id': self.boq_conf.id,
            'state': 'approved',
            'material_total': 3_902_000,
            'service_total': 4_708_000,
            'others_price': 0,
        })
        
        self.work_unit_maintenance = self.env['boq.work_unit'].create({
            'code': 'MNT-001',
            'name': 'Maintenance Service',
            'uom_id': self.uom.id,
            'boq_conf_id': self.boq_conf.id,
            'state': 'approved',
            'others_price': 0,
            # 'service_total': 5_000_000,
            # 'others_price': 2_000_000,
        })
    
    def _setup_boq_components(self):
        """Set up BOQ components (materials and services)"""

        self.boq_material = self.env['boq.material'].create({
            'work_unit_id': self.work_unit_ais.id,
            'product_id': self.product_material.id,
            'material_quantity': 1,
            # 'boq_conf_id': self.boq_conf.id,
        })

        self.boq_service = self.env['boq.service'].create({
            'work_unit_id': self.work_unit_ais.id,
            'product_id': self.product_service.id,
            'service_quantity': 0.3,
        })

        self.work_unit_ais.write({
            'material_ids': [(4, self.boq_material.id, 0)],  
            'service_ids': [(4, self.boq_service.id, 0)] 
        })

        self.boq_service_mnt = self.env['boq.service'].create({
            'work_unit_id': self.work_unit_maintenance.id,
            'product_id': self.product_service.id,
            'service_quantity': 0.7,
        })

        self.work_unit_maintenance.write({
            'service_ids': [(4, self.boq_service_mnt.id, 0)]
        })
    
    def _create_work_unit_line(self, work_unit, quantity=1):
  
        return self.env['boq.work_unit.line'].create({
            'work_unit_id': work_unit.id,
            'boq_root_id': self.boq_root.id,
            'quantity': quantity,
            'name': work_unit.name,
            'code': work_unit.code if hasattr(work_unit, 'code') else None,
        })

    def test_01_default_values(self):

        work_unit_line = self._create_work_unit_line(self.work_unit_ais)
        
        self.assertEqual(self.boq_root.material_margin, 0.95, "Material margin should be 0.95")
        self.assertEqual(self.boq_root.installation_margin, 0.95, "Installation margin should be 0.95")
        self.assertEqual(self.work_unit_ais.profit_percentage, 15, "Profit percentage should be 15")
        
        print("TEST PASSED: Default margins and profit percentage test passed successfully")

    def test_02_base_computation(self):

        work_unit_line = self._create_work_unit_line(self.work_unit_ais)
        
        expected_material_base = ceil(self.work_unit_ais.material_total / 1000) * 1000
        expected_service_base = ceil(self.work_unit_ais.service_total / 1000) * 1000
        
        self.assertEqual(work_unit_line.material_base_price, expected_material_base, 
                        f"Material base price should be {expected_material_base}")
        self.assertEqual(work_unit_line.service_base_price, expected_service_base, 
                        f"Service base price should be {expected_service_base}")
        
        print("TEST PASSED: Base computation test passed successfully")

    def test_03_price_component_calculation(self):

        work_unit_line = self._create_work_unit_line(self.work_unit_cctv, quantity=2)
        
        expected_material_base = ceil(self.work_unit_cctv.material_total / 1000) * 1000
        expected_service_base = ceil(self.work_unit_cctv.service_total / 1000) * 1000
        
        expected_material_final = expected_material_base * 2
        expected_service_final = expected_service_base * 2
        
        self.assertEqual(work_unit_line.material_price_final, expected_material_final, 
                        f"Material price final should be {expected_material_final}")
        self.assertEqual(work_unit_line.service_price_final, expected_service_final,  
                        f"Service price final should be {expected_service_final}")
        
        print("TEST PASSED: Price component calculation test passed successfully")

    def test_04_profit_calculation(self):

        work_unit_line = self._create_work_unit_line(self.work_unit_maintenance)
        
        expected_others_price = ceil(self.work_unit_maintenance.others_price / 1000) * 1000
        self.assertEqual(work_unit_line.others_base_price, expected_others_price, 
                        f"Others base price should be {expected_others_price}")
        
        print("TEST PASSED: Profit calculation test passed successfully")

    def test_05_margin_application(self):

        work_unit_line = self._create_work_unit_line(self.work_unit_pc_server)
        
        material_base = work_unit_line.material_base_price
        service_base = work_unit_line.service_base_price
        
        material_margin = material_base / self.boq_root.material_margin
        expected_material_margin_base = ceil(material_margin / 1000) * 1000
        
        service_margin = service_base / self.boq_root.installation_margin
        expected_service_margin_base = ceil(service_margin / 1000) * 1000
        
        self.assertAlmostEqual(work_unit_line.material_margin_base, expected_material_margin_base,
                              msg=f"Material margin base should be approximately {expected_material_margin_base}")
        self.assertAlmostEqual(work_unit_line.service_margin_base, expected_service_margin_base, 
                              msg=f"Service margin base should be approximately {expected_service_margin_base}")
        
        print("TEST PASSED: Margin application test passed successfully")

    def test_06_quantity_multiplication(self):
  
        work_unit_line = self._create_work_unit_line(self.work_unit_cctv, quantity=3)
        
        material_margin_base = work_unit_line.material_margin_base
        service_margin_base = work_unit_line.service_margin_base
        
        expected_material_margin_final = material_margin_base * 3
        expected_service_margin_final = service_margin_base * 3
        
        self.assertEqual(work_unit_line.material_margin_final, expected_material_margin_final,
                        f"Material margin final should be {expected_material_margin_final}")
        self.assertEqual(work_unit_line.service_margin_final, expected_service_margin_final,
                        f"Service margin final should be {expected_service_margin_final}")
        
        expected_final_price = material_margin_base + service_margin_base + work_unit_line.others_base_price
        self.assertEqual(work_unit_line.final_price, expected_final_price, 
                        f"Final price should be {expected_final_price}")
        
        print("TEST PASSED: Quantity multiplication test passed successfully")

    def test_07_update_test(self):

        work_unit_line = self._create_work_unit_line(self.work_unit_ais)

        work_unit_line._get_work_unit_components()
        work_unit_line._get_base_price()
        work_unit_line._compute_components_price_final()

        initial_final_price = work_unit_line.final_price
        initial_material_final_price = work_unit_line.material_price_final
        initial_service_final_price = work_unit_line.service_price_final
       
        # print("DEBUG: Initial final price:", initial_final_price)
        # print("DEBUG: Initial material final price:", initial_material_final_price)
        # print("DEBUG: Initial service final price:", initial_service_final_price)
        # print("DEBUG: Material base price:", work_unit_line.material_base_price)
        # print("DEBUG: Service base price:", work_unit_line.service_base_price)
        # print("DEBUG: Others base price:", work_unit_line.others_base_price)
        # print("DEBUG: Quantity before update:", work_unit_line.quantity)
        # print("DEBUG: Material price final:", work_unit_line.material_price_final)
        # print("DEBUG: Service price final:", work_unit_line.service_price_final)
        # print("DEBUG: Others price final:", work_unit_line.others_price_final)
        # print("===============================before")
        

        work_unit_line.write({'quantity': 3})
        # print("DEBUG: Quantity after update:", work_unit_line.quantity)
        work_unit_line._compute_components_price_final()

        # print("DEBUG: Material final price after quantity update:", work_unit_line.material_price_final)
        # print("DEBUG: Initial material final price:", initial_material_final_price)
        
        # Test price changes after quantity update
        if work_unit_line.material_price_final != 0:
            self.assertNotEqual(work_unit_line.material_price_final, initial_material_final_price, 
                               "Material price final should change after quantity update")
        if work_unit_line.service_price_final != 0:
            self.assertNotEqual(work_unit_line.service_price_final, initial_service_final_price, 
                               "Service price final should change after quantity update")
        
        work_unit_line.write({'override_price': 10_000_000})
        
        self.assertEqual(work_unit_line.service_base_price, 10_000_000, 
                        "Service base price should equal override price for INST code")
        self.assertEqual(work_unit_line.material_base_price, 0, 
                        "Material base price should be 0 when override price is set for INST code")
        
        print("TEST PASSED: Update test passed successfully")

    def test_08_boq_root_final_price_calculation(self):

        work_unit_line = self._create_work_unit_line(self.work_unit_ais)
        work_unit_line_mnt = self._create_work_unit_line(self.work_unit_maintenance)
        
        work_unit_line._get_work_unit_components()
        work_unit_line._get_base_price()
        work_unit_line._compute_components_price_final()
        
        # print("DEBUG: work unit line code:", work_unit_line.code)
        # print("DEBUG: material margin:", self.boq_root.material_margin)
        # print("DEBUG: installation margin:", self.boq_root.installation_margin)
        
        # print("DEBUG: wul-material base price:", work_unit_line.material_base_price)
        # print("DEBUG: wul-service base price:", work_unit_line.service_base_price)
        # print("DEBUG: wul-service price final:", work_unit_line.service_price_final)

        # Recompute all prices
        self.boq_root.action_recompute_all_prices()

        # print("DEBUG: material_base_cost", self.boq_root.material_base_cost)
        # print("DEBUG: installation_base_cost", self.boq_root.installation_base_cost)
        
        self.assertGreater(self.boq_root.material_base_cost, 0, 
                          "Material base cost should be greater than 0")
        self.assertGreater(self.boq_root.installation_base_cost, 0, 
                          "Installation base cost should be greater than 0")
        self.assertGreater(self.boq_root.price_subtotal, 0, 
                          "Price subtotal should be greater than 0")
        self.assertGreater(self.boq_root.maintenance_base_total, 0, 
                          "Maintenance base total should be greater than 0")
        
        print("TEST PASSED: BoQ Root final price calculation test passed successfully")
