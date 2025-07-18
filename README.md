# Hit BoQ Module - Technical Documentation

## Overview

The Hit BoQ (Bill of Quantities) module is a comprehensive Odoo 17 application designed to manage construction project cost estimation and procurement workflows. It provides a complete solution for creating detailed BOQs, managing work units, calculating margins, and integrating with sales orders and purchase requisitions.

## Dependencies

The module depends on the following Odoo modules:
- `base` - Core Odoo functionality
- `product` - Product management
- `mail` - Mail and activity tracking
- `sale` - Sales order management
- `purchase` - Purchase order management
- `project` - Project management integration

External Modules:
- `ssi_multiple_approval_mixin` - Approval workflow functionality
- `winprof_approval` - Custom approval processes

## Architecture Overview

### Core Models

#### 1. `boq.root` - Main BoQ Model
The central model that represents a complete Bill of Quantities document.

**Key Features:**
- Hierarchical cost calculation with margins
- Integration with sale orders and purchase orders
- Material, installation, and maintenance cost tracking
- Currency support (default: IDR)
- Multi-state workflow (draft → confirm → done)

**Important Fields:**
```python
# Identification
boq_code = fields.Char('Kode BoQ')
boq_name = fields.Char('Nama')

# Cost Calculations (Before Margin)
material_base_cost = fields.Monetary('Total Harga Material')
installation_base_cost = fields.Monetary('Total Harga Instalasi')
maintenance_base_total = fields.Monetary('Total Harga Maintenance')

# Cost Calculations (After Margin)
material_price_final = fields.Monetary('Total Harga Material sesudah margin')
installation_price_final = fields.Monetary('Total Harga Instalasi sesudah margin')
maintenance_final = fields.Monetary('Total Harga Maintenance sesudah margin')
price_final = fields.Monetary('Final Price')

# Relations
work_unit_line_ids = fields.One2many('boq.work_unit.line', 'boq_root_id')
sale_order_ids = fields.One2many('sale.order', 'boq_id')
```

#### 2. `boq.work_unit` - Work Unit Definition
Represents individual work units that can be reused across multiple BoQs.

**Key Features:**
- Approval workflow integration
- Material, service, and other cost components
- Revision tracking
- Lock mechanism to prevent changes during approval

**Important Fields:**
```python
# Core Information
code = fields.Char('Kode Pekerjaan')
name = fields.Char('Nama Pekerjaan')
state = fields.Selection([('draft', 'Draft'), ('to_approve', 'Waiting for Confirmation'), 
                         ('approved', 'Approved'), ('rejected', 'Rejected')])

# Cost Components
material_line = fields.One2many('boq.material.line', 'work_unit_id')
service_line = fields.One2many('boq.service.line', 'work_unit_id')
others_ids = fields.One2many('boq.others', 'work_unit_id')

# Calculated Totals
price_unit = fields.Monetary('Total Harga Pekerjaan')
material_total = fields.Monetary('Harga Material')
service_total = fields.Monetary('Harga Instalasi')
```

#### 3. `boq.work_unit.line` - BoQ Work Unit Instance
Links work units to specific BoQs with quantity and override capabilities.

**Key Features:**
- Quantity-based cost calculation
- Price override functionality
- Final cost computation with margins

#### 4. Component Models

**Material Lines (`boq.material.line`)**
- Product-based material cost calculation
- Quantity and unit price management
- Integration with product catalog

**Service Lines (`boq.service.line`)**
- Service/labor cost calculation
- Installation and maintenance services
- Custom pricing support

**Others (`boq.others`)**
- Miscellaneous costs
- Flexible cost categorization

#### 5. Configuration (`boq.conf`)
Central configuration for margins and pricing parameters.

**Key Configuration Fields:**
```python
material_margin = fields.Float('Material Margin')
installation_margin = fields.Float('Installation Margin')
maintenance_margin = fields.Float('Maintenance Margin')
profit_percentage = fields.Float('Profit Percentage')
```

