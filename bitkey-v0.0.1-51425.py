import sys, json, os, hashlib, secrets, string, requests
from PyQt5 import QtWidgets, QtGui, QtCore

# Constants
USER_DATA_FILE = "users.json"
PASSWORD_DATA_DIR = "data"

os.makedirs(PASSWORD_DATA_DIR, exist_ok=True)

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)

def generate_password(length, use_symbols):
    chars = string.digits
    if use_symbols:
        chars += string.ascii_letters + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))

# Main App
class BitKeyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BitKey")
        self.setGeometry(300, 100, 1000, 600)
        self.setStyleSheet("background-color: #1b1f23; color: white; font-family: Arial;")

        self.users = load_users()
        self.current_user = None
        self.passwords = []

        self.init_login_ui()

    def init_login_ui(self):
        self.central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        logo = QtWidgets.QLabel("🔑 BitKey")
        logo.setStyleSheet("font-size: 30px; color: #00aaff;")
        logo.setAlignment(QtCore.Qt.AlignCenter)

        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setStyleSheet("padding: 10px;")

        self.pass_input = QtWidgets.QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pass_input.setStyleSheet("padding: 10px;")

        self.message = QtWidgets.QLabel("")
        self.message.setStyleSheet("color: red;")

        login_btn = QtWidgets.QPushButton("Login")
        login_btn.clicked.connect(self.login)
        signup_btn = QtWidgets.QPushButton("Create Account")
        signup_btn.clicked.connect(self.signup)

        for btn in (login_btn, signup_btn):
            btn.setStyleSheet("background-color: #00aaff; color: white; padding: 10px; margin-top: 10px;")

        layout.addWidget(logo)
        layout.addWidget(self.email_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.message)
        layout.addWidget(login_btn)
        layout.addWidget(signup_btn)

        self.central.setLayout(layout)
        self.setCentralWidget(self.central)

    def login(self):
        email = self.email_input.text()
        password = self.pass_input.text()
        if email in self.users and self.users[email] == hash_password(password):
            self.current_user = email
            self.load_passwords()
            self.init_main_ui()
        else:
            self.message.setText("Invalid credentials.")

    def signup(self):
        email = self.email_input.text()
        password = self.pass_input.text()
        if email in self.users:
            self.message.setText("User already exists.")
        else:
            self.users[email] = hash_password(password)
            save_users(self.users)
            self.current_user = email
            self.passwords = []
            self.save_passwords()
            self.init_main_ui()

    def load_passwords(self):
        path = os.path.join(PASSWORD_DATA_DIR, f"{self.current_user}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                self.passwords = json.load(f)
        else:
            self.passwords = []

    def save_passwords(self):
        path = os.path.join(PASSWORD_DATA_DIR, f"{self.current_user}.json")
        with open(path, "w") as f:
            json.dump(self.passwords, f, indent=2)

    def init_main_ui(self):
        self.sidebar = QtWidgets.QListWidget()
        self.sidebar.addItems(["🏠 Home", "🔐 Generate", "👤 Account"])
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #121417;
                color: white;
                font-size: 18px;
                padding: 10px;
            }
            QListWidget::item {
                height: 50px;
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #00aaff;
                color: black;
            }
        """)
        self.sidebar.setFixedWidth(200)
        self.sidebar.currentRowChanged.connect(self.display_tab)

        self.stack = QtWidgets.QStackedWidget()
        self.home_tab = self.create_home_tab()
        self.gen_tab = self.create_generate_tab()
        self.account_tab = self.create_account_tab()

        self.stack.addWidget(self.home_tab)
        self.stack.addWidget(self.gen_tab)
        self.stack.addWidget(self.account_tab)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)

        container = QtWidgets.QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def display_tab(self, index):
        self.stack.setCurrentIndex(index)

    def create_home_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("Your Passwords")
        title.setStyleSheet("font-size: 20px; color: #00aaff;")
        layout.addWidget(title)

        self.pw_list = QtWidgets.QListWidget()
        self.refresh_passwords()
        layout.addWidget(self.pw_list)

        tab.setLayout(layout)
        return tab

    def refresh_passwords(self):
        self.pw_list.clear()
        for i, pw in enumerate(self.passwords):
            exposed = "⚠️ " if pw.get("exposed", False) else ""
            item_widget = QtWidgets.QWidget()
            h_layout = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(f"{exposed}{pw['value']}")
            label.setStyleSheet("color: white;")
            copy_btn = QtWidgets.QPushButton("Copy")
            copy_btn.setFixedWidth(60)
            copy_btn.clicked.connect(lambda _, val=pw['value']: self.copy_to_clipboard(val))
            del_btn = QtWidgets.QPushButton("Delete")
            del_btn.setFixedWidth(60)
            del_btn.clicked.connect(lambda _, idx=i: self.delete_password(idx))
            h_layout.addWidget(label)
            h_layout.addStretch()
            h_layout.addWidget(copy_btn)
            h_layout.addWidget(del_btn)
            item_widget.setLayout(h_layout)
            list_item = QtWidgets.QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            self.pw_list.addItem(list_item)
            self.pw_list.setItemWidget(list_item, item_widget)

    def copy_to_clipboard(self, text):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(text)

    def delete_password(self, index):
        if 0 <= index < len(self.passwords):
            del self.passwords[index]
            self.save_passwords()
            self.refresh_passwords()

    def create_generate_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("Generate Password")
        title.setStyleSheet("font-size: 20px; color: #00aaff;")
        layout.addWidget(title)

        self.length_input = QtWidgets.QSpinBox()
        self.length_input.setRange(4, 100)
        self.length_input.setValue(12)
        self.use_symbols = QtWidgets.QCheckBox("Include Letters & Symbols")
        self.use_symbols.setChecked(True)

        gen_button = QtWidgets.QPushButton("Generate")
        gen_button.setStyleSheet("background-color: #00aaff; color: white; padding: 10px;")
        gen_button.clicked.connect(self.generate_password_action)

        self.generated_label = QtWidgets.QLabel("")
        layout.addWidget(QtWidgets.QLabel("Length:"))
        layout.addWidget(self.length_input)
        layout.addWidget(self.use_symbols)
        layout.addWidget(gen_button)
        layout.addWidget(self.generated_label)

        tab.setLayout(layout)
        return tab

    def generate_password_action(self):
        length = self.length_input.value()
        include_symbols = self.use_symbols.isChecked()
        password = generate_password(length, include_symbols)
        exposed = self.check_password_exposure(password)
        self.generated_label.setText(f"Generated: {password}")
        self.passwords.append({"value": password, "exposed": exposed})
        self.save_passwords()
        self.refresh_passwords()

    def check_password_exposure(self, password):
        sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1[:5]
        try:
            res = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5)
            if res.status_code == 200:
                hashes = res.text.splitlines()
                return any(line.startswith(sha1[5:]) for line in hashes)
        except Exception:
            pass
        return False

    def create_account_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("Account Info")
        title.setStyleSheet("font-size: 20px; color: #00aaff;")
        layout.addWidget(title)

        email_label = QtWidgets.QLabel(f"Email: {self.current_user}")
        count_label = QtWidgets.QLabel(f"Passwords generated: {len(self.passwords)}")

        logout_button = QtWidgets.QPushButton("Logout")
        logout_button.setStyleSheet("background-color: red; color: white; padding: 10px;")
        logout_button.clicked.connect(self.logout)

        layout.addWidget(email_label)
        layout.addWidget(count_label)
        layout.addStretch()
        layout.addWidget(logout_button)
        tab.setLayout(layout)
        return tab

    def logout(self):
        self.current_user = None
        self.init_login_ui()

# Run app
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    bitkey = BitKeyApp()
    bitkey.show()
    sys.exit(app.exec_())
