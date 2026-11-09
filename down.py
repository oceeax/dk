from flask import Flask, render_template_string, request, send_file, redirect, url_for
import os
import io
import string
import shutil
import time
import zipfile
import platform
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = "supersecretkey123456"
ADMIN_USER = "admin"
ADMIN_PASS = "jkljkl"
LOGGED_IN = False

if platform.system() == "Windows":
    LOG_FILE = r"C:\Users\file_log.txt"
else:
    LOG_FILE = "/var/tmp/file_log.txt"

MAX_LOG_LINES = 500


# ========== ✅ 编码修复工具 ==========
def fix_mojibake(name):
    """修复浏览器上传中文文件名被 latin-1 误解码导致的乱码"""
    if not name:
        return name
    try:
        return name.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def attachment_response(path_or_buf, filename, mimetype=None):
    """统一下载响应头，强制 RFC 5987 编码，保证中文文件名不乱码"""
    resp = send_file(path_or_buf, as_attachment=True,
                     download_name=filename, mimetype=mimetype)
    ascii_fallback = filename.encode("ascii", "ignore").decode("ascii") or "download"
    resp.headers["Content-Disposition"] = (
        'attachment; filename="{}"; filename*=UTF-8\'\'{}'.format(
            ascii_fallback, quote(filename)
        )
    )
    return resp
# ====================================


def write_log(content):
    t = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        lines = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        lines.append(f"[{t}] {content}\n")
        if len(lines) > MAX_LOG_LINES:
            lines = lines[-MAX_LOG_LINES:]
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception:
        pass


def get_all_drives():
    drives = []
    if platform.system() == "Windows":
        for c in string.ascii_uppercase:
            d = f"{c}:\\"
            if os.path.isdir(d):
                drives.append(d)
    else:
        drives.append("/")
    return drives


def list_dir(path):
    skip_win = ("Windows", "Program Files", "Program Files (x86)", "$Recycle.Bin")
    skip_linux = ("/proc", "/sys", "/dev", "/run")
    items = []
    try:
        for name in os.listdir(path):
            full = os.path.join(path, name)
            if platform.system() != "Windows":
                if full in skip_linux:
                    continue
            else:
                if name in skip_win:
                    continue
            is_dir = os.path.isdir(full)
            items.append({"name": name, "path": full, "is_dir": is_dir})
    except PermissionError:
        pass
    return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))


@app.route("/login", methods=["GET", "POST"])
def login():
    global LOGGED_IN
    if request.method == "POST":
        u = request.form.get("user")
        p = request.form.get("pass")
        if u == ADMIN_USER and p == ADMIN_PASS:
            LOGGED_IN = True
            write_log("管理员登录成功")
            return redirect(url_for("index"))
        write_log(f"登录失败:{u}")
    return render_template_string('''
    <!DOCTYPE html>
    <html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,Arial}
    body{background:#f5f7fa;padding:20px}
    .box{max-width:400px;margin:40px auto;background:#fff;padding:30px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.1)}
    h2{text-align:center;margin-bottom:24px}
    .inp{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px;font-size:16px}
    .btn{width:100%;padding:12px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-size:16px}
    </style></head><body>
    <div class="box">
        <h2>管理员登录</h2>
        <form method=post>
            <input class="inp" name=user placeholder="账号" value="admin">
            <input class="inp" name=pass type=password placeholder="密码">
            <button class="btn">登录系统</button>
        </form>
    </div>
    </body></html>
    ''')


@app.route("/")
def index():
    if not LOGGED_IN:
        return redirect(url_for("login"))
    drives = get_all_drives()
    write_log("进入盘符页")
    return render_template_string('''
    <!DOCTYPE html>
    <html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,Arial}
    body{background:#f5f7fa;padding:20px}
    .box{max-width:700px;margin:0 auto;background:#fff;padding:24px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.1)}
    h2{margin-bottom:20px}
    .drive{display:block;padding:14px;margin:10px 0;background:#eff6ff;border-radius:8px;text-decoration:none;color:#2563eb;font-size:16px}
    </style></head><body>
    <div class="box">
        <h2>全盘文件管理器</h2>
        {% for d in drives %}
            <a class="drive" href="/browse?path={{d}}">📂 {{d}}</a>
        {% endfor %}
    </div>
    </body></html>
    ''', drives=drives)


