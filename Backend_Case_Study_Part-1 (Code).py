from flask import request, jsonify
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json

    try:
        # Validate request body
        if not data:
            return jsonify({"error": "Invalid request body"}), 400

        # Validate required fields
        if 'name' not in data or 'sku' not in data or 'price' not in data:
            return jsonify({"error": "name, sku and price are required"}), 400

        # Validate price
        try:
            price = Decimal(str(data['price']))
        except:
            return jsonify({"error": "Invalid price format"}), 400

        # Check SKU uniqueness
        existing = Product.query.filter_by(sku=data['sku']).first()
        if existing:
            return jsonify({"error": "SKU already exists"}), 409

        # Create product (not tied to warehouse)
        product = Product(
            name=data['name'],
            sku=data['sku'],
            price=price
        )

        db.session.add(product)
        db.session.flush()  # Get product.id before commit

        # Create inventory only if warehouse is provided
        if 'warehouse_id' in data:
            quantity = data.get('initial_quantity', 0)

            inventory = Inventory(
                product_id=product.id,
                warehouse_id=data['warehouse_id'],
                quantity=quantity
            )
            db.session.add(inventory)

        # Single transaction commit
        db.session.commit()

        return jsonify({
            "message": "Product created",
            "product_id": product.id
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database constraint error"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
