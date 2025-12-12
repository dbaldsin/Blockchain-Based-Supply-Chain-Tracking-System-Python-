# Blockchain-Based Supply Chain Tracking System (Python)

## Project Overview

This project is a **custom blockchain-based supply chain tracking system** implemented in **Python**. It simulates how products (e.g. pharmaceuticals) can be securely registered, transferred, and tracked across stakeholders using an immutable blockchain ledger.

The system models real-world blockchain concepts such as **blocks, transactions, hashing, validators, delegated authority, and pending transactions**, with all blockchain state persisted in a structured JSON file.

---

## Key Objectives

- Demonstrate core **blockchain principles** without external frameworks
- Track product movement across a **multi-party supply chain**
- Ensure **data integrity and traceability** using cryptographic hashes
- Model a simplified **delegated authority / stake-based validation** mechanism

---

## Core Features

### Blockchain Ledger
- Genesis block initialization
- Sequential block creation with:
  - Index
  - Timestamp
  - Transactions
  - Previous hash
  - Validator
  - Nonce
  - Current block hash
- Immutable chain structure stored in JSON

---

### Transactions
Supported transaction types include:
- **Product registration**
- **Product transfer between stakeholders**

Each transaction records:
- Product ID
- Origin
- Destination
- Timestamp

Pending transactions are queued and later committed to the blockchain when a block is validated.

---

### Stakeholders
The system models real supply-chain entities such as:
- Manufacturers
- Distributors
- Logistics providers

Each stakeholder includes:
- Unique ID
- Stakeholder type
- Stake value (used in governance/validation logic)

---

### Delegates & Validation
- Delegates represent trusted validators
- Each delegate has:
  - Vote weight
  - Stake
- Delegates are responsible for validating blocks
- Validation logic ensures chain consistency and integrity

---

## Data Persistence

Blockchain state is stored in a structured JSON file containing:
- Full blockchain ledger
- Pending transactions
- Stakeholders
- Delegates

This allows:
- Persistent state across program runs
- Easy inspection and debugging
- Reproducible blockchain history

---

## Technical Stack

- **Language:** Python  
- **Data Storage:** JSON  
- **Core Concepts Implemented:**
  - Cryptographic hashing (SHA-256)
  - Blockchain immutability
  - Transaction queues
  - Delegated validation
  - Supply chain provenance

---

## Engineering Focus

- Built blockchain logic **from first principles**
- Clean separation of concerns:
  - Block creation
  - Transaction handling
  - Validation
  - Persistence
- Emphasis on readability and extensibility
- Designed for easy addition of:
  - New transaction types
  - More validators
  - Enhanced consensus logic

---

## How to Run

1. Ensure Python 3 is installed.
2. Place the Python source file(s) and `blockchain.json` in the same directory.
3. Run the main script:
```bash
python main_rev_2.py
