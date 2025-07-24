#!/usr/bin/env python
"""
Django script to populate random data for Room, Session, Todo, TrackTodo, and Ranking models.
Run this script with: python manage.py shell < populate_random_data.py
Or place it in management/commands/ and run: python manage.py populate_data
"""

import os
import django
import random
from datetime import datetime, timedelta, date
from django.utils import timezone
from faker import Faker

# Setup Django environment (if running as standalone script)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'challenge.settings')
django.setup()

from authapp.models import CustomUser
from pages.models import Room, Session, Todo, TrackTodo, SessionRanking, RoomRanking

fake = Faker()

def create_users(num_users=20):
    """Create random users"""
    users = []
    for _ in range(num_users):
        username = fake.unique.user_name()
        email = fake.unique.email()
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password='testpass123'
        )
        users.append(user)
        print(f"Created user: {username}")
    
    return users

def create_rooms(users, num_rooms=10):
    """Create random rooms with random members"""
    rooms = []
    room_names = [
        "Study Squad", "Code Warriors", "Book Club", "Math Masters",
        "Language Learners", "Project Hustlers", "Focus Zone", "Productivity Palace",
        "Study Sanctuary", "Achievement Arena", "Learning Lab", "Focus Factory",
        "Brain Builders", "Goal Getters", "Progress Party"
    ]
    
    for i in range(num_rooms):
        name = random.choice(room_names) + f" {i+1}" if i >= len(room_names) else room_names[i]
        bio = fake.text(max_nb_chars=200)
        admin = random.choice(users)
        
        # Randomly decide if room has password (30% chance)
        password = fake.password(length=8) if random.random() < 0.3 else None
        
        room = Room.objects.create(
            name=name,
            bio=bio,
            password=password,
            admin=admin
        )
        
        # Add random members (including admin)
        num_members = random.randint(3, min(10, len(users)))
        members = random.sample(users, num_members)
        if admin not in members:
            members.append(admin)
        
        room.members.set(members)
        rooms.append(room)
        print(f"Created room: {name} with {len(members)} members")
    
    return rooms

def create_sessions(rooms, num_sessions_per_room=3):
    """Create random sessions for each room"""
    sessions = []
    session_topics = [
        "Daily Study Session", "Project Sprint", "Coding Marathon", "Reading Challenge",
        "Exam Prep", "Assignment Focus", "Research Deep Dive", "Skill Building",
        "Practice Session", "Review Time", "Creative Work", "Problem Solving"
    ]
    
    for room in rooms:
        # Ensure only one active session per room at a time
        active_session_created = False
        
        for i in range(random.randint(1, num_sessions_per_room)):
            name = f"{random.choice(session_topics)} {i+1}"
            description = fake.text(max_nb_chars=150)
            
            # Create session dates
            session_type = random.choice(['past', 'current', 'future'])
            
            if session_type == 'past':
                # Past completed session
                days_ago = random.randint(15, 60)
                start_date = timezone.now() - timedelta(days=days_ago)
                session_length = random.randint(3, 14)
                finish_date = (start_date + timedelta(days=session_length)).date()
                
            elif session_type == 'current' and not active_session_created:
                # Current active session (no finish date or future finish date)
                days_ago = random.randint(1, 10)
                start_date = timezone.now() - timedelta(days=days_ago)
                
                # 50% chance of having finish date in future, 50% no finish date
                if random.random() < 0.5:
                    future_days = random.randint(5, 20)
                    finish_date = (timezone.now() + timedelta(days=future_days)).date()
                else:
                    finish_date = None
                active_session_created = True
                
            else:
                # Future session or additional past session
                if session_type == 'future':
                    days_ahead = random.randint(1, 30)
                    start_date = timezone.now() + timedelta(days=days_ahead)
                    session_length = random.randint(5, 20)
                    finish_date = (start_date + timedelta(days=session_length)).date()
                else:
                    # Additional past session
                    days_ago = random.randint(30, 90)
                    start_date = timezone.now() - timedelta(days=days_ago)
                    session_length = random.randint(3, 14)
                    finish_date = (start_date + timedelta(days=session_length)).date()
            
            try:
                session = Session.objects.create(
                    room=room,
                    name=name,
                    description=description,
                    start_date=start_date,
                    finish_date=finish_date
                )
                
                # Add random members from room
                room_members = list(room.members.all())
                num_session_members = random.randint(2, len(room_members))
                session_members = random.sample(room_members, num_session_members)
                session.members.set(session_members)
                
                sessions.append(session)
                print(f"Created session: {name} in {room.name} ({'active' if session.is_active else 'completed'})")
                
            except Exception as e:
                print(f"Skipped session {name} due to validation error: {e}")
                continue
    
    return sessions

