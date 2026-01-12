from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///request_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # student, secretary, lecturer, head_of_dept
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'name': self.name,
            'department': self.department
        }

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(50), nullable=False)  # Study Approval, Appeal, Postponement, General
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected, in_progress
    priority = db.Column(db.String(20), default='medium')  # high, medium, low
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    secretary_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    head_of_dept_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    final_notes = db.Column(db.Text, nullable=True)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='student_requests')
    secretary = db.relationship('User', foreign_keys=[secretary_id], backref='secretary_requests')
    lecturer = db.relationship('User', foreign_keys=[lecturer_id], backref='lecturer_requests')
    head_of_dept = db.relationship('User', foreign_keys=[head_of_dept_id], backref='head_requests')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'request_type': self.request_type,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'final_notes': self.final_notes,
            'secretary_name': self.secretary.name if self.secretary else None,
            'lecturer_name': self.lecturer.name if self.lecturer else None
        }

class ApprovalLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # approved, rejected
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    request = db.relationship('Request', backref='approval_logs')
    approver = db.relationship('User', backref='approval_actions')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=True)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')
    request = db.relationship('Request', backref='request_notifications')

# Helper function to check if user is authenticated and is head of dept
def require_head_of_dept(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        user = User.query.get(session['user_id'])
        if not user or user.role != 'head_of_dept':
            return jsonify({'error': 'Forbidden - Head of Department access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.role == 'head_of_dept':
            return redirect(url_for('head_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return jsonify({'success': True, 'role': user.role, 'redirect': url_for('head_dashboard' if user.role == 'head_of_dept' else 'dashboard')})
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/quick-login/<role>')
def quick_login(role):
    # Demo quick login
    role_map = {
        'student': 'student',
        'secretary': 'secretary',
        'lecturer': 'lecturer',
        'head_of_dept': 'head_of_dept'
    }
    
    if role not in role_map:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(role=role_map[role]).first()
    if user:
        session['user_id'] = user.id
        if user.role == 'head_of_dept':
            return redirect(url_for('head_dashboard'))
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/head-dashboard')
def head_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != 'head_of_dept':
        return redirect(url_for('dashboard'))
    return render_template('head_dashboard.html')

# API Routes for Department Head

@app.route('/api/head/pending-requests', methods=['GET'])
@require_head_of_dept
def get_pending_requests():
    """Fetch pending approval requests with filtering"""
    # Get filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    request_type = request.args.get('request_type')
    
    # Base query - only pending requests
    query = Request.query.filter_by(status='pending')
    
    # Apply filters
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from)
            query = query.filter(Request.created_at >= date_from_obj)
        except:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to)
            query = query.filter(Request.created_at <= date_to_obj)
        except:
            pass
    
    if request_type:
        query = query.filter_by(request_type=request_type)
    
    # Order by created date (newest first)
    requests = query.order_by(Request.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'requests': [req.to_dict() for req in requests],
        'count': len(requests)
    })

@app.route('/api/head/approve-request/<int:request_id>', methods=['POST'])
@require_head_of_dept
def approve_request(request_id):
    """Approve or reject a request"""
    data = request.get_json()
    action = data.get('action')  # 'approve' or 'reject'
    notes = data.get('notes', '')
    
    if action not in ['approve', 'reject']:
        return jsonify({'success': False, 'error': 'Invalid action'}), 400
    
    request_obj = Request.query.get_or_404(request_id)
    
    # Only allow approval of pending requests
    if request_obj.status != 'pending':
        return jsonify({'success': False, 'error': 'Request is not pending'}), 400
    
    # Update request status
    request_obj.status = 'approved' if action == 'approve' else 'rejected'
    request_obj.head_of_dept_id = session['user_id']
    request_obj.updated_at = datetime.utcnow()
    
    # Log approval action
    log_entry = ApprovalLog(
        request_id=request_id,
        approver_id=session['user_id'],
        action=action,
        notes=notes
    )
    db.session.add(log_entry)
    
    # Create notification for student
    notification = Notification(
        user_id=request_obj.student_id,
        message=f'Your request "{request_obj.title}" has been {action}d by the Department Head.',
        request_id=request_id
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Request {action}d successfully',
        'request': request_obj.to_dict()
    })

@app.route('/api/head/add-final-notes/<int:request_id>', methods=['POST'])
@require_head_of_dept
def add_final_notes(request_id):
    """Add final notes visible to student"""
    data = request.get_json()
    notes = data.get('notes', '').strip()
    
    if not notes:
        return jsonify({'success': False, 'error': 'Notes cannot be empty'}), 400
    
    request_obj = Request.query.get_or_404(request_id)
    
    # Update final notes
    request_obj.final_notes = notes
    request_obj.updated_at = datetime.utcnow()
    
    # Create notification for student
    notification = Notification(
        user_id=request_obj.student_id,
        message=f'Final notes have been added to your request "{request_obj.title}".',
        request_id=request_id
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Final notes added successfully',
        'request': request_obj.to_dict()
    })