### Integration Models

#### Sales Integration (`sale.order` extension)
- Adds BoQ-specific fields to sale orders
- Custom buttons for project creation and RFQ generation
- Purchase order count tracking

**Extended Fields:**
```python
is_boq = fields.Boolean('Is BoQ')
boq_id = fields.Many2one('boq.root', 'BoQ')
boq_name = fields.Char('BoQ Name')
purchase_order_count = fields.Integer('Purchase Order Count')
```

#### Purchase Integration (`purchase.order` extension)
- Links purchase orders to BoQ work units
- Cost tracking for procurement

#### Product Integration (`product.product` extension)
- BoQ-specific product categorization
- Special product tags for BoQ items

## Data Flow

### 1. BoQ Creation Workflow
```
1. Create BoQ Root → 2. Add Work Units → 3. Configure Materials/Services → 
4. Calculate Costs → 5. Generate Sale Order → 6. Create RFQ → 7. Project Creation
```

### 2. Work Unit Approval Workflow
```
Draft → To Approve → Approved/Rejected
```

### 3. Cost Calculation Flow
```
Base Costs → Apply Margins → Calculate Finals → Aggregate to BoQ Total
```

## Key Business Logic

### Cost Calculation Algorithm

1. **Material Costs**: Sum of (quantity × unit_price) for all materials
2. **Service Costs**: Sum of service line costs (installation + maintenance)
3. **Margin Application**: Base cost × (1 + margin_percentage)
4. **Final Calculation**: Sum of all component finals + profit

### Price Override Logic
- Work unit line level overrides take precedence
- Override affects final calculations but preserves base costs
- Supports selective overriding of material vs. service costs

### Maintenance Cost Categorization
- Installation-based maintenance: Calculated from service lines with 'MNT' prefix
- Others-based maintenance: From boq.others records
- Separate margin application for each category

## User Interface Structure

### Menu Hierarchy
```
BoQ/
├── All BoQ/
│   ├── Home (BoQ List)
│   └── BoQ Configuration
├── Satuan Pekerjaan/
│   └── Home (Work Units List)
├── Sales/
│   ├── BoQ Quotations
│   └── BoQ Sale Orders
└── Approval/
    └── Work Unit Approval
```

### Key Views

#### BoQ Root Views
- **Tree View**: Summary list with key metrics
- **Form View**: Detailed cost breakdown and work unit management
- **Report View**: Printable BoQ document

#### Work Unit Views
- **Tree View**: Work unit catalog with status
- **Form View**: Detailed component management
- **Approval View**: Workflow management interface

## Wizards

### 1. BoQ Make Sale (`boq.make.sale`)
Converts approved BoQ to sale order with proper line item mapping.

### 2. Create RFQ (`sale.order.create.rfq.wizard`)
Generates purchase requisitions from sale order work units.

**Key Features:**
- Selective work unit inclusion
- Vendor pre-selection based on materials
- Automatic product line creation

## Security & Access Control

### Access Rights (ir.model.access.csv)
All core models grant full access (read/write/create/unlink) to `base.group_user`.

### Record Rules
- Work units: Draft records editable by creators
- BoQ Root: State-based access control
- Approval workflow: Role-based approval rights

## File Structure

