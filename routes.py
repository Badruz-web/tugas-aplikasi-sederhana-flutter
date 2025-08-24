from flask import render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, login_manager
from models import User, Surat, PengajuanSurat
from werkzeug.security import generate_password_hash, check_password_hash
import json
from app import app
import pdfkit
import io
from datetime import datetime
from weasyprint import HTML
from flask import make_response

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['Badruz']
        password = request.form['Sudarto']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            flash('Username sudah terdaftar')
            return redirect(url_for('register'))
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registrasi berhasil, silakan login')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Username atau password salah')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('dashboard_admin_main'))
    elif current_user.role == 'operator':
        return redirect(url_for('dashboard_operator_main'))
    elif current_user.role == 'warga':
        return redirect(url_for('dashboard_warga_main'))
    else:
        flash('Role tidak dikenali')
        return redirect(url_for('login'))

@app.route('/dashboard-admin-main')
@login_required
def dashboard_admin_main():
    if current_user.role != 'admin':
        flash('Hanya admin yang dapat mengakses halaman ini.')
        return redirect(url_for('dashboard'))
    return render_template('dashboard_admin.html')

@app.route('/dashboard-operator-main')
@login_required
def dashboard_operator_main():
    if current_user.role != 'operator':
        flash('Hanya operator yang dapat mengakses halaman ini.')
        return redirect(url_for('dashboard'))
    return render_template('dashboard_operator.html')

@app.route('/dashboard-warga-main')
@login_required
def dashboard_warga_main():
    if current_user.role != 'warga':
        flash('Hanya warga yang dapat mengakses halaman ini.')
        return redirect(url_for('dashboard'))
    return render_template('dashboard_warga.html')

@app.route('/pengajuan-surat', methods=['GET', 'POST'])
@login_required
def pengajuan_surat():
    # Hanya admin dan warga yang boleh akses
    if current_user.role not in ['admin', 'warga']:
        flash('Hanya admin dan warga yang dapat mengajukan surat.')
        return redirect(url_for('dashboard'))
    jenis_surat_list = Surat.query.all()
    if request.method == 'POST':
        surat_id = request.form.get('surat_id')
        surat = Surat.query.get(surat_id)
        if not surat:
            flash('Jenis surat tidak ditemukan.')
            return redirect(url_for('pengajuan_surat'))
        # Ambil field dinamis dari surat
        field_form = json.loads(surat.field_form)
        data_pengajuan = {}
        for field in field_form:
            data_pengajuan[field['name']] = request.form.get(field['name'], '')
        pengajuan = PengajuanSurat(
            user_id=current_user.id,
            surat_id=surat.id,
            data_pengajuan=json.dumps(data_pengajuan),
            status='diajukan'
        )
        db.session.add(pengajuan)
        db.session.commit()
        flash('Pengajuan surat berhasil diajukan!')
        return redirect(url_for('dashboard'))
    return render_template('pengajuan_surat.html', jenis_surat_list=jenis_surat_list)

@app.route('/dashboard-admin', methods=['GET', 'POST'])
@login_required
def dashboard_admin():
    if current_user.role != 'admin':
        flash('Hanya admin yang dapat mengakses halaman ini.')
        return redirect(url_for('dashboard'))
    pengajuan_list = PengajuanSurat.query.order_by(PengajuanSurat.tanggal_pengajuan.desc()).all()
    if request.method == 'POST':
        pengajuan_id = request.form.get('pengajuan_id')
        status = request.form.get('status')
        pengajuan = PengajuanSurat.query.get(pengajuan_id)
        if pengajuan and status in ['diajukan', 'diproses', 'selesai', 'ditolak']:
            pengajuan.status = status
            db.session.commit()
            flash('Status pengajuan berhasil diubah.')
        return redirect(url_for('dashboard_admin'))
    return render_template('dashboard_admin_pengajuan.html', pengajuan_list=pengajuan_list)

@app.route('/cetak-surat/<int:pengajuan_id>')
@login_required
def cetak_surat(pengajuan_id):
    if current_user.role != 'admin':
        flash('Hanya admin yang dapat mencetak surat.')
        return redirect(url_for('dashboard'))
    pengajuan = PengajuanSurat.query.get_or_404(pengajuan_id)
    data = json.loads(pengajuan.data_pengajuan)
    return render_template('cetak_surat.html', pengajuan=pengajuan, data=data)

