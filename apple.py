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
st.set_page_config(page_title="🎵 Concert Ticketing System", layout="wide", page_icon="🎫")

# --------- Initialize blockchain safely ----------
if "blockchain" not in st.session_state:
    st.session_state.blockchain = TicketBlockchain()
blockchain = st.session_state.blockchain

if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "redeem_select" not in st.session_state:
    st.session_state.redeem_select = None
if "verify_select" not in st.session_state:
    st.session_state.verify_select = None

# --------- Predefined Events (India concerts) ----------
events = [
    {"name": "Imagine Dragons Live", "city": "Mumbai", "venue": "NSCI Dome", "time": "2025-11-10 19:00", "price": 5999},
    {"name": "Coldplay Concert", "city": "Bengaluru", "venue": "Kanteerava Stadium", "time": "2025-11-15 20:00", "price": 5999},
    {"name": "Adele Live", "city": "Delhi", "venue": "Jawaharlal Nehru Stadium", "time": "2025-12-01 19:30", "price": 5999},
    {"name": "Ed Sheeran Tour", "city": "Kolkata", "venue": "Salt Lake Stadium", "time": "2025-12-10 20:00", "price": 5999},
    {"name": "Arijit Singh Concert", "city": "Pune", "venue": "Shiv Chhatrapati Sports Complex", "time": "2025-12-20 19:00", "price": 5999},
]

# --------- Aesthetic Landing Page ----------
st.markdown("""
    <style>
    .main {background-color: #f5f5f7; color: #111;}
    h1 {color: #000; font-weight: 600;}
    .stButton>button {background-color:#0071e3;color:white;border-radius:8px;padding:8px 16px;}
    .event-box {border:1px solid #e1e1e1;border-radius:12px;padding:16px;margin-bottom:12px;background-color:white;}
    </style>
""", unsafe_allow_html=True)

st.title("🎵 Select Your Concert Event")
st.write("Book tickets for the hottest concerts happening across India!")

# --------- Event Selection ----------
for idx, e in enumerate(events):
    st.markdown(f"""
    <div class="event-box">
    <h3>{e['name']}</h3>
    <p><b>City:</b> {e['city']} &nbsp;&nbsp; <b>Venue:</b> {e['venue']}</p>
    <p><b>Time:</b> {e['time']} &nbsp;&nbsp; <b>Price:</b> INR {e['price']}</p>
    </div>
    """, unsafe_allow_html=True)

event_names = [e["name"] for e in events]
st.subheader("Step 1: Enter Your Name")
user_name = st.text_input("Your Name", key="user_name")

st.subheader("Step 2: Select Event")
selected_event_name = st.selectbox("Choose Event", event_names, key="selected_event")
selected_event = next((ev for ev in events if ev["name"] == selected_event_name), None)

# --------- Issue Ticket ----------
if st.button("Book Ticket"):
    if user_name and selected_event:
        ticket_id = blockchain.issue_ticket(user_name, selected_event)
        blockchain.mine()
        st.success(f"Ticket booked successfully! 🎫\nTicket ID: {ticket_id}")
        st.text_input("Ticket ID (copy this)", ticket_id, key=f"ticket_{ticket_id}")
    else:
        st.warning("Please enter your name and select an event.")

# --------- Dropdown lists for tickets ----------
valid_tickets = [tid for tid, t in blockchain.tickets.items() if t["status"] == "valid"]
all_tickets = list(blockchain.tickets.keys())

# --------- Redeem Ticket ----------
st.subheader("Redeem Your Ticket")
if valid_tickets:
    redeem_ticket_id = st.selectbox("Select Ticket to Redeem", valid_tickets, key="redeem_select")
    if st.button("Redeem Ticket"):
        blockchain.redeem_ticket(redeem_ticket_id)
        blockchain.mine()
        st.success(f"Ticket {redeem_ticket_id} redeemed successfully.")
else:
    st.info("No valid tickets available to redeem.")

# --------- Verify Ticket ----------
st.subheader("Verify Ticket")
if all_tickets:
    verify_ticket_id = st.selectbox("Select Ticket to Verify", all_tickets, key="verify_select")
    if st.button("Verify Ticket"):
        ticket = blockchain.verify_ticket(verify_ticket_id)
        if ticket:
            st.json(ticket)
            st.text_input("Ticket ID", verify_ticket_id, key=f"verify_{verify_ticket_id}")
        else:
            st.error("Ticket not found.")
else:
    st.info("No tickets available to verify.")

# --------- Blockchain Ledger ----------
st.subheader("Blockchain Ledger")
for block in blockchain.chain:
    st.write(f"Block Index: {block.index}, Previous Hash: {block.previous_hash}")
    st.json([tx.to_dict() for tx in block.transactions])