@app.route('/api/head/request-details/<int:request_id>', methods=['GET'])
@require_head_of_dept
def get_request_details(request_id):
    """Get detailed information about a specific request"""
    request_obj = Request.query.get_or_404(request_id)
    
    # Get approval logs
    logs = ApprovalLog.query.filter_by(request_id=request_id).order_by(ApprovalLog.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'request': request_obj.to_dict(),
        'approval_logs': [{
            'id': log.id,
            'approver_name': log.approver.name,
            'action': log.action,
            'notes': log.notes,
            'created_at': log.created_at.isoformat() if log.created_at else None
        } for log in logs]
    })

# Initialize database
def create_tables():
    with app.app_context():
        db.create_all()
        
        # Create demo users if they don't exist
        if not User.query.filter_by(role='head_of_dept').first():
            head = User(
                email='head@example.com',
                password_hash=generate_password_hash('password'),
                role='head_of_dept',
                name='Department Head',
                department='Computer Science'
            )
            db.session.add(head)
        
        if not User.query.filter_by(role='student').first():
            student = User(
                email='student@example.com',
                password_hash=generate_password_hash('password'),
                role='student',
                name='John Student',
                department='Computer Science'
            )
            db.session.add(student)
        
        if not User.query.filter_by(role='secretary').first():
            secretary = User(
                email='secretary@example.com',
                password_hash=generate_password_hash('password'),
                role='secretary',
                name='Jane Secretary',
                department='Computer Science'
            )
            db.session.add(secretary)
        
        if not User.query.filter_by(role='lecturer').first():
            lecturer = User(
                email='lecturer@example.com',
                password_hash=generate_password_hash('password'),
                role='lecturer',
                name='Dr. Smith Lecturer',
                department='Computer Science'
            )
            db.session.add(lecturer)
        
        # Create some sample pending requests
        if Request.query.count() == 0:
            student = User.query.filter_by(role='student').first()
            if student:
                requests_data = [
                    {
                        'student_id': student.id,
                        'request_type': 'Study Approval',
                        'title': 'Request for Course Overload',
                        'description': 'I would like to request approval to take 6 courses this semester.',
                        'priority': 'high'
                    },
                    {
                        'student_id': student.id,
                        'request_type': 'Appeal',
                        'title': 'Grade Appeal Request',
                        'description': 'I would like to appeal my grade in CS101.',
                        'priority': 'medium'
                    },
                    {
                        'student_id': student.id,
                        'request_type': 'Postponement',
                        'title': 'Exam Postponement Request',
                        'description': 'I need to postpone my final exam due to medical reasons.',
                        'priority': 'high'
                    },
                    {
                        'student_id': student.id,
                        'request_type': 'General',
                        'title': 'General Inquiry',
                        'description': 'I have a question about the curriculum.',
                        'priority': 'low'
                    }
                ]
                
                for req_data in requests_data:
                    req = Request(**req_data)
                    db.session.add(req)
        
        db.session.commit()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
