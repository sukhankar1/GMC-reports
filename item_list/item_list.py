# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, cstr, strip_html

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": "Item Code",
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"label": "Item Name",
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": "VED",
			"fieldname": "ved",
			"fieldtype": "Link",
			"options": "VED",
			"width": 100
		},
		{
			"label": "Strength",
			"fieldname": "strength",
			"fieldtype": "Data",
			"width": 110
		},
		{
			"label": "Classification",
			"fieldname": "classification",
			"fieldtype": "Link",
			"options": "Classification",
			"width": 120
		},
		{
			"label": "Classification Type",
			"fieldname": "classification_type",
			"fieldtype": "Link",
			"options": "Classification Type",
			"width": 130
		},
		{
			"label": "Material Category",
			"fieldname": "material_category",
			"fieldtype": "Link",
			"options": "Material Category",
			"width": 130
		},
		{
			"label": "Category",
			"fieldname": "category",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 130
		},
		{
			"label": "Sub Category",
			"fieldname": "sub_category",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 130
		},
		{
			"label": "Sub Category 2",
			"fieldname": "sub_category_2",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Schedule Type",
			"fieldname": "schedule_type",
			"fieldtype": "Link",
			"options": "Schedule Type",
			"width": 110
		},
		{
			"label": "Generic Name",
			"fieldname": "generic_name",
			"fieldtype": "Link",
			"options": "Generic Name",
			"width": 150
		},
		{
			"label": "Marketed By",
			"fieldname": "marketed_by",
			"fieldtype": "Link",
			"options": "Marketed By",
			"width": 140
		},
		{
			"label": "Manufactured By",
			"fieldname": "manufactured_by",
			"fieldtype": "Link",
			"options": "Manufacturer",
			"width": 140
		},
		{
			"label": "Substitute Group",
			"fieldname": "substitute_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 130
		},
		{
			"label": "Critical Category",
			"fieldname": "critical_category",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Description",
			"fieldname": "description",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": "Manufacturer",
			"fieldname": "manufacturer",
			"fieldtype": "Link",
			"options": "Brand",
			"width": 130
		},
		{
			"label": "Bin Location",
			"fieldname": "bin_location",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Quoted Price",
			"fieldname": "quoted_price",
			"fieldtype": "Float",
			"width": 110
		},
		{
			"label": "Quoted MRP",
			"fieldname": "quoted_mrp",
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"label": "Expiry",
			"fieldname": "expiry",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": "Purchase UOM",
			"fieldname": "purchase_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 110
		},
		{
			"label": "Consumption UOM",
			"fieldname": "consumption_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 120
		},
		{
			"label": "Conversion Factor",
			"fieldname": "conversion_factor",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": "Purchase Rate",
			"fieldname": "purchase_rate",
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"label": "MRP",
			"fieldname": "mrp",
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"label": "GP Value",
			"fieldname": "gp_value",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": "GP %",
			"fieldname": "gp_percent",
			"fieldtype": "Percent",
			"width": 90
		},
		{
			"label": "HSN/SAC Code",
			"fieldname": "hsn_sac_code",
			"fieldtype": "Data",
			"width": 110
		},
		{
			"label": "Status",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 90
		},
		{
			"label": "Created By",
			"fieldname": "created_by",
			"fieldtype": "Data",
			"width": 140
		},
		{
			"label": "Created Date & Time",
			"fieldname": "created_date_time",
			"fieldtype": "Datetime",
			"width": 140
		},
		{
			"label": "Modified By",
			"fieldname": "modified_by",
			"fieldtype": "Data",
			"width": 140
		},
		{
			"label": "Modified Date & Time",
			"fieldname": "modified_date_time",
			"fieldtype": "Datetime",
			"width": 140
		}
	]

