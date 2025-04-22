{
    "name": "BoQ",
    "summary": "Bill of Quantity ",
    "description": "Module for managing Bill of Quantity",
    "author": "Your Company",
    "website": "https://yourcompany.com",
    "version": "1.0.0",
    "category": "Customizations",
    "depends": [
        "base", 
        "product", 
        "mail", 
        "sale", 
        "project",
    ],
    "data": [

        "security/security.xml",
        "security/ir.model.access.csv",
        
        "data/product_tag_data.xml",
        "data/initial_boq_conf_data.xml",

        "wizard/boq_make_sale_views.xml",

        "views/sale_order_views.xml",
        "views/product_views.xml",

        "views/boq_report_preview_views.xml",
        "views/boq_conf_views.xml",
        "views/boq_root_views.xml",
        "views/work_unit_views.xml",
        "report/boq_root_report.xml",
        "views/menu_boq_views.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": True,
}