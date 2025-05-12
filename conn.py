from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import random

app = Flask(__name__)
app.secret_key = "supersecret"  # Required for flashing messages

# MongoDB Atlas connection
client = MongoClient("mongodb+srv://202311050:Mangodb99.@cluster50.fqokfj9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster50&tls=true")
db = client["project"]
users_col = db["users"]
events_col = db["events"]

# Simulated session for current user (use Flask-Login for production)
logged_in_user = {}

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    global logged_in_user
    if request.method == "POST":
        college_id = request.form['college_id']
        password = request.form['password']
        user = users_col.find_one({"college_id": college_id, "password": password})
        if user:
            logged_in_user = user
            return redirect(url_for("view_events"))
        flash("❌ Invalid college ID or password")
    return render_template("login.html")


@app.route('/register', methods=["GET", "POST"])
def register_user():
    if request.method == "POST":
        role = request.form['role']
        if role == "admin":  # Prevent admin registration through form
            flash("❌ Admin registration not allowed")
            return redirect(url_for("register_user"))
            
        name = request.form['name']
        password = request.form['password']
        college_id = request.form['college_id']
        organization = request.form.get('organization', '').strip()

        user_data = {
            "role": role,
            "name": name,
            "password": password,
            "college_id": college_id
        }

        if role == "organizer":
            user_data["organizer_id"] = f"ORG{random.randint(10000, 99999)}"
            user_data["organization"] = organization or "N/A"

        users_col.insert_one(user_data)
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route('/events')
def view_events():
    if not logged_in_user:
        return redirect(url_for("login"))
    
    is_admin = logged_in_user.get("role") == "admin"
    is_organizer = logged_in_user.get("role") == "organizer"
    college_id = logged_in_user.get("college_id")
    
    # Admins and organizers see all events, students see all events
    all_events = list(events_col.find())
    
    # Get organizer names
    organizer_ids = [e.get("organizer_id") for e in all_events]
    organizers = {org["college_id"]: org["name"] 
                 for org in users_col.find({"college_id": {"$in": organizer_ids}})}
    
    # Prepare event data
    processed_events = []
    for event in all_events:
        processed_events.append({
            **event,
            "is_my_event": event.get("organizer_id") == college_id,  # True only for event creator
            "organizer_name": organizers.get(event.get("organizer_id"), "Unknown"),
            "organizer_email": f"{event.get('organizer_id', '')}@college.edu"
        })
    
    return render_template("events.html",
                         events=processed_events,
                         is_admin=is_admin,
                         is_organizer=is_organizer,
                         college_id=college_id)
    
    return render_template("events.html",
                         events=processed_events,
                         is_admin=is_admin,
                         is_organizer=is_organizer,
                         college_id=college_id)

@app.route('/add_event', methods=["GET", "POST"])
def add_event():
    if not logged_in_user or logged_in_user.get("role") != "organizer":
        flash("❌ Only organizers can add events.")
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["event_name"]
        location = request.form["event_location"]
        date = request.form["event_date"]
        time = request.form["event_time"]
        max_regs = int(request.form["max_registrations"])
        description = request.form.get("description", "").strip()

        events_col.insert_one({
            "name": name,
            "location": location,
            "date": date,
            "time": time,
            "max_registrations": max_regs,
            "description": description,
            "registered_users": [],
            "organizer_id": logged_in_user.get("college_id")
        })
        return redirect(url_for("view_events"))
    return render_template("add_event.html")

@app.route('/confirm_registration/<event_id>', methods=["GET"])
def confirm_registration(event_id):
    if not logged_in_user:
        return redirect(url_for("login"))
    
    event = events_col.find_one({"_id": ObjectId(event_id)})
    if not event:
        flash("❌ Event not found.")
        return redirect(url_for("view_events"))
    
    if logged_in_user.get("college_id") in event.get("registered_users", []):
        flash("✅ You are already registered for this event.")
        return redirect(url_for("view_events"))
    
    if len(event.get("registered_users", [])) >= event.get("max_registrations", 0):
        flash("❌ Registration full for this event.")
        return redirect(url_for("view_events"))
    
    return render_template("confirm_registration.html", event=event)

@app.route('/register_event/<event_id>', methods=["POST"])
def register_for_event(event_id):
    if not logged_in_user:
        flash("❌ Please log in to register for events.")
        return redirect(url_for("login"))
    
    # Check if user clicked "Cancel"
    if request.form.get('choice') == 'no':
        flash("⚠️ Registration cancelled.")
        return redirect(url_for("view_events"))
    
    event = events_col.find_one({"_id": ObjectId(event_id)})
    if not event:
        flash("❌ Event not found.")
        return redirect(url_for("view_events"))
    
    user_id = logged_in_user.get("college_id")
    
    if user_id in event.get("registered_users", []):
        flash("✅ You have already registered for this event.")
        return redirect(url_for("view_events"))
    
    if len(event.get("registered_users", [])) >= event.get("max_registrations", 0):
        flash("❌ Registration full for this event.")
        return redirect(url_for("view_events"))
    
    events_col.update_one(
        {"_id": ObjectId(event_id)},
        {"$addToSet": {"registered_users": user_id}}
    )
    flash("✅ Successfully registered!")
    return redirect(url_for("view_events"))

@app.route('/event_registrations/<event_id>')
def view_event_registrations(event_id):
    if not logged_in_user or logged_in_user.get("role") != "organizer":
        flash("❌ Only organizers can view event registrations.")
        return redirect(url_for("login"))
    
    event = events_col.find_one({"_id": ObjectId(event_id)})
    if not event:
        flash("❌ Event not found.")
        return redirect(url_for("view_events"))
    
    # Check if current user is the organizer of this event
    if event.get("organizer_id") != logged_in_user.get("college_id"):
        flash("❌ You can only view registrations for your own events.")
        return redirect(url_for("view_events"))
    
    # Get user details for all registered users
    registered_users = []
    for college_id in event.get("registered_users", []):
        user = users_col.find_one({"college_id": college_id})
        if user:
            registered_users.append({
                "name": user.get("name", "Unknown"),
                "college_id": college_id,
                "role": user.get("role", "student")
            })
    
    return render_template("event_registrations.html", 
                         event=event, 
                         registered_users=registered_users)

if __name__ == '__main__':
    app.run(debug=True)