def get_data(filters):
	if not filters:
		filters = {}

	conditions = []
	values = {}

	if filters.get("classification"):
		conditions.append("i.custom_classification = %(classification)s")
		values["classification"] = filters.get("classification")

	if filters.get("status"):
		if filters.get("status") == "Active":
			conditions.append("(i.disabled = 0 OR i.disabled IS NULL)")
		elif filters.get("status") == "Disabled":
			conditions.append("i.disabled = 1")

	if filters.get("therapeutic_group"):
		conditions.append("""(
			i.custom_generic_name IN (
				SELECT gn.name FROM `tabGeneric Name` gn WHERE gn.generic_group = %(therapeutic_group)s
			)
			OR i.item_group = %(therapeutic_group)s
			OR i.custom_category = %(therapeutic_group)s
		)""")
		values["therapeutic_group"] = filters.get("therapeutic_group")

	if filters.get("therapeutic_sub_group"):
		conditions.append("""(
			i.custom_generic_name IN (
				SELECT gn.name FROM `tabGeneric Name` gn WHERE gn.generic_group = %(therapeutic_sub_group)s
			)
			OR i.item_group = %(therapeutic_sub_group)s
		)""")
		values["therapeutic_sub_group"] = filters.get("therapeutic_sub_group")

	where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

	query = f"""
		SELECT
			i.name,
			i.item_code,
			i.item_name,
			i.custom_ved AS ved,
			i.custom_strength,
			i.custom_strength_unit,
			i.custom_classification AS classification,
			i.custom_classification_type AS classification_type,
			i.custom_material_category AS material_category,
			i.custom_category AS category,
			i.item_group AS sub_category,
			i.custom_schedule_type AS schedule_type,
			i.custom_generic_name AS generic_name,
			i.custom_marketed_by AS marketed_by,
			i.default_item_manufacturer AS manufactured_by,
			i.custom_subtitute_group AS substitute_group,
			i.custom_reserved_antibiotic,
			i.custom_high_risk_drug,
			i.custom_emergency_drug,
			i.custom_narcotic_drug,
			i.description,
			i.brand AS manufacturer,
			i.custom_quoted_price AS quoted_price,
			i.custom_mrp AS quoted_mrp,
			i.shelf_life_in_days,
			i.has_expiry_date,
			i.purchase_uom,
			i.stock_uom AS consumption_uom,
			i.last_purchase_rate AS purchase_rate,
			i.standard_rate,
			i.custom_gp_value AS gp_value,
			i.custom_gp AS gp_percent,
			i.gst_hsn_code AS hsn_sac_code,
			i.disabled,
			i.owner AS created_by,
			i.creation AS created_date_time,
			i.modified_by,
			i.modified AS modified_date_time
		FROM
			`tabItem` i
		{where_clause}
		ORDER BY
			i.creation DESC
	"""

	items = frappe.db.sql(query, values, as_dict=True)

	if not items:
		return []

	item_names = [it.name for it in items]

	# Fetch UOM conversion factors
	uom_conv_map = {}
	if item_names:
		uom_records = frappe.db.sql("""
			SELECT parent, uom, conversion_factor
			FROM `tabUOM Conversion Detail`
			WHERE parent IN %(item_names)s
		""", {"item_names": item_names}, as_dict=True)
		for u in uom_records:
			uom_conv_map[(u.parent, u.uom)] = flt(u.conversion_factor)

	# Fetch Bin Locations from Item Consumption Details
	bin_map = {}
	if item_names:
		bin_records = frappe.db.sql("""
			SELECT parent, bin_location
			FROM `tabItem Consumption Details`
			WHERE parent IN %(item_names)s AND bin_location IS NOT NULL AND bin_location != ''
		""", {"item_names": item_names}, as_dict=True)
		for b in bin_records:
			if b.parent not in bin_map:
				bin_map[b.parent] = b.bin_location

	data = []
	for it in items:
		# Strength
		strength_parts = []
		if it.custom_strength:
			strength_parts.append(cstr(it.custom_strength).strip())
		if it.custom_strength_unit and cstr(it.custom_strength_unit).strip() not in [".", ""]:
			strength_parts.append(cstr(it.custom_strength_unit).strip())
		strength_val = " ".join(strength_parts) if strength_parts else ""

		# Critical Category
		critical_cat = ""
		if it.custom_reserved_antibiotic:
			critical_cat = "Reserved Antibiotic"
		elif it.custom_high_risk_drug:
			critical_cat = "High Risk Drug"
		elif it.custom_emergency_drug:
			critical_cat = "Emergency Drug"
		elif it.custom_narcotic_drug:
			critical_cat = "Narcotic Drug"

		# Expiry
		if it.shelf_life_in_days and it.shelf_life_in_days > 0:
			expiry_val = f"{it.shelf_life_in_days} Days"
		elif it.has_expiry_date:
			expiry_val = "Yes"
		else:
			expiry_val = "No"

		# Conversion factor
		cf = uom_conv_map.get((it.name, it.purchase_uom), 1.0)
		if not cf:
			cf = 1.0

		# Description clean
		desc = strip_html(it.description or "")
		if desc:
			desc = desc.replace("\n", " ").strip()

		# MRP
		mrp_val = flt(it.quoted_mrp) or flt(it.standard_rate)

		row = {
			"item_code": it.item_code,
			"item_name": it.item_name,
			"ved": it.ved or "",
			"strength": strength_val,
			"classification": it.classification or "",
			"classification_type": it.classification_type or "",
			"material_category": it.material_category or "",
			"category": it.category or "",
			"sub_category": it.sub_category or "",
			"sub_category_2": "",
			"schedule_type": it.schedule_type or "",
			"generic_name": it.generic_name or "",
			"marketed_by": it.marketed_by or "",
			"manufactured_by": it.manufactured_by or "",
			"substitute_group": it.substitute_group or "",
			"critical_category": critical_cat,
			"description": desc,
			"manufacturer": it.manufacturer or "",
			"bin_location": bin_map.get(it.name, ""),
			"quoted_price": flt(it.quoted_price),
			"quoted_mrp": flt(it.quoted_mrp),
			"expiry": expiry_val,
			"purchase_uom": it.purchase_uom or "",
			"consumption_uom": it.consumption_uom or "",
			"conversion_factor": flt(cf),
			"purchase_rate": flt(it.purchase_rate),
			"mrp": mrp_val,
			"gp_value": flt(it.gp_value),
			"gp_percent": flt(it.gp_percent),
			"hsn_sac_code": it.hsn_sac_code or "",
			"status": "Disabled" if it.disabled else "Active",
			"created_by": it.created_by or "",
			"created_date_time": it.created_date_time,
			"modified_by": it.modified_by or "",
			"modified_date_time": it.modified_date_time
		}
		data.append(row)

	return data
