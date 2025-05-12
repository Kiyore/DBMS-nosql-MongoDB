# 📅 Campus Event Management System

A Flask web app for managing campus events with MongoDB.

---

## ✨ Features

* Registration and login facility for Students, Organizers
* Organizers can add events
* Students can view & register for events
* Organizers can view event registrations
* Flash messages for feedback

---

## 👥 User Roles & Permissions

* **Admin**

  * Full control over the system
  * Can view all events and registrations
  * Can contact organizers (system can provide contact details like emails, phone numbers, etc.)
  * Admin accounts must be added manually in the database

* **Organizer**

  * Can create events with or without a limit on total registrations
  * Can view/manage registrations **for their events**
  * Cannot edit or delete events
  * Cannot register as a student

* **Student**

  * Can view all events
  * Can register for events
  * Two-step confirmation to prevent accidental registration

---

## ⚙️ Tech Stack

* Python (Flask)
* MongoDB Atlas (`pymongo`)
* HTML
* CSS

---

## 🚀 Setup

1. Install dependencies:

   ```bash
   pip install flask pymongo bson
   ```

2. Update MongoDB connection in `app.py`

3. Run the app:

   ```bash
   python app.py
   ```

4. Open:

   ```bash
   http://localhost:5000
   ```

---

## ✅ Highlights

* ✅ Ready to use
* ✅ Simple interface
* ✅ MongoDB backend

---
