from flask import Flask, request, jsonify
import hashlib
import time
import json
from typing import List, Dict

# Blockchain Classes
class Stakeholder:
    def __init__(self, stakeholder_id, name, stakeholder_type, stake=0):
        self.stakeholder_id = stakeholder_id
        self.name = name
        self.stakeholder_type = stakeholder_type
        self.stake = stake

    def to_dict(self):
        return {
            "stakeholder_id": self.stakeholder_id,
            "name": self.name,
            "stakeholder_type": self.stakeholder_type,
            "stake": self.stake,
        }


class Transaction:
    def __init__(self, transaction_type, product_id, origin, destination, timestamp=None):
        self.transaction_type = transaction_type
        self.product_id = product_id
        self.origin = origin
        self.destination = destination
        self.timestamp = timestamp or time.time()

    def to_dict(self):
        return {
            "transaction_type": self.transaction_type,
            "product_id": self.product_id,
            "origin": self.origin,
            "destination": self.destination,
            "timestamp": self.timestamp,
        }


class Block:
    def __init__(self, index, transactions: List[Transaction], previous_hash, validator):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.validator = validator
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = (
            f"{self.index}{self.timestamp}{[tx.to_dict() for tx in self.transactions]}"
            f"{self.previous_hash}{self.validator}{self.nonce}"
        )
        return hashlib.sha256(block_data.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "validator": self.validator,
            "nonce": self.nonce,
            "hash": self.hash,
        }


class Blockchain:
    def __init__(self, filename="blockchain.json"):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.stakeholders: Dict[str, Stakeholder] = {}
        self.reward = 10
        self.filename = filename
        self.load_chain()

    def create_genesis_block(self):
        """Creates the initial block in the blockchain."""
        return Block(0, [], "0", "Genesis")

    def get_latest_block(self):
        return self.chain[-1]

    def register_stakeholder(self, stakeholder: Stakeholder):
        """Adds a stakeholder to the blockchain if they don't already exist."""
        if stakeholder.name in self.stakeholders:
            return "Stakeholder already exists."
        self.stakeholders[stakeholder.name] = stakeholder
        self.save_chain()
        return "Stakeholder registered successfully."

    def register_product(self, product_id, manufacturer, manufacture_date):
        """Registers a new product to the blockchain."""
        for block in self.chain:
            for txn in block.transactions:
                if txn.product_id == product_id:
                    return "Product already registered."

        if manufacturer not in self.stakeholders:
            return "Manufacturer not found in stakeholders."
        if self.stakeholders[manufacturer].stakeholder_type != "Certified Manufacturer":
            return "Manufacturer is not certified to register products."

        transaction = Transaction(
            transaction_type="register",
            product_id=product_id,
            origin=manufacturer,
            destination="Supply Chain",
            timestamp=manufacture_date
        )
        self.pending_transactions.append(transaction)
        self.save_chain()
        return "Product registration successful."

    def transfer_ownership(self, product_id, new_owner):
        """Transfers ownership of a product to a new stakeholder."""
        current_owner = None
        for block in self.chain:
            for txn in block.transactions:
                if txn.product_id == product_id:
                    current_owner = txn.destination

        if not current_owner:
            return "Product not found."
        if new_owner not in self.stakeholders:
            return "New owner not found in stakeholders."

        transaction = Transaction(
            transaction_type="transfer",
            product_id=product_id,
            origin=current_owner,
            destination=new_owner,
            timestamp=time.time()
        )
        self.pending_transactions.append(transaction)
        self.save_chain()
        return f"Ownership transferred to {new_owner}."

    def mine_pending_transactions(self):
        """Mines all pending transactions into a new block."""
        if not self.pending_transactions:
            return "No transactions to mine."

        validator = self.select_validator()
        if not validator:
            return "No valid validator selected."

        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.get_latest_block().hash,
            validator=validator,
        )
        self.chain.append(new_block)
        self.stakeholders[validator].stake += self.reward
        self.pending_transactions = []
        self.save_chain()
        return f"Block added by validator: {validator}"

    def verify_product(self, product_id):
        """Retrieves the transaction history for a given product."""
        product_history = []
        for block in self.chain:
            for txn in block.transactions:
                if txn.product_id == product_id:
                    product_history.append(txn.to_dict())

        if not product_history:
            return "Product not found."
        return product_history

    def save_chain(self):
        """Saves the blockchain to a file."""
        with open(self.filename, "w") as file:
            json.dump(self.to_dict(), file, indent=4)

    def load_chain(self):
        """Loads the blockchain from a file, if it exists."""
        try:
            with open(self.filename, "r") as file:
                data = json.load(file)
                self.chain = [
                    Block(
                        block["index"],
                        [Transaction(**tx) for tx in block["transactions"]],
                        block["previous_hash"],
                        block["validator"]
                    )
                    for block in data["chain"]
                ]
                self.pending_transactions = [Transaction(**tx) for tx in data["pending_transactions"]]
                self.stakeholders = {
                    name: Stakeholder(**stakeholder)
                    for name, stakeholder in data["stakeholders"].items()
                }
        except FileNotFoundError:
            pass

    def to_dict(self):
        """Converts the blockchain to a dictionary format."""
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "stakeholders": {name: stakeholder.to_dict() for name, stakeholder in self.stakeholders.items()},
        }

    def select_validator(self):
        """Selects a validator for mining based on stakes."""
        if not self.stakeholders:
            return None
        sorted_stakeholders = sorted(self.stakeholders.values(), key=lambda s: s.stake, reverse=True)
        return sorted_stakeholders[0].name

# Flask Application
app = Flask(__name__)
blockchain = Blockchain()

# Flask Routes
@app.route('/reset', methods=['POST'])
def reset_blockchain():
    blockchain.chain = [blockchain.create_genesis_block()]
    blockchain.pending_transactions = []
    blockchain.stakeholders = {}
    blockchain.save_chain()
    return jsonify({"message": "Blockchain reset successfully."}), 200

@app.route('/register_stakeholder', methods=['POST'])
def register_stakeholder():
    data = request.json
    stakeholder = Stakeholder(**data)
    result = blockchain.register_stakeholder(stakeholder)
    return jsonify({"message": result}), 200

@app.route('/register_product', methods=['POST'])
def register_product():
    data = request.json
    result = blockchain.register_product(**data)
    return jsonify({"message": result}), 200

@app.route('/mine', methods=['GET'])
def mine():
    result = blockchain.mine_pending_transactions()
    return jsonify({"message": result}), 200

@app.route('/verify_product/<product_id>', methods=['GET'])
def verify_product(product_id):
    result = blockchain.verify_product(product_id)
    return jsonify(result), 200

@app.route('/transfer_ownership', methods=['POST'])
def transfer_ownership():
    data = request.json
    required_fields = ["product_id", "new_owner"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields."}), 400

    result = blockchain.transfer_ownership(
        product_id=data["product_id"],
        new_owner=data["new_owner"]
    )
    status_code = 200 if result.startswith("Ownership transferred") else 400
    return jsonify({"message": result}), status_code


if __name__ == "__main__":
    app.run(debug=True)
