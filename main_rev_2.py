from flask import Flask, request, jsonify
import hashlib
import time
import json
from typing import List, Dict
import argparse
import logging

# Setup Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# -----------------------------
# Blockchain Classes
# -----------------------------

class Authority:
    def __init__(self, authority_id, name, votes=0, stake=0):
        self.authority_id = authority_id
        self.name = name
        self.votes = votes
        self.stake = stake

    def to_dict(self):
        return {
            "authority_id": self.authority_id,
            "name": self.name,
            "votes": self.votes,
            "stake": self.stake,
        }

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
            "stake": self.stake
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
        self.delegates: Dict[str, Authority] = {}

    def create_genesis_block(self):
        return Block(0, [], "0", "Genesis")

    def get_latest_block(self):
        return self.chain[-1]

    def is_chain_valid(self):
        """
        Validates the integrity of the blockchain by ensuring that:
        1. Each block's hash matches its calculated hash.
        2. Each block's previous hash matches the hash of the previous block.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check if the current block's hash is correct
            if current_block.hash != current_block.calculate_hash():
                logger.error(f"Invalid hash at block {i}.")
                return False

            # Check if the current block points to the correct previous hash
            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Invalid previous hash at block {i}.")
                return False

        logger.info("Blockchain is valid.")
        return True


    def register_stakeholder(self, stakeholder: Stakeholder):
        if stakeholder.name in self.stakeholders:
            return "Stakeholder already exists."
        self.stakeholders[stakeholder.name] = stakeholder
        self.save_chain()
        return "Stakeholder registered successfully."

    def register_product(self, product_id, manufacturer, manufacture_date):
        for block in self.chain:
            for txn in block.transactions:
                if txn.product_id == product_id:
                    return "Product already registered."

        if manufacturer not in self.stakeholders:
            return "Manufacturer not found in stakeholders."

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

    def register_delegate(self, authority: Authority):
        if authority.name in self.delegates:
            return "Delegate already exists."
        self.delegates[authority.name] = authority
        self.save_chain()
        return "Delegate registered successfully."

    def vote_delegate(self, stakeholder_name, delegate_name):
        if stakeholder_name not in self.stakeholders:
            return "Stakeholder not found."
        if delegate_name not in self.delegates:
            return "Delegate not found."

        stakeholder = self.stakeholders[stakeholder_name]
        delegate = self.delegates[delegate_name]
        delegate.votes += stakeholder.stake
        self.save_chain()
        return f"{stakeholder_name} voted for {delegate_name}."

    def mine_pending_transactions(self):
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
        if validator in self.delegates:
            self.delegates[validator].stake += self.reward
        self.pending_transactions = []
        self.save_chain()
        return f"Block added by validator: {validator}"

    def select_validator(self):
        if not self.delegates:
            return None
        sorted_delegates = sorted(self.delegates.values(), key=lambda d: d.votes, reverse=True)
        return sorted_delegates[0].name

    def save_chain(self):
        with open(self.filename, "w") as file:
            json.dump(self.to_dict(), file, indent=4)

    def load_chain(self):
        try:
            with open(self.filename, "r") as file:
                data = json.load(file)

                # Load chain
                self.chain = [
                    Block(
                        block["index"],
                        [Transaction(**tx) for tx in block["transactions"]],
                        block["previous_hash"],
                        block["validator"]
                    )
                    for block in data["chain"]
                ]

                # Load pending transactions
                self.pending_transactions = [Transaction(**tx) for tx in data["pending_transactions"]]

                # Load stakeholders
                self.stakeholders = {
                    name: Stakeholder(**stakeholder)
                    for name, stakeholder in data["stakeholders"].items()
                }

                # Load delegates (initialize as empty if not present)
                self.delegates = {
                    name: Authority(**delegate)
                    for name, delegate in data.get("delegates", {}).items()
                }

                logger.debug(f"Blockchain loaded from '{self.filename}'.")

        except FileNotFoundError:
            logger.debug(f"'{self.filename}' not found. Initializing new blockchain.")
            self.chain = [self.create_genesis_block()]
            self.pending_transactions = []
            self.stakeholders = {}
            self.delegates = {}  # Initialize delegates
            self.save_chain()
        except Exception as e:
            logger.error(f"Error loading blockchain: {e}")


    def to_dict(self):
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "stakeholders": {name: stakeholder.to_dict() for name, stakeholder in self.stakeholders.items()},
            "delegates": {name: delegate.to_dict() for name, delegate in self.delegates.items()},
        }


# -----------------------------
# Flask App
# -----------------------------

app = Flask(__name__)
blockchain = Blockchain()

# ---- ROUTES ----

@app.route('/reset', methods=['POST'])
def reset_blockchain():
    """Resets the blockchain."""
    blockchain.chain = [blockchain.create_genesis_block()]
    blockchain.pending_transactions = []
    blockchain.stakeholders = {}
    blockchain.delegates = {}
    blockchain.save_chain()
    return jsonify({"message": "Blockchain has been reset successfully."}), 200

@app.route('/register_stakeholder', methods=['POST'])
def register_stakeholder():
    data = request.json
    stakeholder = Stakeholder(data["stakeholder_id"], data["name"], data["stakeholder_type"], data.get("stake", 0))
    result = blockchain.register_stakeholder(stakeholder)
    return jsonify({"message": result}), 200

@app.route('/register_product', methods=['POST'])
def register_product():
    data = request.json
    result = blockchain.register_product(data["product_id"], data["manufacturer"], data["manufacture_date"])
    return jsonify({"message": result}), 200

@app.route('/transfer_ownership', methods=['POST'])
def transfer_ownership():
    data = request.json
    result = blockchain.transfer_ownership(data["product_id"], data["new_owner"])
    return jsonify({"message": result}), 200

@app.route('/register_delegate', methods=['POST'])
def register_delegate():
    data = request.json
    delegate = Authority(data["authority_id"], data["name"])
    result = blockchain.register_delegate(delegate)
    return jsonify({"message": result}), 200

@app.route('/vote_delegate', methods=['POST'])
def vote_delegate():
    data = request.json
    result = blockchain.vote_delegate(data["stakeholder_name"], data["delegate_name"])
    return jsonify({"message": result}), 200

@app.route('/mine', methods=['GET'])
def mine():
    result = blockchain.mine_pending_transactions()
    return jsonify({"message": result}), 200

@app.route('/validate', methods=['GET'])
def validate():
    """
    Validates the blockchain and returns the status.
    """
    is_valid = blockchain.is_chain_valid()
    message = "Blockchain is valid." if is_valid else "Blockchain is invalid."
    return jsonify({"message": message}), 200 if is_valid else 400


@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify(blockchain.to_dict()), 200

@app.route('/delegates', methods=['GET'])
def get_delegates():
    delegates = [delegate.to_dict() for delegate in blockchain.delegates.values()]
    return jsonify(delegates), 200


if __name__ == "__main__":
    app.run(debug=True)