```
hit_boq/
├── __init__.py
├── __manifest__.py
├── data/
│   ├── initial_boq_conf_data.xml    # Default configuration
│   └── product_tag_data.xml         # BoQ product tags
├── models/
│   ├── __init__.py
│   ├── boq_root.py                  # Main BoQ model
│   ├── boq_work_unit.py             # Work unit definition
│   ├── boq_work_unit_line.py        # BoQ work unit instance
│   ├── boq_material_line.py         # Material components
│   ├── boq_service_line.py          # Service components
│   ├── boq_others.py                # Other cost components
│   ├── boq_conf.py                  # Configuration model
│   ├── boq_work_unit_approval.py    # Approval workflow
│   ├── sale_order.py                # Sales integration
│   ├── purchase_order.py            # Purchase integration
│   └── product_product.py           # Product extensions
├── views/
│   ├── boq_root_views.xml           # Main BoQ interfaces
│   ├── work_unit_views.xml          # Work unit management
│   ├── work_unit_approval_views.xml # Approval interfaces
│   ├── boq_conf_views.xml           # Configuration interface
│   ├── sale_order_views.xml         # Sales integration UI
│   ├── product_views.xml            # Product extensions
│   ├── boq_report_preview_views.xml # Report preview
│   └── menu_boq_views.xml           # Menu structure
├── wizard/
│   ├── __init__.py
│   ├── boq_make_sale.py             # BoQ to sale conversion
│   ├── boq_make_sale_views.xml
│   ├── sale_order_create_rfq.py     # RFQ generation
│   └── sale_order_create_rfq_views.xml
├── report/
│   └── boq_root_report.xml          # QWeb report template
├── security/
│   └── ir.model.access.csv          # Access control
├── static/src/css/
│   └── boq_views.css                # Custom styling
└── tests/
    ├── __init__.py
    └── test_case2_refactor.py       # Unit tests
```

### Key Methods

#### BoQ Root Methods
```python
def action_create_sale_order(self):
    """Convert BoQ to sale order"""

def _compute_boq_price(self):
    """Calculate total BoQ costs with margins"""

def _calculate_material_prices(self, lines):
    """Calculate material cost totals"""

def _calculate_installation_prices(self, lines):
    """Calculate installation cost totals"""
```

#### Work Unit Methods
```python
def action_to_approve(self):
    """Submit work unit for approval"""

def action_approve(self):
    """Approve work unit"""

def action_reject(self):
    """Reject work unit"""

def _compute_component_prices(self):
    """Calculate component cost totals"""
```

## Configuration

### Initial Setup
1. Install module dependencies
2. Configure BoQ settings in BoQ Configuration menu
3. Set up product tags for BoQ items
4. Configure approval workflows

### Key Configuration Parameters
- Material margin percentage
- Installation margin percentage  
- Maintenance margin percentage
- Default profit percentage
- Currency settings (default: IDR)

## Customization Guidelines

### Adding New Cost Components
1. Create new model inheriting cost calculation patterns
2. Add One2many relation to work unit
3. Update cost computation methods
4. Add UI components in work unit form view

### Extending Approval Workflow
1. Modify state selections in work unit model
2. Add corresponding action methods
3. Update approval views and buttons
4. Configure approval rules in dependent modules

### Custom Reports
1. Inherit from existing QWeb report template
2. Extend report context with custom data
3. Modify report actions for new variants

## Performance Considerations

### Database Optimization
- Use computed fields with store=True for frequently accessed calculations
- Index commonly searched fields (codes, names, states)
- Optimize One2many field domains

### Calculation Efficiency
- Cache margin calculations at BoQ conf level
- Use batch operations for bulk updates
- Implement lazy loading for large work unit sets

## Migration Notes

### Version Compatibility
- Built for Odoo 17
- Uses modern ORM patterns and computed fields
- Leverages mail.thread for activity tracking

### Data Migration
When upgrading from previous versions:
1. Backup existing BoQ data
2. Run migration scripts for model changes
3. Verify cost calculation accuracy
4. Update custom views if modified

## Troubleshooting

### Common Issues

1. **Cost Calculation Errors**
   - Verify margin configuration
   - Check work unit component completeness
   - Validate currency settings

2. **Approval Workflow Problems**
   - Confirm user permissions
   - Check workflow state transitions
   - Verify approval module dependencies

3. **Integration Issues**
   - Validate sale order BoQ flags
   - Check purchase order linking
   - Verify project integration settings

### Existing problems/bugs:
    - SO button box ('POs' field, 'statinfo' widget) stays on 0

### Notes:
    - PO to SO relation. PO creation will automatically get the SO.id on creation.

---


