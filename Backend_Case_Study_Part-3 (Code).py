from flask import jsonify
from datetime import datetime, timedelta

@app.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def get_low_stock_alerts(company_id):

    alerts = []
    recent_days = 30
    cutoff_date = datetime.utcnow() - timedelta(days=recent_days)

    # Step 1: Get all warehouses of the company
    warehouses = Warehouse.query.filter_by(company_id=company_id).all()

    for warehouse in warehouses:

        # Step 2: Get inventory for each warehouse
        inventory_items = Inventory.query.filter_by(warehouse_id=warehouse.id).all()

        for item in inventory_items:
            product = Product.query.get(item.product_id)

            # Step 3: Check if product has threshold
            if not hasattr(product, 'threshold'):
                continue

            threshold = product.threshold
            current_stock = item.quantity

            # Step 4: Get recent sales data
            sales = Sale.query.filter(
                Sale.product_id == product.id,
                Sale.warehouse_id == warehouse.id,
                Sale.created_at >= cutoff_date
            ).all()

            # Skip if no recent sales
            if not sales:
                continue

            total_sold = sum(s.quantity for s in sales)

            # Avoid division by zero
            if total_sold == 0:
                continue

            avg_daily_sales = total_sold / recent_days

            # Step 5: Check low stock condition
            if current_stock < threshold:

                days_until_stockout = int(current_stock / avg_daily_sales)

                # Step 6: Get supplier info
                supplier = db.session.query(Supplier).join(ProductSupplier)\
                    .filter(ProductSupplier.product_id == product.id).first()

                alerts.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "sku": product.sku,
                    "warehouse_id": warehouse.id,
                    "warehouse_name": warehouse.name,
                    "current_stock": current_stock,
                    "threshold": threshold,
                    "days_until_stockout": days_until_stockout,
                    "supplier": {
                        "id": supplier.id if supplier else None,
                        "name": supplier.name if supplier else None,
                        "contact_email": supplier.contact_email if supplier else None
                    }
                })

    return jsonify({
        "alerts": alerts,
        "total_alerts": len(alerts)
    })