@app.route("/browse")
def browse():
    if not LOGGED_IN:
        return redirect(url_for("login"))
    drives = get_all_drives()
    path = request.args.get("path", drives[0])
    write_log(f"浏览:{path}")
    items = list_dir(path)
    return render_template_string('''
    <!DOCTYPE html>
    <html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,Arial}
    body{background:#f5f7fa;padding:15px}
    .box{max-width:900px;margin:0 auto;background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.1)}
    .path{font-size:14px;color:#666;margin-bottom:16px;word-break:break-all}
    .back{display:inline-block;margin-bottom:16px;padding:8px 14px;background:#eee;border-radius:6px;text-decoration:none;color:#333;margin-right:8px}
    .gohome{display:inline-block;margin-bottom:16px;padding:8px 14px;background:#eff6ff;border-radius:6px;text-decoration:none;color:#2563eb}
    .item{padding:12px 10px;border-bottom:1px solid #eee;display:flex;flex-wrap:wrap;align-items:center;gap:8px;word-break:break-all}
    .op a{padding:4px 8px;border-radius:4px;text-decoration:none;font-size:14px;margin:0 4px}
    .down{background:#dcfce7;color:#166534}
    .del{background:#fee2e2;color:#dc2626}
    .ren{background:#fff3cd;color:#92400e}
    .zip{background:#dbeafe;color:#1d4ed8}
    .folder{color:#2563eb;font-weight:500;text-decoration:none}
    .upload-box{margin-top:20px;padding:16px;background:#f8fafc;border-radius:8px}
    input,button{padding:8px 12px;font-size:15px;border-radius:6px;border:1px solid #ddd}
    button{background:#2563eb;color:#fff;border:none}
    </style></head><body>
    <div class="box">
        <a class="back" href="javascript:history.back()">← 返回上一页</a>
        <a class="gohome" href="/">🏠 返回盘符主页</a>
        <div class="path">当前路径：{{path}}</div>
        {% for i in items %}
            <div class="item">
            {% if i.is_dir %}
                <a class="folder" href="/browse?path={{i.path}}">📁 {{i.name}}</a>
                <div class="op">
                    <a class="zip" href="/download_folder?path={{i.path}}">⬇ 下载文件夹</a>
                    <a class="ren" href="/rename?path={{i.path}}">重命名</a>
                    <a class="del" href="/delete?path={{i.path}}" onclick="return confirm('删除文件夹及全部内容？')">删除</a>
                </div>
            {% else %}
                <span>📄 {{i.name}}</span>
                <div class="op">
                    <a class="down" href="/download?path={{i.path}}">下载</a>
                    <a class="ren" href="/rename?path={{i.path}}">重命名</a>
                    <a class="del" href="/delete?path={{i.path}}" onclick="return confirm('删除文件？')">删除</a>
                </div>
            {% endif %}
            </div>
        {% endfor %}
        <div class="upload-box">
            <h4>上传文件</h4>
            <form action="/upload?path={{path}}" method=post enctype=multipart/form-data style="margin-top:10px">
                <input type=file name=file multiple required>
                <button>上传</button>
            </form>
            <h4 style="margin-top:18px">上传文件夹</h4>
            <form action="/upload?path={{path}}" method=post enctype=multipart/form-data style="margin-top:10px">
                <input type=file name=file webkitdirectory directory multiple required>
                <button>上传文件夹</button>
            </form>
        </div>
    </div>
    </body></html>
    ''', path=path, items=items)


