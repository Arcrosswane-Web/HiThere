from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, join_room, leave_room, send
import random
import string
from datetime import datetime 

app = Flask(__name__)
app.config["SECRET_KEY"] = "Arcrosswane1212"
# Add session configuration for better persistence
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

socketio = SocketIO(app, cors_allowed_origins="*")
rooms = {}

def RandomRoomCode():
    return "".join(random.choices(string.ascii_uppercase, k=4))

@app.route('/')
def Home():
    return render_template('index.html')

@app.route('/Features')
def Features():
    return render_template('Features.html')
    
@app.route('/ContactUs')
def ContactUs():
    return render_template('ContactUs.html')
    
@app.route('/AboutUs')
def AboutUs():
    return render_template('AboutUs.html')

@app.route('/CreateRoom', methods=['GET', 'POST'])
def CreateRoom():
    if request.method == "POST":
        name = request.form.get('username')
        if not name:  # Check if name is provided
            return render_template('CreateRoom.html', errors=["Name is required"], name=name)

        session.clear()
        room = RandomRoomCode()
        session["room"] = room
        session["name"] = name
        session.permanent = True  # Make session permanent

        rooms[room] = {
            "members": [],
            "messages": []
        }
        return redirect("/ChatRoom")

    return render_template('CreateRoom.html')

@app.route('/JoinRoom', methods=["GET", "POST"])
def JoinRoom():
    if request.method == 'POST':
        room = request.form.get('room')
        name = request.form.get('name')

        if not room or not name:  # Check if both are provided
            return render_template('JoinRoom.html', errors=["Room code is required", "Name is required"])

        session.clear()

        if room not in rooms: 
            return render_template('JoinRoom.html', errors=["Room does not exist"], name=name, room=room)

        session["room"] = room
        session["name"] = name
        session.permanent = True  # Make session permanent

        # Don't add to members here - do it in connect event
        return redirect("/ChatRoom")  

    return render_template('JoinRoom.html')

@app.route('/ChatRoom')
def ChatRoom():
    # Check if session variables exist
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return redirect("/")

    if room not in rooms:
        return redirect("/")

    return render_template('ChatRoom.html', room=room, messages=rooms[room]["messages"])

@socketio.on('message')
def message(data):
    room = session.get("room")
    name = session.get("name")

    # Better session validation
    if not room or not name or room not in rooms: 
        print(f"Invalid session - room: {room}, name: {name}")
        return

    content = {
        "name": name,
        "message": data["data"],
        "date": datetime.now().strftime("%H:%M:%S")
    }
    socketio.emit("message", content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{name} said: {data['data']}")

@socketio.on('connect')
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        print(f"Connection rejected - missing session data. Room: {room}, Name: {name}")
        return False  # Reject connection

    if room not in rooms:
        print(f"Connection rejected - room {room} does not exist")
        return False  # Reject connection

    join_room(room)

    # Check if user is already in the room to avoid duplicates
    if name not in rooms[room]["members"]:
        rooms[room]["members"].append(name)

    content = {
        "name": name,
        "message": "has entered the room",
        "date": datetime.now().strftime("%H:%M:%S")
    }
    socketio.emit("message", content, to=room)
    print(f"{name} joined room {room}")

@socketio.on('disconnect')
def disconnect():
    room = session.get("room")
    name = session.get("name")

    if not room or not name or room not in rooms:
        return

    leave_room(room)

    # Fix: Use remove() instead of push()
    if name in rooms[room]["members"]:
        rooms[room]["members"].remove(name)

    content = {
        "name": name,
        "message": "has left the room",
        "date": datetime.now().strftime("%H:%M")
    }
    socketio.emit("message", content, to=room)
    print(f"{name} left room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)
