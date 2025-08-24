from flask import Flask
import os
from extensions import db, login_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345678986'  # Ganti dengan secret key yang aman
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

from models import User
from models import Surat
import json
from routes import *
from models import ResetPasswordRequest
from flask import url_for

@app.context_processor
def inject_notifikasi():
    notifikasi = []
    from flask_login import current_user
    if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated and getattr(current_user, 'role', None) == 'admin':
        pending = ResetPasswordRequest.query.filter_by(status='pending').all()
        for req in pending:
            notifikasi.append({
                'text': f"Permintaan reset password dari {req.username}",
                'url': url_for('reset_password_requests')
            })
    return dict(notifikasi_list=notifikasi)

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists('db.sqlite3'):
            db.create_all()
        # Tambah data contoh surat jika belum ada
        if Surat.query.count() == 0:
            surat_list = [
                Surat(
                    nama='Surat Keterangan Domisili',
                    deskripsi='Surat keterangan domisili untuk keperluan administrasi.',
                    field_form=json.dumps([
                        {'name': 'nama_lengkap', 'label': 'Nama Lengkap', 'type': 'text', 'required': True},
                        {'name': 'nik', 'label': 'NIK', 'type': 'text', 'required': True},
                        {'name': 'alamat', 'label': 'Alamat', 'type': 'text', 'required': True},
                        {'name': 'rt_rw', 'label': 'RT/RW', 'type': 'text', 'required': True},
                        {'name': 'keperluan', 'label': 'Keperluan', 'type': 'text', 'required': True}
                    ])
                ),
                Surat(
                    nama='Surat Keterangan Usaha',
                    deskripsi='Surat keterangan usaha untuk keperluan usaha.',
                    field_form=json.dumps([
                        {'name': 'nama_lengkap', 'label': 'Nama Lengkap', 'type': 'text', 'required': True},
                        {'name': 'nik', 'label': 'NIK', 'type': 'text', 'required': True},
                        {'name': 'nama_usaha', 'label': 'Nama Usaha', 'type': 'text', 'required': True},
                        {'name': 'alamat_usaha', 'label': 'Alamat Usaha', 'type': 'text', 'required': True},
                        {'name': 'jenis_usaha', 'label': 'Jenis Usaha', 'type': 'text', 'required': True}
                    ])
                ),
                Surat(
                    nama='Surat Pengantar SKCK',
                    deskripsi='Surat pengantar SKCK untuk keperluan kepolisian.',
                    field_form=json.dumps([
                        {'name': 'nama_lengkap', 'label': 'Nama Lengkap', 'type': 'text', 'required': True},
                        {'name': 'nik', 'label': 'NIK', 'type': 'text', 'required': True},
                        {'name': 'tempat_tanggal_lahir', 'label': 'Tempat/Tanggal Lahir', 'type': 'text', 'required': True},
                        {'name': 'alamat', 'label': 'Alamat', 'type': 'text', 'required': True},
                        {'name': 'keperluan', 'label': 'Keperluan', 'type': 'text', 'required': True}
                    ])
                )
            ]
            db.session.bulk_save_objects(surat_list)
            db.session.commit()
    import webbrowser
    try:
        webbrowser.get('chrome').open('http://localhost:5001')
    except:
        webbrowser.open('http://localhost:5001')
    app.run(debug=True, port=5001) 