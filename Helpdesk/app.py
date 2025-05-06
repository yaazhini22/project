from flask import Flask, render_template, request, redirect, url_for, flash
import random
import re
from datetime import datetime
from flask_mail import Mail, Message


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ticketsystem911@gmail.com'
app.config['MAIL_PASSWORD'] = 'eheb xiet ukmz elpc'
app.config['MAIL_DEFAULT_SENDER'] = 'ticketsystem911@gmail.com'

mail = Mail(app)


class Node:
    def __init__(self, department):
        self.department = department
        self.tickets = []  # List to store tickets for the same department
        self.left = None
        self.right = None

class BinaryTree:
    def __init__(self):
        self.root = None

    def insert(self, ticket):
        if not self.root:
            self.root = Node(ticket['department'])
            self.root.tickets.append(ticket)
        else:
            self._insert(self.root, ticket)

    def _insert(self, node, ticket):
        if ticket['department'].lower() < node.department.lower():
            if node.left is None:
                node.left = Node(ticket['department'])
                node.left.tickets.append(ticket)
            else:
                self._insert(node.left, ticket)
        elif ticket['department'].lower() > node.department.lower():
            if node.right is None:
                node.right = Node(ticket['department'])
                node.right.tickets.append(ticket)
            else:
                self._insert(node.right, ticket)
        else:
            node.tickets.append(ticket)  # Same department, add ticket to the list

    def mark_priority(self, ticket_id):
        return self._mark_priority(self.root, ticket_id)

    def _mark_priority(self, node, ticket_id):
        if node is None:
            return False
        for ticket in node.tickets:
            if ticket['id'] == ticket_id:
                ticket['priority'] = not ticket.get('priority', False)
                return True
        if self._mark_priority(node.left, ticket_id):
            return True
        return self._mark_priority(node.right, ticket_id)

    def get_sorted(self, reverse=False):
        tickets = self.to_list()

        # Separate priority and non-priority tickets
        priority_tickets = [ticket for ticket in tickets if ticket.get('priority', False)]
        non_priority_tickets = [ticket for ticket in tickets if not ticket.get('priority', False)]

        # Concatenate with priority tickets first
        sorted_tickets = priority_tickets + non_priority_tickets

        # Sort the combined list by department (optional)
        sorted_tickets.sort(key=lambda x: x['department'].lower(), reverse=reverse)

        return sorted_tickets
    def get_tickets_by_department(self, department):
        return self._get_tickets_by_department(self.root, department, [])

    def _get_tickets_by_department(self, node, department, result):
        if node is None:
            return result
        if node.department.lower() == department.lower():
            result.extend(node.tickets)
        self._get_tickets_by_department(node.left, department, result)
        self._get_tickets_by_department(node.right, department, result)
        return result

    def to_list(self):
        return self._to_list(self.root)

    def _to_list(self, node):
        if node is None:
            return []
        return self._to_list(node.left) + node.tickets + self._to_list(node.right)

    def update(self, ticket_id, updates):
        return self._update(self.root, ticket_id, updates)

    def _update(self, node, ticket_id, updates):
        if node is None:
            return False
        for ticket in node.tickets:
            if ticket['id'] == ticket_id:
                for key, value in updates.items():
                    ticket[key] = value
                return True
        if self._update(node.left, ticket_id, updates):
            return True
        return self._update(node.right, ticket_id, updates)
# Global binary tree to store ticket data
ticket_tree = BinaryTree()

# Function to generate a unique 6-digit ticket ID
def generate_ticket_id():
    return ''.join(random.choices('0123456789', k=6))

# Function to read ticket data from TXT file
# Function to read ticket data from TXT file
def read_txt():
    global ticket_tree
    ticket_tree = BinaryTree()  # Reset the tree
    with open('data.txt', mode='r') as file:
        next(file)  # Skip the first line (header)
        for line in file:
            fields = line.strip().split(',')
            if len(fields) >= 11: 
                ticket = {
                    'id': fields[0],
                    'name': fields[1],
                    'date': fields[2],  # Assuming date is stored in 'dd/mm/yyyy' format
                    'status': fields[3],
                    'subject': fields[4],
                    'department': fields[5],
                    'location': fields[6],
                    'room': fields[7],
                    'mobile': fields[8],
                    'time': fields[9],
                    'priority': fields[10].strip() == 'True'  # Convert 'True'/'False' to boolean
                }
                ticket_tree.insert(ticket)

