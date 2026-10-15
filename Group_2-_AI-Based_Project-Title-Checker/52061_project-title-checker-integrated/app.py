"""
AI Based Project Similarity Detection System
=============================================
Flask Backend — Uses ML/NLP pipeline for intelligent title matching.

Tech Stack: Python, Flask, scikit-learn, NLTK, SQLite
"""

import os
import sqlite3
from datetime import timedelta
from functools import wraps

from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

# Import our AI/ML engine
from ml_engine import engine as similarity_engine
from ir_routes import create_ir_blueprint, ensure_ir_tables
from ir.recommend import content_based
import dl_engine

# ============================================================
# App Configuration
# ============================================================

app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'ai-project-similarity-detection-secret-2024')
app.permanent_session_lifetime = timedelta(hours=24)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.db')


# ============================================================
# Database Helpers
# ============================================================

def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables and seed default faculty account."""
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'faculty')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'submitted' CHECK(status IN ('submitted', 'approved', 'warned')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            faculty_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (faculty_id) REFERENCES users(id)
        );
    ''')

    # Backward-compatible schema migration for DL fields
    try:
        col_names = [r[1] for r in conn.execute('PRAGMA table_info(projects)').fetchall()]
        if 'description' not in col_names:
            conn.execute('ALTER TABLE projects ADD COLUMN description TEXT DEFAULT ""')
        if 'domain' not in col_names:
            conn.execute('ALTER TABLE projects ADD COLUMN domain TEXT DEFAULT ""')
        conn.commit()
    except Exception as e:
        print(f'[MIGRATE] Column check error: {e}')

    ensure_ir_tables(conn)

    # Seed default faculty account
    existing = conn.execute(
        'SELECT id FROM users WHERE username = ?', ('faculty',)
    ).fetchone()
    if not existing:
        hashed = generate_password_hash('faculty123')
        conn.execute(
            'INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)',
            ('faculty', hashed, 'Dr. Faculty', 'faculty')
        )
        conn.commit()
        print('[OK] Default faculty account created: username=faculty, password=faculty123')

    # Add a few example projects on the first run so the IR search can be tested.
    # These are clearly labelled demo records and can be replaced with real projects.
    project_count = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
    if project_count == 0:
        demo_projects = [
            ('demo_student_1', 'Asha Demo', 'Student Performance Prediction System'),
            ('demo_student_2', 'Rohan Demo', 'Student Result Analysis Using Machine Learning'),
            ('demo_student_3', 'Neha Demo', 'Online Shopping Management System'),
            ('demo_student_4', 'Arjun Demo', 'Movie Recommendation System'),
            ('demo_student_5', 'Sara Demo', 'Face Recognition Attendance System'),
            ('demo_student_6', 'Kabir Demo', 'Product Demand Prediction Using Python'),
            ('demo_student_7', 'Mira Demo', 'Travel Group Recommendation System'),
            ('demo_student_8', 'Ishaan Demo', 'Library Management System'),
        ]
        for username, name, title in demo_projects:
            conn.execute(
                'INSERT OR IGNORE INTO users (username, password, name, role) VALUES (?, ?, ?, ?)',
                (username, generate_password_hash('demo123'), name, 'student')
            )
            student = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            conn.execute(
                'INSERT OR IGNORE INTO projects (student_id, title, status) VALUES (?, ?, ?)',
                (student['id'], title, 'approved')
            )
        conn.commit()
        print('[OK] Example project records added for testing the IR dashboard.')

    conn.close()


# ============================================================
# Auth Decorators
# ============================================================

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Please log in to continue'}), 401
        return f(*args, **kwargs)
    return decorated


def require_student(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Please log in to continue'}), 401
        if session.get('role') != 'student':
            return jsonify({'error': 'Access denied. Students only.'}), 403
        return f(*args, **kwargs)
    return decorated


def require_faculty(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Please log in to continue'}), 401
        if session.get('role') != 'faculty':
            return jsonify({'error': 'Access denied. Faculty only.'}), 403
        return f(*args, **kwargs)
    return decorated


# ============================================================
# Auth Routes
# ============================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    name = data.get('name', '').strip()

    if not username or not password or not name:
        return jsonify({'error': 'All fields are required'}), 400
    if len(username) < 3:
        return jsonify({'error': 'Roll No must be at least 3 characters'}), 400
    if len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400

    conn = get_db()
    if conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        conn.close()
        return jsonify({'error': 'This Roll No is already registered'}), 409

    hashed = generate_password_hash(password)
    cursor = conn.execute(
        'INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)',
        (username, hashed, name, 'student')
    )
    conn.commit()
    uid = cursor.lastrowid
    conn.close()

    session.permanent = True
    session['user_id'] = uid
    session['username'] = username
    session['name'] = name
    session['role'] = 'student'

    return jsonify({
        'message': 'Registration successful',
        'user': {'id': uid, 'username': username, 'name': name, 'role': 'student'}
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    session.permanent = True
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['name'] = user['name']
    session['role'] = user['role']

    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user['id'], 'username': user['username'],
            'name': user['name'], 'role': user['role']
        }
    })


@app.route('/api/auth/me')
def me():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify({'user': {
        'id': session['user_id'], 'username': session['username'],
        'name': session['name'], 'role': session['role']
    }})


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})


# ============================================================
# Student Routes
# ============================================================

def _get_existing_projects(exclude_student_id=None):
    """Fetch all project records, optionally excluding one student."""
    conn = get_db()
    if exclude_student_id:
        rows = conn.execute(
            'SELECT id, student_id, title, description, domain, status FROM projects WHERE student_id != ?',
            (exclude_student_id,)
        ).fetchall()
    else:
        rows = conn.execute('SELECT id, student_id, title, description, domain, status FROM projects').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_existing_titles(exclude_student_id=None):
    """Fetch all project titles, optionally excluding one student."""
    return [p['title'] for p in _get_existing_projects(exclude_student_id)]


@app.route('/api/student/project')
@require_student
def get_student_project():
    conn = get_db()
    project = conn.execute('''
        SELECT p.*, u.name as student_name, u.username
        FROM projects p JOIN users u ON p.student_id = u.id
        WHERE p.student_id = ?
    ''', (session['user_id'],)).fetchone()
    conn.close()
    return jsonify({'project': dict(project) if project else None})


@app.route('/api/student/project', methods=['POST'])
@require_student
def submit_project():
    """Submit a new project title — runs through the AI/ML similarity pipeline."""
    data = request.get_json()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()

    if not title or len(title) < 5:
        return jsonify({'error': 'Project title must be at least 5 characters long'}), 400

    conn = get_db()
    if conn.execute('SELECT id FROM projects WHERE student_id = ?', (session['user_id'],)).fetchone():
        conn.close()
        return jsonify({'error': 'You already have a project. Use update to change your title.'}), 409
    conn.close()

    # --- AI/ML Similarity Check (Multi-Field Hybrid) ---
    existing_projects = _get_existing_projects(exclude_student_id=session['user_id'])
    existing_titles = [p['title'] for p in existing_projects]
    is_rejected, similar_titles, analysis = similarity_engine.check_title(
        new_title=title,
        existing_titles=existing_titles,
        new_description=description,
        existing_projects=existing_projects,
    )

    if is_rejected:
        exact = any(s.get('is_exact_match') for s in similar_titles)
        return jsonify({
            'error': ('This exact title already exists! Choose a different title.'
                      if exact
                      else 'AI detected your title is too similar to existing title(s). Choose a more unique title.'),
            'similarTitles': similar_titles,
            'analysis': analysis,
            'rejected': True,
        }), 409

    # Accepted — save
    # Run Deep Learning analysis (LSTM domain classification, Autoencoder anomaly detection, Neural NER)
    dl_analysis = dl_engine.analyze_proposal(title, description)
    predicted_domain = dl_analysis.get('domain_classification', {}).get('predicted_domain') or ''

    conn = get_db()
    cur = conn.execute(
        'INSERT INTO projects (student_id, title, description, domain, status) VALUES (?, ?, ?, ?, ?)',
        (session['user_id'], title, description, predicted_domain, 'submitted')
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()

    return jsonify({
        'message': 'Project title accepted by AI! Submitted successfully.',
        'project': {'id': pid, 'title': title, 'description': description, 'domain': predicted_domain, 'status': 'submitted'},
        'analysis': analysis,
        'dl_analysis': dl_analysis,
        'recommendations': _recommendations_for(title, session['user_id']),
    }), 201


@app.route('/api/student/project', methods=['PUT'])
@require_student
def update_project():
    """Update project title — re-runs AI/ML similarity check."""
    data = request.get_json()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()

    if not title or len(title) < 5:
        return jsonify({'error': 'Project title must be at least 5 characters long'}), 400

    conn = get_db()
    existing_proj = conn.execute(
        'SELECT id, description, domain FROM projects WHERE student_id = ?', (session['user_id'],)
    ).fetchone()
    conn.close()

    if not existing_proj:
        return jsonify({'error': 'No project found. Submit a new title.'}), 404

    # --- AI/ML Similarity Check (Multi-Field Hybrid) ---
    existing_projects = _get_existing_projects(exclude_student_id=session['user_id'])
    existing_titles = [p['title'] for p in existing_projects]
    is_rejected, similar_titles, analysis = similarity_engine.check_title(
        new_title=title,
        existing_titles=existing_titles,
        new_description=description,
        existing_projects=existing_projects,
    )

    if is_rejected:
        exact = any(s.get('is_exact_match') for s in similar_titles)
        return jsonify({
            'error': ('This exact title already exists! Choose a different title.'
                      if exact
                      else 'AI detected your title is too similar to existing title(s). Choose a more unique title.'),
            'similarTitles': similar_titles,
            'analysis': analysis,
            'rejected': True,
        }), 409

    # Run Deep Learning analysis
    if not description and existing_proj['description']:
        description = existing_proj['description']
    dl_analysis = dl_engine.analyze_proposal(title, description)
    predicted_domain = dl_analysis.get('domain_classification', {}).get('predicted_domain') or ''

    conn = get_db()
    conn.execute(
        'UPDATE projects SET title = ?, description = ?, domain = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE student_id = ?',
        (title, description, predicted_domain, 'submitted', session['user_id'])
    )
    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Title updated and accepted by AI!',
        'project': {'id': existing_proj['id'], 'title': title, 'description': description, 'domain': predicted_domain, 'status': 'submitted'},
        'analysis': analysis,
        'dl_analysis': dl_analysis,
        'recommendations': _recommendations_for(title, session['user_id']),
    })


@app.route('/api/student/warnings')
@require_student
def get_student_warnings():
    conn = get_db()
    warnings = conn.execute('''
        SELECT w.*, u.name as faculty_name
        FROM warnings w
        JOIN users u ON w.faculty_id = u.id
        JOIN projects p ON w.project_id = p.id
        WHERE p.student_id = ?
        ORDER BY w.created_at DESC
    ''', (session['user_id'],)).fetchall()

    project = conn.execute(
        'SELECT id FROM projects WHERE student_id = ?', (session['user_id'],)
    ).fetchone()
    if project:
        conn.execute(
            'UPDATE warnings SET is_read = 1 WHERE project_id = ? AND is_read = 0',
            (project['id'],)
        )
        conn.commit()
    conn.close()
    return jsonify({'warnings': [dict(w) for w in warnings]})


@app.route('/api/student/warnings/count')
@require_student
def warning_count():
    conn = get_db()
    project = conn.execute(
        'SELECT id FROM projects WHERE student_id = ?', (session['user_id'],)
    ).fetchone()
    if not project:
        conn.close()
        return jsonify({'count': 0})
    r = conn.execute(
        'SELECT COUNT(*) as c FROM warnings WHERE project_id = ? AND is_read = 0',
        (project['id'],)
    ).fetchone()
    conn.close()
    return jsonify({'count': r['c']})


# ============================================================
# Faculty Routes
# ============================================================

@app.route('/api/faculty/projects')
@require_faculty
def faculty_projects():
    conn = get_db()
    projects = conn.execute('''
        SELECT p.*, u.name as student_name, u.username as student_username,
            (SELECT COUNT(*) FROM warnings w WHERE w.project_id = p.id) as warning_count
        FROM projects p
        JOIN users u ON p.student_id = u.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    conn.close()

    projects_list = [dict(p) for p in projects]

    # AI/ML: compute pairwise similarities
    if len(projects_list) >= 2:
        titles = [p['title'] for p in projects_list]
        sim_map = similarity_engine.pairwise_max_similarity(titles)
        for p in projects_list:
            max_sim, most_similar = sim_map.get(p['title'], (0, ''))
            p['max_similarity'] = max_sim
            p['most_similar_to'] = most_similar
    else:
        for p in projects_list:
            p['max_similarity'] = 0
            p['most_similar_to'] = ''

    return jsonify({'projects': projects_list})


@app.route('/api/faculty/warn/<int:project_id>', methods=['POST'])
@require_faculty
def warn_student(project_id):
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message or len(message) < 5:
        return jsonify({'error': 'Warning message must be at least 5 characters'}), 400

    conn = get_db()
    if not conn.execute('SELECT id FROM projects WHERE id = ?', (project_id,)).fetchone():
        conn.close()
        return jsonify({'error': 'Project not found'}), 404

    conn.execute(
        'INSERT INTO warnings (project_id, faculty_id, message) VALUES (?, ?, ?)',
        (project_id, session['user_id'], message)
    )
    conn.execute(
        'UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        ('warned', project_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Warning sent to student successfully'}), 201


@app.route('/api/faculty/approve/<int:project_id>', methods=['POST'])
@require_faculty
def approve_project(project_id):
    conn = get_db()
    if not conn.execute('SELECT id FROM projects WHERE id = ?', (project_id,)).fetchone():
        conn.close()
        return jsonify({'error': 'Project not found'}), 404
    conn.execute(
        'UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        ('approved', project_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Project title approved successfully'})


@app.route('/api/faculty/stats')
@require_faculty
def faculty_stats():
    conn = get_db()
    stats = {
        'totalStudents':    conn.execute("SELECT COUNT(*) as c FROM users WHERE role='student'").fetchone()['c'],
        'totalProjects':    conn.execute("SELECT COUNT(*) as c FROM projects").fetchone()['c'],
        'submittedProjects': conn.execute("SELECT COUNT(*) as c FROM projects WHERE status='submitted'").fetchone()['c'],
        'approvedProjects': conn.execute("SELECT COUNT(*) as c FROM projects WHERE status='approved'").fetchone()['c'],
        'warnedProjects':   conn.execute("SELECT COUNT(*) as c FROM projects WHERE status='warned'").fetchone()['c'],
        'totalWarnings':    conn.execute("SELECT COUNT(*) as c FROM warnings").fetchone()['c'],
    }
    conn.close()
    return jsonify({'stats': stats})


# ============================================================
# Deep Learning (DL) APIs  ->  see dl_engine/
# ============================================================

@app.route('/api/dl/analyze', methods=['POST'])
@require_login
def dl_analyze():
    """Analyze arbitrary proposal text using LSTM, Autoencoder, and Neural NER."""
    data = request.get_json(silent=True) or {}
    title = str(data.get('title', '')).strip()
    description = str(data.get('description', '')).strip()
    if not title and not description:
        return jsonify({'error': 'Title or description required'}), 400
    return jsonify(dl_engine.analyze_proposal(title, description))


@app.route('/api/faculty/project/<int:project_id>/dl-analysis')
@require_faculty
def faculty_project_dl_analysis(project_id):
    """Retrieve decision-oriented Deep Learning and Similarity evaluation for a project."""
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    if not project:
        conn.close()
        return jsonify({'error': 'Project not found'}), 404
    p_dict = dict(project)

    other_rows = conn.execute(
        'SELECT id, title, description, domain, status FROM projects WHERE id != ?',
        (project_id,)
    ).fetchall()
    conn.close()
    other_projects = [dict(r) for r in other_rows]

    # Run Deep Learning models
    dl_res = dl_engine.analyze_proposal(p_dict.get('title', ''), p_dict.get('description', ''))

    # Run multi-field similarity comparison against other projects
    _, similar_list, _ = similarity_engine.check_title(
        new_title=p_dict.get('title', ''),
        existing_titles=[p['title'] for p in other_projects],
        new_description=p_dict.get('description', ''),
        new_domain=p_dict.get('domain', ''),
        existing_projects=other_projects,
    )

    top_sim = similar_list[0]['similarity'] if similar_list else 0
    top_matches = [
        {
            'title': s['title'],
            'similarity': s['similarity'],
            'risk_level': s['risk_level'],
            'match_reason': s.get('match_reason', ''),
        }
        for s in similar_list[:4]
    ]

    # Calibrate overall review and recommendations
    if top_sim >= similarity_engine.REJECTION_THRESHOLD or any(s.get('is_exact_match') for s in similar_list):
        overall_review = "High Risk"
        recommendation = "Review for possible duplication"
        sim_risk_level = "High Risk"
    elif top_sim >= similarity_engine.REVIEW_THRESHOLD:
        overall_review = "Needs Review"
        recommendation = "Faculty review recommended"
        sim_risk_level = "Needs Review"
    else:
        sim_risk_level = "Low Risk"
        novelty_unusual = dl_res.get('novelty_analysis', {}).get('is_unusual', False)
        if novelty_unusual:
            overall_review = "Needs Review"
            recommendation = "Faculty review recommended (novel / unusual vocabulary)"
        else:
            overall_review = "Low Risk"
            recommendation = "No strong duplicate detected"

    # Novelty signal formatting
    autoencoder_res = dl_res.get('novelty_analysis', {})
    if autoencoder_res.get('status') == 'empty_input':
        novelty_signal = "Needs Review (empty proposal)"
    elif autoencoder_res.get('is_unusual'):
        novelty_signal = "Unusual"
    else:
        novelty_signal = "Normal"

    # Key technologies identified (from NER entity extraction)
    ner_grouped = dl_res.get('named_entities', {}).get('grouped', {})
    tech_candidates = []
    for cat in ['languages', 'frameworks', 'methods']:
        tech_candidates.extend(ner_grouped.get(cat, []))
    # Deduplicate while preserving order
    tech_identified = list(dict.fromkeys(tech_candidates))

    # Predicted domain & confidence
    dom_res = dl_res.get('domain_classification', {})
    predicted_domain = dom_res.get('predicted_domain') or (p_dict.get('domain') or 'Unclassified')
    dom_conf = dom_res.get('confidence_percent')
    is_uncertain = dom_res.get('is_uncertain', False)
    decision_status = dom_res.get('decision_status', 'Prediction Available')
    model_type = dom_res.get('model_type', 'Primary Domain Classifier')

    model_reliability = {
        'semantic_active': similarity_engine.semantic_service.is_available,
        'semantic_model': similarity_engine.semantic_service.status_message,
        'domain_classifier_note': (
            f"{model_type} ({dom_conf}% confidence, {decision_status})"
            if dom_conf and dom_conf > 0
            else "Domain classifier prediction available"
        ),
        'novelty_note': autoencoder_res.get('interpretation', 'Autoencoder reconstruction error signal'),
        'is_uncertain': is_uncertain,
        'decision_status': decision_status,
        'lstm_comparison': f"BiLSTM Sequence Model: {dom_res.get('lstm_domain', 'N/A')} ({dom_res.get('lstm_confidence_percent', 0)}%)",
    }

    decision_review = {
        'overall_review': overall_review,
        'similarity_score': top_sim,
        'similarity_risk': sim_risk_level,
        'closest_matches': top_matches,
        'predicted_domain': predicted_domain,
        'domain_confidence': dom_conf,
        'is_domain_uncertain': is_uncertain,
        'domain_decision_status': decision_status,
        'domain_model_type': model_type,
        'lstm_domain': dom_res.get('lstm_domain'),
        'lstm_confidence': dom_res.get('lstm_confidence_percent'),
        'key_technologies': tech_identified,
        'grouped_technologies': ner_grouped,
        'novelty_signal': novelty_signal,
        'novelty_percentile': autoencoder_res.get('percentile'),
        'final_recommendation': recommendation,
        'model_reliability': model_reliability,
    }

    return jsonify({
        'project': p_dict,
        'dl_analysis': dl_res,
        'decision_review': decision_review,
    })


# ============================================================
# Information Retrieval (IR) APIs  ->  see ir_routes.py / ir/
# ============================================================

app.register_blueprint(create_ir_blueprint(get_db, require_login, require_student, require_faculty))


def _recommendations_for(title, student_id):
    """Top-3 similar existing projects (current student's own project excluded)."""
    conn = get_db()
    rows = conn.execute('SELECT id, title, student_id FROM projects WHERE student_id != ?',
                        (student_id,)).fetchall()
    conn.close()
    return content_based(title, [dict(r) for r in rows], 3)


# ============================================================
# Page Routes
# ============================================================

@app.route('/')
def index():
    return send_from_directory('public', 'login.html')

@app.route('/student')
def student_page():
    return send_from_directory('public', 'student.html')

@app.route('/faculty')
def faculty_page():
    return send_from_directory('public', 'faculty.html')

@app.route('/ir')
def ir_page():
    return send_from_directory('public', 'ir.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('public', path)


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 3000))

    print()
    print('=' * 52)
    print('  AI Based Project Similarity Detection System')
    print(f'  Running at: http://localhost:{port}')
    print('=' * 52)
    print()
    print('  Faculty Login:  username=faculty  password=faculty123')
    print()

    app.run(host=os.environ.get('HOST', '127.0.0.1'), port=port,
            debug=os.environ.get('FLASK_DEBUG') == '1')
