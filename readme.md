# CTRLD

A comprehensive Django-based productivity tracking application that enables users to create collaborative study/work rooms, manage sessions, track todos, and monitor progress through detailed statistics and leaderboards.

## 🌟 Features

### 🏠 Room Management
- Create password-protected rooms for collaborative sessions
- Room admin controls and member management
- Room-specific settings and configurations
- Room leaderboards to track member performance

### 📅 Session Management  
- Admin-controlled session creation and management
- Session joining for room members
- **Auto-end sessions** with configurable deadlines (middleware-powered)
- Real-time deadline monitoring and automatic session termination
- Session-specific leaderboards and rankings
- Detailed session descriptions and metadata

### ✅ Todo Management
- Personal todo creation and management within sessions
- Track completion times and progress
- Todo analytics and insights
- Time-based todo tracking with daily organization

### 📊 Comprehensive Statistics
- **Personal Stats**: Individual user performance metrics
- **Session Stats**: Detailed session analytics with charts
- **Room Stats**: Overall room performance tracking  
- Interactive charts and visualizations
- Historical data analysis and trends

### 🔐 Authentication & User Management
- Custom user authentication system
- User profiles with customizable settings
- Password change functionality
- User activity tracking (last online status)
- Permission-based access control

### 🏆 Leaderboard System
- Room leaderboards with total hours tracking
- Session rankings based on participation and completion
- Real-time ranking updates
- Performance comparison tools

### 🔔 Notification System
- Admin notices and announcements
- Notice read status tracking
- HTML-formatted notices support
- User-specific notification preferences
- **Custom signals** for automated notification triggers

### 🎭 Demo Experience
- **One-click demo login** from homepage
- Pre-populated demo user with sample data
- Demo tasks and sessions for immediate exploration
- Full feature showcase without registration required

## 🛠️ Technology Stack

- **Backend**: Django 4.x
- **API**: Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Authentication**: Custom Django Authentication
- **Frontend**: Django Templates with HTML/CSS/JavaScript
- **Testing**: Django TestCase with 120+ test cases
- **Advanced Django Features**:
  - Custom Middleware (3 implementations)
  - Custom Signals for notifications
  - Custom Mixins for access control
  - Custom Permission Classes for API security

## 📁 Project Structure

```
├── api/                    # RESTful API endpoints
├── authapp/               # Authentication & user management
├── challenge/             # Main Django project configuration
├── pages/                 # Core application logic
│   ├── models.py         # Database models
│   ├── views.py          # View controllers  
│   ├── urls.py           # URL routing
│   ├── forms.py          # Django forms
│   ├── middleware.py     # Custom middleware implementations
│   ├── signals.py        # Custom signals for notifications
│   ├── mixins.py         # Custom mixins (Member/Admin/NotDemo)
│   ├── permissions.py    # Custom permission classes
│   ├── templates/        # HTML templates
│   └── tests/            # Comprehensive test suite
├── stats/                 # Statistics & analytics
└── static/               # Static assets
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Pr45H4nt/CtrlD
   cd CtrlD
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Open your browser to `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## 🏗️ Advanced Django Architecture

### Custom Middleware
1. **Session Auto-End Middleware**: Automatically terminates sessions when deadlines are reached
2. **Last Active Middleware**: Tracks user activity and updates last online status
3. **Admin URL Protection Middleware**: Restricts `/admin/` access to admin users only (404 for regular users)

### Custom Signals
- **Notification Signals**: Automated notification triggers for system events
- **User Activity Signals**: Real-time user status updates
- **Session Lifecycle Signals**: Session start/end event handling

### Custom Mixins
- **`MemberRequiredMixin`**: Ensures only room/session members can access views
- **`AdminRequiredMixin`**: Restricts access to admin users only
- **`NotDemoUserMixin`**: Prevents demo users from performing certain actions

### Custom Permission Classes (API)
- **MemberOnlyPermission**: API access limited to room/session members
- **AdminOnlyPermission**: API endpoints restricted to administrators
- **AllowAllPermission**: Public API access with proper validation

## 🧪 Testing

The project includes a comprehensive test suite with **120+ test cases** covering:

- Model functionality and relationships
- View logic and permissions
- API endpoints
- User authentication flows
- Room and session management
- Statistics calculations

**Run all tests:**
```bash
python manage.py test
```

**Run specific app tests:**
```bash
python manage.py test authapp
python manage.py test pages
python manage.py test api
python manage.py test stats
```

**Test coverage:**
- Authentication & User Management
- Room Creation & Management  
- Session Lifecycle Management (including auto-end)
- Todo Operations
- Statistics Calculations
- API Endpoints & Custom Permissions
- Custom Middleware Functionality
- Custom Mixins & Access Control
- Signal Processing
- Demo User Functionality

## 📊 Key Models

- **CustomUser**: Extended user model with profile information
- **Room**: Collaborative spaces with password protection
- **Session**: Time-tracked work/study sessions
- **Todo**: Task management within sessions
- **SessionRanking**: Performance tracking and leaderboards
- **Notice**: System-wide notifications and announcements

## 🔗 API Endpoints

The project includes a full REST API for:
- User authentication and management
- Room operations (CRUD)
- Session management
- Todo operations  
- Statistics retrieval
- Real-time data updates

API documentation available at `/api/` when running the development server.

## 🎯 Usage Flow

### For New Users
1. **Demo Experience**: Click "Demo Login" on homepage for instant access with sample data
2. **User Registration/Login**: Create account or sign in for full functionality

### Core Workflow
1. **Room Creation**: Create a new room or join existing one with password
2. **Session Management**: Room admin starts a session with configurable deadline
3. **Todo Tracking**: Members join session and add their todos
4. **Real-time Monitoring**: Sessions auto-end when deadlines are reached
5. **Progress Analysis**: Track completion and view comprehensive statistics
6. **Leaderboards**: Compare performance with other members

### Demo Features
- Pre-configured rooms and sessions
- Sample todos and completed tasks
- Historical statistics and charts
- Full leaderboard demonstrations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Bug Reports

If you find a bug, please create an issue with:
- Bug description
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)

## 📞 Support

For support and questions, please open an issue in the GitHub repository.

---

**Built with ❤️ using Django**