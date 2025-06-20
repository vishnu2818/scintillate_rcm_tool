# 🚀 Scintillate RCM Insurance Update Tool (v2.2)

A streamlined web-based platform for managing insurance payer edit rules and CPT modifier instructions using Django and Excel import.

---

## 📦 Features

- ✅ **JWT Authentication** with role-based access (Admin, Manager, Viewer)
- 📥 **Dual Excel Import** for `InsuranceEdit` and `ModifierRule` models
- 🔍 **Auto-mapping & Preview** of Excel data before import
- 📊 **Unified Dashboard** with filters: Client → Payer → Category/Sub-category
- 📄 **Instructional Cards** & **Modifier Tables**
- 👥 **Admin Panel** for managing clients and rules
- 📤 **Export to CSV** for admins

---

## 🛠️ Tech Stack

- Python 3.12+
- Django 5.x
- SQLite (default, can swap with PostgreSQL)
- Tailwind CSS for UI
- JWT (via `djangorestframework-simplejwt`)
- pandas (for Excel import)

---

## 🔐 Roles & Permissions

| Role         | Permissions                |
|--------------|----------------------------|
| `Admin`      | Full CRUD, all clients     |
| `Manager`    | CRUD for assigned client   |
| `Viewer`     | Read-only access           |

---

## 🚀 Setup Instructions

1. **Clone the Repo**

git clone https://github.com/YOUR_USERNAME/scintillate_rcm_tool.git
cd scintillate_rcm_tool

2. **Set up Virtual Environment**

python3 -m venv env
source env/bin/activate

3. **Install Dependencies**
   
pip install -r requirements.txt

4. **Run Migrations**

python manage.py migrate

5. **Create Superuser**

python manage.py createsuperuser

6. **Start the Server**
7. 
python manage.py runserver