def write_to_txt():
    tickets = ticket_tree.to_list()
    with open('data.txt', mode='w') as file:
        file.write("id,name,date,status,subject,department,location,room,mobile,time,priority\n")
        for ticket in tickets:
            file.write(f"{ticket['id']},{ticket['name']},{ticket['date']},{ticket['status']},{ticket['subject']},{ticket['department']},{ticket['location']},{ticket['room']},{ticket['mobile']},{ticket['time']},{ticket['priority']}\n")

# Call read_txt on startup to load existing data
read_txt()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signin')
def sign_in():
    return render_template('signin.html')

@app.route('/signup')
def signup_form():
    return render_template('signup.html')

@app.route('/submit_signup', methods=['POST'])
def submit_signup():
    email = request.form['email']
    name = request.form['name']
    password = request.form['password']
    
    # Validate email format
    if not re.match(r"[a-zA-Z0-9._%+-]+@ssn.edu.in", email):
        flash('Invalid email. Please use an SSN email address.')
        return redirect(url_for('signup_form'))

    # Check if the email already exists in signup.txt
    with open('signup.txt', 'r') as f:
        for line in f:
            # Ensure the line has the correct format
            fields = line.strip().split(',')
            if len(fields) == 3:
                stored_email, _, _ = fields
                if email == stored_email:
                    flash('Account already exists. Please sign in.')
                    return redirect(url_for('signup_form'))
            else:
                continue  # Skip improperly formatted lines

    # If the email does not exist, append the new account
    with open('signup.txt', 'a') as f:
        f.write(f'{email},{name},{password}\n')
    
    flash('Signup successful. Please sign in.')
    return redirect(url_for('sign_in'))