def create_todos_and_tracking(sessions):
    """Create todos and tracking data for sessions"""
    task_templates = [
        "Complete chapter {} of {}",
        "Practice {} problems",
        "Review {} concepts",
        "Write {} pages of {}",
        "Study {} for {} minutes",
        "Research {} topic",
        "Complete {} exercises",
        "Prepare for {} exam",
        "Finish {} assignment",
        "Learn {} new skill"
    ]
    
    subjects = [
        "Mathematics", "Physics", "Chemistry", "Biology", "Computer Science",
        "History", "Literature", "Psychology", "Economics", "Philosophy",
        "Spanish", "French", "Art", "Music", "Statistics"
    ]
    
    for session in sessions:
        for member in session.members.all():
            # Each member gets 2-5 todos
            num_todos = random.randint(2, 5)
            
            for _ in range(num_todos):
                # Generate random task
                template = random.choice(task_templates)
                if "{}" in template:
                    # Fill in template placeholders
                    subject = random.choice(subjects)
                    number = random.randint(1, 20)
                    task = template.format(number, subject)
                else:
                    task = template
                
                # Random completion status
                completed = random.random() < 0.6  # 60% chance completed
                completed_on = None
                if completed:
                    # Random completion date within session period
                    if session.start_date:
                        start = session.start_date.date()
                        end = session.finish_date or timezone.now().date()
                        days_diff = (end - start).days
                        if days_diff > 0:
                            completed_on = start + timedelta(days=random.randint(0, days_diff))
                        else:
                            completed_on = start
                
                todo = Todo.objects.create(
                    user=member,
                    session=session,
                    task=task,
                    completed=completed,
                    completed_on=completed_on
                )
                
                # Create tracking data
                create_tracking_for_todo(todo, session)
                
                print(f"Created todo: {task[:30]}... for {member.username}")

def create_tracking_for_todo(todo, session):
    """Create random tracking data for a todo"""
    # Generate tracking data for random days
    if session.start_date:
        start_date = session.start_date.date()
        today = timezone.now().date()
        
        # For past sessions, use the finish date or a reasonable end date
        if session.finish_date and session.finish_date <= today:
            end_date = session.finish_date
        elif session.finish_date and session.finish_date > today:
            # For active sessions with future finish date, track up to today
            end_date = today
        else:
            # For active sessions without finish date, track up to today
            end_date = today
        
        # Create tracking for random days in the session period
        current_date = start_date
        cumulative_hours = 0
        
        while current_date <= end_date:
            # 40% chance of working on this todo on any given day
            if random.random() < 0.4:
                daily_hours = round(random.uniform(0.5, 4.0), 2)  # 0.5 to 4 hours
                cumulative_hours += daily_hours
                
                TrackTodo.objects.create(
                    todo=todo,
                    day=current_date,
                    hours=daily_hours,
                    hours_till_day=cumulative_hours
                )
            
            current_date += timedelta(days=1)

def populate_all_data():
    """Main function to populate all data"""
    print("Starting data population...")
    
    # Clear existing data (optional - uncomment if needed)
    # print("Clearing existing data...")
    # TrackTodo.objects.all().delete()
    # Todo.objects.all().delete()
    # SessionRanking.objects.all().delete()
    # RoomRanking.objects.all().delete()
    # Session.objects.all().delete()
    # Room.objects.all().delete()
    # CustomUser.objects.all().delete()
    
    # Create data
    print("Creating users...")
    users = create_users(25)
    
    print("Creating rooms...")
    rooms = create_rooms(users, 8)
    
    print("Creating sessions...")
    sessions = create_sessions(rooms, 4)
    
    print("Creating todos and tracking data...")
    create_todos_and_tracking(sessions)
    
    print("Updating rankings...")
    # Update all rankings
    for room in rooms:
        room.updateRoomRankings()
    
    for session in sessions:
        session.updateSessionRanking()
    
    print("Data population completed!")
    print(f"Created:")
    print(f"  - {CustomUser.objects.count()} users")
    print(f"  - {Room.objects.count()} rooms")
    print(f"  - {Session.objects.count()} sessions")
    print(f"  - {Todo.objects.count()} todos")
    print(f"  - {TrackTodo.objects.count()} tracking entries")
    print(f"  - {SessionRanking.objects.count()} session rankings")
    print(f"  - {RoomRanking.objects.count()} room rankings")

if __name__ == "__main__":
    populate_all_data()