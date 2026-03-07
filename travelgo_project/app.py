import os
import uuid
import datetime
import boto3
from flask import Flask, render_template, request, redirect, session
import dynamodb_config as db
import sns_service

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "travelgo-secret")

REGION = "ap-south-1"

# AWS SNS Client
sns = boto3.client('sns', region_name=REGION)

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "your-sns-topic-arn")

# ---------------- INITIALIZE DATABASE ----------------

def init_dynamodb():
    try:
        db.create_tables()
        db.seed_initial_data()
    except Exception as e:
        print("DynamoDB init:", e)

init_dynamodb()

# ---------------- HELPER FUNCTIONS ----------------

def send_notification(message, subject="TravelGo Notification"):
    """Send notification via AWS SNS with error handling"""
    try:
        if SNS_TOPIC_ARN and SNS_TOPIC_ARN != "your-sns-topic-arn":
            response = sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=message,
                Subject=subject
            )
            print(f"SNS Notification sent! Message ID: {response.get('MessageId')}")
            return True
        else:
            print("SNS Topic ARN not configured. Skipping notification.")
            return False
    except Exception as e:
        print(f"SNS Error: {e}")
        return False


def send_booking_confirmation(booking):
    """Send booking confirmation notification"""
    message = f"""
╔══════════════════════════════════════════════════════════╗
║           ✈️  TRAVELGO BOOKING CONFIRMATION  ✈️          ║
╚══════════════════════════════════════════════════════════╝

🎫 Booking ID: {booking.get('booking_id')}

📋 Booking Details:
   • Type: {booking.get('type')}
   • Details: {booking.get('details')}
   • Route: {booking.get('source')} ➝ {booking.get('destination')}
   • Seat: {booking.get('seat') or 'N/A'}
   • Date: {booking.get('date')}
   • Price: ₹{booking.get('price')}

💳 Payment Information:
   • Method: {booking.get('payment_method')}
   • Reference: {booking.get('payment_reference')}

👤 Customer Email: {booking.get('email')}

✅ Your booking has been confirmed successfully!

═══════════════════════════════════════════════════════════
Thank you for choosing TravelGo! Have a safe journey! 🚄
"""

    send_notification(message, "TravelGo - Booking Confirmed ✅")


def send_cancellation_alert(booking_id, email):
    """Send booking cancellation alert"""
    message = f"""
╔══════════════════════════════════════════════════════════╗
║        🚫  TRAVELGO BOOKING CANCELLATION ALERT  🚫        ║
╚══════════════════════════════════════════════════════════╝

🎫 Booking ID: {booking_id}

⚠️  Your booking has been CANCELLED successfully.

👤 Customer Email: {email}

💰 Note: Refund will be processed according to the cancellation policy.

═══════════════════════════════════════════════════════════
We hope to serve you again soon! 🙏
"""

    send_notification(message, f"TravelGo - Booking {booking_id} Cancelled ❌")


def get_transport_info(t_id):

    listing = db.get_listing(t_id)

    if listing:
        return {
            "type": listing.get("TransportType"),
            "source": listing.get("Source"),
            "destination": listing.get("Destination"),
            "details": listing.get("Name"),
            "price": listing.get("Price")
        }

    hotel = db.get_hotel(t_id)

    if hotel:
        return {
            "type": "Hotel",
            "source": hotel.get("City"),
            "destination": hotel.get("City"),
            "details": hotel.get("Name"),
            "price": hotel.get("Price")
        }

    return None


# ---------------- HOME ----------------

@app.route('/')
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        email = request.form['email']
        name = request.form['name']
        password = request.form['password']

        existing_user = db.get_user(email)

        if existing_user:
            return render_template("register.html", error="Email already exists")

        db.create_user(email, name, password)

        return redirect('/login')

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = db.get_user(email)

        if user and user.get("Password") == password:

            session['user'] = email
            session['name'] = user.get("Name")

            db.update_user_login(email)

            return redirect('/dashboard')

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login')

    bookings = db.get_user_bookings(session['user'])
    bookings = db.convert_decimal_to_float(bookings)

    return render_template(
        "dashboard.html",
        name=session['name'],
        bookings=bookings
    )