@app.route('/cetak-surat/<int:pengajuan_id>/pdf')
@login_required
def cetak_surat_pdf(pengajuan_id):
    if current_user.role != 'admin':
        flash('Hanya admin yang dapat mencetak surat.')
        return redirect(url_for('dashboard'))
    pengajuan = PengajuanSurat.query.get_or_404(pengajuan_id)
    data = json.loads(pengajuan.data_pengajuan)
    # Pilih belangko berdasarkan parameter atau default dari jenis surat
    belangko = request.args.get('belangko', pengajuan.surat.belangko_default)
    rendered = render_template('template_surat_pdf.html', pengajuan=pengajuan, data=data, belangko=belangko)
    pdf = HTML(string=rendered, base_url=request.host_url).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=surat_{pengajuan.id}.pdf'
    return response

@app.route('/riwayat-pengajuan')
@login_required
def riwayat_pengajuan():
    if current_user.role != 'warga':
        flash('Hanya warga yang dapat melihat riwayat pengajuan mereka.')
        return redirect(url_for('dashboard'))
    pengajuan_list = PengajuanSurat.query.filter_by(user_id=current_user.id).order_by(PengajuanSurat.tanggal_pengajuan.desc()).all()
    return render_template('riwayat_pengajuan.html', pengajuan_list=pengajuan_list)

@app.route('/laporan-surat', methods=['GET', 'POST'])
@login_required
def laporan_surat():
    if current_user.role != 'admin':
        flash('Hanya admin yang dapat melihat laporan surat.')
        return redirect(url_for('dashboard'))
    dari = request.args.get('dari')
    sampai = request.args.get('sampai')
    query = PengajuanSurat.query
    if dari:
        dari_date = datetime.strptime(dari, '%Y-%m-%d')
        query = query.filter(PengajuanSurat.tanggal_pengajuan >= dari_date)
    if sampai:
        sampai_date = datetime.strptime(sampai, '%Y-%m-%d')
        query = query.filter(PengajuanSurat.tanggal_pengajuan <= sampai_date)
    pengajuan_list = query.order_by(PengajuanSurat.tanggal_pengajuan.desc()).all()
    # Data untuk grafik: jumlah pengajuan per jenis surat
    grafik_data = {}
    for p in pengajuan_list:
        nama = p.surat.nama
        grafik_data[nama] = grafik_data.get(nama, 0) + 1
    return render_template('laporan_surat.html', pengajuan_list=pengajuan_list, dari=dari, sampai=sampai, grafik_data=grafik_data)

@app.route('/lupa-password', methods=['GET', 'POST'])
def lupa_password():
    if request.method == 'POST':
        username = request.form['username']
        from models import ResetPasswordRequest
        req = ResetPasswordRequest(username=username)
        db.session.add(req)
        db.session.commit()
        flash('Permintaan reset password telah dikirim ke admin. Silakan tunggu konfirmasi.')
        return redirect(url_for('login'))
    return render_template('lupa_password.html')

@app.route('/reset-password-requests', methods=['GET', 'POST'])
@login_required
def reset_password_requests():
    if current_user.role != 'admin':
        flash('Hanya admin yang dapat mengakses halaman ini.')
        return redirect(url_for('dashboard'))
    from models import ResetPasswordRequest, User
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        user = User.query.filter_by(username=username).first()
        if user:
            user.set_password(new_password)
            db.session.commit()
            # Update status permintaan reset
            req = ResetPasswordRequest.query.filter_by(username=username, status='pending').first()
            if req:
                req.status = 'selesai'
                db.session.commit()
            flash(f'Password untuk {username} berhasil diubah.')
        else:
            flash('User tidak ditemukan.')
        return redirect(url_for('reset_password_requests'))
    requests = ResetPasswordRequest.query.filter_by(status='pending').order_by(ResetPasswordRequest.requested_at.asc()).all()
    return render_template('reset_password_requests.html', requests=requests) 