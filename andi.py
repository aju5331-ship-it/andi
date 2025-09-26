import streamlit as st
import hashlib
import json
import time
import uuid

# ---------------- Blockchain Classes ----------------
class TicketTransaction:
    def __init__(self, tx_type, ticket_id, owner, event=None, new_owner=None):
        self.tx_type = tx_type
        self.ticket_id = ticket_id
        self.owner = owner
        self.event = event
        self.new_owner = new_owner
        self.timestamp = time.time()
    def to_dict(self):
        return self.__dict__

class Block:
    def __init__(self, index, transactions, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = time.time()
        self.previous_hash = previous_hash
        self.nonce = nonce
    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class TicketBlockchain:
    difficulty = 2
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.tickets = {}
        self.create_genesis_block()
    def create_genesis_block(self):
        genesis_block = Block(0, [], "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)
    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)
    def mine(self):
        if not self.pending_transactions:
            return None
        new_block = Block(len(self.chain), self.pending_transactions, self.chain[-1].compute_hash())
        new_block.hash = self.proof_of_work(new_block)
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block
    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith("0" * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash
    def issue_ticket(self, owner, event):
        ticket_id = str(uuid.uuid4())
        tx = TicketTransaction("issue", ticket_id, owner, event)
        self.add_transaction(tx)
        self.tickets[ticket_id] = {"owner": owner, "status": "valid", "event": event}
        return ticket_id
    def transfer_ticket(self, ticket_id, new_owner):
        ticket = self.tickets.get(ticket_id)
        if not ticket or ticket["status"] != "valid":
            return False
        tx = TicketTransaction("transfer", ticket_id, ticket["owner"], new_owner=new_owner)
        self.add_transaction(tx)
        ticket["owner"] = new_owner
        return True
    def redeem_ticket(self, ticket_id):
        ticket = self.tickets.get(ticket_id)
        if not ticket or ticket["status"] != "valid":
            return False
        tx = TicketTransaction("redeem", ticket_id, ticket["owner"])
        self.add_transaction(tx)
        ticket["status"] = "redeemed"
        return True
    def verify_ticket(self, ticket_id):
        return self.tickets.get(ticket_id, None)

# ---------------- Streamlit App ----------------
st.set_page_config(page_title="Blockchain Ticketing System", layout="wide")
st.title("🎫 Blockchain Ticketing System")

# Persist blockchain in session_state
if "blockchain" not in st.session_state:
    st.session_state._