def check_credentials(email, password):
    with open('signup.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                stored_email, stored_name, stored_password = line.split(',')
                if email == stored_email and password == stored_password:
                    return stored_name  
    return None

@app.route('/submit_signin', methods=['POST'])
def submit_signin():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Server-side validation for email
    if not email or 'ssn.edu.in' not in email:
        flash('Invalid email. Email must include "ssn.edu.in". Please try again.')
        return redirect(url_for('sign_in'))
    
    name = check_credentials(email, password)
    if name:
        if email == 'admin@ssn.edu.in' and password == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard', name=name))
    else:
        flash('Invalid email or password. Please try again.')
        return redirect(url_for('sign_in'))

@app.route('/dashboard/<name>')
def dashboard(name):
    if name == 'admin':
        tickets = ticket_tree.to_list()
        return render_template('admin_dashboard.html', name=name, tickets=tickets)
    else:
        # Non-admin users will see a different view, possibly their own tickets
        user_tickets = [ticket for ticket in ticket_tree.to_list() if ticket['name'].lower() == name.lower()]
        return render_template('dashboard.html', name=name, tickets=user_tickets)

@app.route('/admin_dashboard')
def admin_dashboard():
    tickets = ticket_tree.get_sorted(reverse=True)  # True to display priority tickets on top
    return render_template('admin_dashboard.html', tickets=tickets)

@app.route('/submit_page')
def submit_page():
    ticket_id = generate_ticket_id()
    return render_template('submit.html', ticket_id=ticket_id, current_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/submit_ticket', methods=['POST'])
def submit_ticket():
    name = request.form['name']
    date = request.form['date']
    status = 'Opened'  # Set status to 'Opened' for new tickets
    subject = request.form['subject']
    department = request.form['department']
    location = request.form['location']
    room = request.form['room']
    mobile = request.form['mobile']
    time = request.form['time']
    user_email = request.form['email']
    
    ticket_id = generate_ticket_id()
    ticket = {
        'id': ticket_id,
        'name': name,
        'date': date,
        'status': status,
        'subject': subject,
        'department': department,
        'location': location,
        'room': room,
        'mobile': mobile,
        'time': time,
        'priority': False
    }
    
    ticket_tree.insert(ticket)
    write_to_txt()

    # Sending email to the user
    send_email(user_email, ticket_id, ticket)

    # Redirecting to ticket details page with correct ticket ID
    return redirect(url_for('ticket_details', ticket_id=ticket_id))



@app.route('/ticket/<ticket_id>')
def ticket_details(ticket_id):
    # Logic to fetch ticket details from your data structure or database
    ticket = next((t for t in ticket_tree.to_list() if t['id'] == ticket_id), None)

    if ticket:
        return render_template('details.html', ticket=ticket)
    else:
        return "Ticket not found."


def send_email(user_email, ticket_id, ticket_details):
    subject = f'Ticket Raised: {ticket_id}'
    body = f"""
    Dear {ticket_details['name']},

    Your ticket has been successfully raised. Here are the details:

    Ticket ID: {ticket_id}
    Date: {ticket_details['date']}
    Status: {ticket_details['status']}
    Subject: {ticket_details['subject']}
    Department: {ticket_details['department']}
    Location: {ticket_details['location']}
    Room: {ticket_details['room']}
    Mobile: {ticket_details['mobile']}
    Time: {ticket_details['time']}
    
    Thank you for raising the ticket. We will address your issue as soon as possible.

    Best regards,
    Help Desk Team
    """

    msg = Message(subject, recipients=[user_email])
    msg.body = body

    try:
        mail.send(msg)
        print(f"Email sent successfully to {user_email}")
    except Exception as e:
        print(f"Failed to send email to {user_email}. Error: {str(e)}")

@app.route('/opened_tickets/<name>')
def opened_tickets(name):
    user_tickets = [ticket for ticket in ticket_tree.to_list() if ticket['name'].lower() == name.lower() and ticket['status'] == 'Opened']
    return render_template('opened1.html', name=name, tickets=user_tickets)

@app.route('/closed_tickets/<name>')
def closed_tickets(name):
    user_tickets = [ticket for ticket in ticket_tree.to_list() if ticket['name'].lower() == name.lower() and ticket['status'] == 'Closed']
    return render_template('closed1.html', name=name, tickets=user_tickets)

@app.route('/admin_edit_ticket/<ticket_id>', methods=['POST'])
def admin_edit_ticket(ticket_id):
    new_status = request.form['status']
    ticket_tree.update(ticket_id, {'status': new_status})
    write_to_txt()
    return redirect(url_for('admin_dashboard'))

@app.route('/mark_priority/<ticket_id>', methods=['POST'])
def mark_priority(ticket_id):
    ticket_tree.mark_priority(ticket_id)
    write_to_txt()
    return redirect(url_for('admin_dashboard'))

@app.route('/view_opened')
def view_opened():
    tickets = [ticket for ticket in ticket_tree.to_list() if ticket['status'] == 'Opened']
    return render_template('admin_dashboard.html', tickets=tickets)

@app.route('/view_closed')
def view_closed():
    tickets = [ticket for ticket in ticket_tree.to_list() if ticket['status'] == 'Closed']
    return render_template('admin_dashboard.html', tickets=tickets)

@app.route('/search_tickets', methods=['GET'])
def search_tickets():
    query = request.args.get('query', '').lower()
    tickets = [ticket for ticket in ticket_tree.to_list() if query_in_ticket(query, ticket)]
    return render_template('admin_dashboard.html', tickets=tickets)

def query_in_ticket(query, ticket):
    for value in ticket.values():
        if isinstance(value, str) and query in value.lower():
            return True
    return False

def parse_date(date_str):
    return datetime.strptime(date_str, "%d/%m/%Y")

@app.route('/sort_tickets', methods=['GET'])
def sort_tickets():
    order = request.args.get('order', 'latest').lower()
    tickets = ticket_tree.to_list()

    # Sort tickets based on the date
    sorted_tickets = sorted(
        tickets, 
        key=lambda ticket: parse_date(ticket['date']),
        reverse=(order == 'latest')
    )

    return render_template('admin_dashboard.html', tickets=sorted_tickets)

@app.route('/departments')
def departments():
    return render_template('departments.html')

@app.route('/view_tickets_by_department/<department>')
def view_tickets_by_department(department):
    filtered_tickets = ticket_tree.get_tickets_by_department(department)
    return render_template('department_tickets.html', department=department, tickets=filtered_tickets)

if __name__ == '__main__':
    app.run(debug=True)
