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

# ---------------- Initialize session_state safely ----------------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = TicketBlockchain()
    # ---------- Preload demo tickets ----------
    demo_tickets = [
        ("Alice", "Concert A"),
        ("Bob", "Concert B"),
        ("Charlie", "Sports Event C")
    ]
    for owner, event in demo_tickets:
        ticket_id = st.session_state.blockchain.issue_ticket(owner, event)
    st.session_state.blockchain.mine()

if "issue_owner" not in st.session_state:
    st.session_state.issue_owner = ""
if "issue_event" not in st.session_state:
    st.session_state.issue_event = ""
if "transfer_owner" not in st.session_state:
    st.session_state.transfer_owner = ""
if "transfer_select" not in st.session_state:
    st.session_state.transfer_select = None
if "redeem_select" not in st.session_state:
    st.session_state.redeem_select = None
if "verify_select" not in st.session_state:
    st.session_state.verify_select = None

blockchain = st.session_state.blockchain

# ---------------- Issue Ticket ----------------
st.subheader("Issue Ticket")
owner = st.text_input("Owner Name", key="issue_owner")
event_name = st.text_input("Event Name", key="issue_event")
if st.button("Issue Ticket"):
    if owner and event_name:
        ticket_id = blockchain.issue_ticket(owner, event_name)
        blockchain.mine()
        st.success(f"Ticket issued! Ticket ID: {ticket_id}")
        st.button("Copy Ticket ID", on_click=lambda tid=ticket_id: st.experimental_set_clipboard(tid))
    else:
        st.warning("Please enter Owner and Event Name.")

# ---------------- Dropdown lists ----------------
valid_tickets = [tid for tid, t in blockchain.tickets.items() if t["status"] == "valid"]
all_tickets = list(blockchain.tickets.keys())

# ---------------- Transfer Ticket ----------------
st.subheader("Transfer Ticket")
if valid_tickets:
    transfer_ticket_id = st.selectbox("Select Ticket to Transfer", valid_tickets, key="transfer_select")
    new_owner = st.text_input("New Owner", key="transfer_owner")
    if st.button("Transfer Ticket"):
        if new_owner:
            blockchain.transfer_ticket(transfer_ticket_id, new_owner)
            blockchain.mine()
            st.success(f"Ticket {transfer_ticket_id} transferred to {new_owner}.")
        else:
            st.warning("Enter a new owner name.")
else:
    st.info("No valid tickets available to transfer.")

# ---------------- Redeem Ticket ----------------
st.subheader("Redeem Ticket")
if valid_tickets:
    redeem_ticket_id = st.selectbox("Select Ticket to Redeem", valid_tickets, key="redeem_select")
    if st.button("Redeem Ticket"):
        blockchain.redeem_ticket(redeem_ticket_id)
        blockchain.mine()
        st.success(f"Ticket {redeem_ticket_id} redeemed successfully.")
else:
    st.info("No valid tickets available to redeem.")

# ---------------- Verify Ticket ----------------
st.subheader("Verify Ticket")
if all_tickets:
    verify_ticket_id = st.selectbox("Select Ticket to Verify", all_tickets, key="verify_select")
    if st.button("Verify Ticket"):
        ticket = blockchain.verify_ticket(verify_ticket_id)
        if ticket:
            st.json(ticket)
            st.info(f"Ticket status: {ticket['status']}, Owner: {ticket['owner']}, Event: {ticket['event']}")
            st.button("Copy Ticket ID", on_click=lambda tid=verify_ticket_id: st.experimental_set_clipboard(tid))
        else:
            st.error("Ticket not found.")
else:
    st.info("No tickets available to verify.")

# ---------------- View Blockchain ----------------
st.subheader("Blockchain Ledger")
for block in blockchain.chain:
    st.write(f"Block Index: {block.index}, Previous Hash: {block.previous_hash}")
    st.json([tx.to_dict() for tx in block.transactions])