@app.route("/rename", methods=["GET", "POST"])
def rename():
    if not LOGGED_IN:
        return redirect(url_for("login"))
    path = request.args.get("path")
    dir_path = os.path.dirname(path)
    old_name = os.path.basename(path)
    if request.method == "POST":
        new_name = request.form.get("new_name", "").strip()
        if new_name:
            new_path = os.path.join(dir_path, new_name)
            try:
                os.rename(path, new_path)
                write_log(f"重命名:{path}→{new_path}")
            except Exception as e:
                write_log(f"重命名失败:{path} {e}")
        return redirect(f"/browse?path={dir_path}")
    return render_template_string('''
    <!DOCTYPE html>
    <html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,Arial}
    body{background:#f5f7fa;padding:20px}
    .box{max-width:450px;margin:20px auto;background:#fff;padding:24px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.1)}
    h3{margin-bottom:16px}
    .old{color:#666;margin-bottom:12px;word-break:break-all}
    input{width:100%;padding:10px;border:1px solid #ddd;border-radius:8px;font-size:16px;margin-bottom:16px}
    button{padding:10px 16px;background:#2563eb;color:#fff;border:none;border-radius:8px;margin-right:10px}
    a{text-decoration:none;color:#666;margin-right:8px}
    </style></head><body>
    <div class="box">
        <a href="javascript:history.back()">← 返回上一页</a>
        <h3>重命名</h3>
        <div class="old">原名称：{{old_name}}</div>
        <form method=post>
            <input name="new_name" placeholder="新名称" required>
            <button>确认</button>
            <a href="/browse?path={{dir_path}}">取消</a>
        </form>
    </div>
    </body></html>
    ''', old_name=old_name, dir_path=dir_path)


@app.route("/download")
def download():
    if not LOGGED_IN:
        return redirect(url_for("login"))
    path = request.args.get("path")
    write_log(f"下载:{path}")
    try:
        return attachment_response(path, os.path.basename(path))
    except Exception:
        write_log(f"下载失败:{path}")
        return "失败"


@app.route("/download_folder")
def download_folder():
    if not LOGGED_IN:
        return redirect(url_for("login"))
    path = request.args.get("path")
    write_log(f"下载文件夹:{path}")
    if not path or not os.path.exists(path):
        write_log(f"下载文件夹失败(不存在):{path}")
        return "失败"
    try:
        norm = os.path.normpath(path)
        folder_name = os.path.basename(norm) or "root"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.isdir(norm):
                base_parent = os.path.dirname(norm)
                for root, dirs, files in os.walk(norm):
                    rel_dir = os.path.relpath(root, base_parent)
                    if not dirs and not files:
                        zf.writestr(rel_dir.replace(os.sep, "/") + "/", "")
                    for name in files:
                        full = os.path.join(root, name)
                        arc = os.path.relpath(full, base_parent)
                        try:
                            zf.write(full, arc)
                        except Exception as e:
                            write_log(f"打包跳过:{full} {e}")
                            continue
            else:
                zf.write(norm, os.path.basename(norm))
        buf.seek(0)
        write_log(f"下载文件夹成功:{path}")
        return attachment_response(buf, f"{folder_name}.zip",
                                   mimetype="application/zip")
    except Exception as e:
        write_log(f"下载文件夹失败:{path} {e}")
        return "失败"


@app.route("/delete")
def delete():
    if not LOGGED_IN:
        return redirect(url_for("login"))
    path = request.args.get("path")
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            write_log(f"删文件夹:{path}")
        else:
            os.remove(path)
            write_log(f"删文件:{path}")
    except Exception as e:
        write_log(f"删除失败:{path} {e}")
    return redirect(request.referrer or "/")


@app.route("/upload", methods=["POST"])
def upload():
    if not LOGGED_IN:
        return redirect(url_for("login"))
    base_path = request.args.get("path") or "/"
    files = request.files.getlist("file")
    saved = 0
    real_base = os.path.abspath(base_path)
    for f in files:
        if not f or not f.filename:
            continue
        # ✅ 关键：先修复中文文件名乱码
        filename = fix_mojibake(f.filename)
        rel = filename.replace("\\", "/")
        parts = [p for p in rel.split("/") if p not in ("", ".", "..")]
        if not parts:
            continue
        rel = os.path.join(*parts)
        save_path = os.path.join(base_path, rel)
        try:
            real_save = os.path.abspath(save_path)
            if os.path.commonpath([real_base, real_save]) != real_base:
                write_log(f"上传拦截(越界):{save_path}")
                continue
            os.makedirs(os.path.dirname(real_save), exist_ok=True)
            f.save(real_save)
            write_log(f"上传:{real_save}")
            saved += 1
        except Exception as e:
            write_log(f"上传失败:{save_path} {e}")
    write_log(f"本次上传完成，共 {saved} 个文件")
    return redirect(request.referrer or "/")


if __name__ == "__main__":
    print("http://0.0.0.0:8116")
    app.run(host="0.0.0.0", port=8116, threaded=True)