# ---------------- BUS SEARCH ----------------

@app.route('/bus')
def bus():

    source = request.args.get("source")
    destination = request.args.get("destination")

    buses = db.get_listings_by_type("Bus")

    if source:
        buses = [b for b in buses if b.get("Source") == source]

    if destination:
        buses = [b for b in buses if b.get("Destination") == destination]

    buses = db.convert_decimal_to_float(buses)

    return render_template("bus.html", buses=buses)


# ---------------- TRAIN ----------------

@app.route('/train')
def train():

    trains = db.get_listings_by_type("Train")
    trains = db.convert_decimal_to_float(trains)

    return render_template("train.html", trains=trains)


# ---------------- FLIGHT ----------------

@app.route('/flight')
def flight():

    flights = db.get_listings_by_type("Flight")
    flights = db.convert_decimal_to_float(flights)

    return render_template("flight.html", flights=flights)


# ---------------- HOTELS ----------------

@app.route('/hotels')
def hotels():

    category = request.args.get("type")

    hotels = db.get_all_hotels()

    if category:
        hotels = [h for h in hotels if h.get("Type") == category]

    hotels = db.convert_decimal_to_float(hotels)

    return render_template("hotels.html", hotels=hotels)


# ---------------- SEAT SELECTION ----------------

@app.route('/seat/<transport_id>/<price>')
def seat(transport_id, price):

    if 'user' not in session:
        return redirect('/login')

    return render_template(
        "seat.html",
        id=transport_id,
        price=price
    )


# ---------------- BOOK ----------------

@app.route('/book', methods=['POST'])
def book():

    if 'user' not in session:
        return redirect('/login')

    t_id = request.form['transport_id']
    seat = request.form.get('seat')
    price = request.form['price']

    info = get_transport_info(t_id)

    if not info:
        return "Transport not found", 404

    session['booking_flow'] = {

        "transport_id": t_id,
        "type": info['type'],
        "source": info['source'],
        "destination": info['destination'],
        "details": info['details'],
        "seat": seat,
        "price": price,
        "date": str(datetime.date.today())

    }

    return render_template(
        "payment.html",
        booking=session['booking_flow']
    )


def parse_seat_count(seat_value):
    """Parse seat string and return count of seats"""
    if not seat_value:
        return 1
    # Handle comma-separated seats like "1, 2, 3"
    seats = [s.strip() for s in str(seat_value).split(',') if s.strip()]
    return len(seats) if seats else 1


# ---------------- PAYMENT ----------------

@app.route('/payment', methods=['POST'])
def payment():

    if 'user' not in session:
        return redirect('/login')

    booking = session['booking_flow']

    booking_id = str(uuid.uuid4())[:8]

    booking['booking_id'] = booking_id
    booking['email'] = session['user']
    booking['payment_method'] = request.form.get('method')
    booking['payment_reference'] = request.form.get('reference')
    booking['price'] = float(booking['price'])

    db.create_booking(

        booking_id=booking['booking_id'],
        user_id=session['user'],
        email=booking['email'],
        transport_id=booking['transport_id'],
        listing_type=booking['type'],
        source=booking['source'],
        destination=booking['destination'],
        details=booking['details'],
        seat=booking['seat'],
        price=booking['price'],
        date=booking['date'],
        payment_method=booking['payment_method'],
        payment_reference=booking['payment_reference']

    )

    # Calculate number of seats booked
    seats_booked = parse_seat_count(booking.get('seat'))
    
    db.update_seat_availability(
        booking['transport_id'],
        booking['date'],
        seats_booked
    )

    # Send booking confirmation notification
    send_booking_confirmation(booking)

    session.pop('booking_flow')

    return render_template(
        "ticket.html",
        booking=booking
    )


# ---------------- CANCEL BOOKING ----------------

@app.route('/cancel/<booking_id>')
def cancel_booking(booking_id):

    if 'user' not in session:
        return redirect('/login')

    db.cancel_booking(booking_id)

    # Send cancellation alert notification
    send_cancellation_alert(booking_id, session['user'])

    return redirect('/dashboard')


# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


# ---------------- RUN APP ----------------

if __name__ == "__main__":

    PORT = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=True
    )