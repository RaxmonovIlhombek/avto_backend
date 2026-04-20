import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Get all payments
cur.execute("SELECT payment.amount, payment.is_paid, booking.user_id FROM parking_payment payment JOIN parking_booking booking ON payment.booking_id = booking.id")
payments = cur.fetchall()

print("All payments in DB:")
for p in payments:
    print(f"Amount: {p[0]}, Is Paid: {p[1]}, User ID: {p[2]}")

conn.close()
