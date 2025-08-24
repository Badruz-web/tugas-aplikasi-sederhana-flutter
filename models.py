from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin/operator/warga
    whatsapp = db.Column(db.String(20), nullable=True)  # nomor WA, wajib untuk warga, opsional untuk admin/operator

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password) 

class Surat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.Text)
    # field_form: JSON string  field dinamis 
    field_form = db.Column(db.Text, nullable=False)
    # belangko_default: 'desa' atau 'kabupaten'
    belangko_default = db.Column(db.String(20), default='desa')

class PengajuanSurat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    surat_id = db.Column(db.Integer, db.ForeignKey('surat.id'), nullable=False)
    data_pengajuan = db.Column(db.Text, nullable=False)  # JSON string data isian
    status = db.Column(db.String(20), default='diajukan')  # diajukan, diproses, selesai, ditolak
    tanggal_pengajuan = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='pengajuan_surat')
    surat = db.relationship('Surat', backref='pengajuan') 

class LoginHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='login_history') 

class ResetPasswordRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, selesai
    requested_at = db.Column(db.DateTime, default=datetime.utcnow) 