button{width:100%;padding:11px;background:#2196F3;color:white;border:none;border-radius:6px;font-size:1    const key = document.getElementById("key").value;
    const res = await fetch("/api/login",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({key:key})
    });
    const d = await res.json();
    if(d.ok){
        window.location.href="/";
    }else{
        document.getElementById("err").innerText=d.msg;
    }
}
</script>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>分片文件上传下载</title>
<style>
*{box-sizing:border-box;font-family:system-ui}
body{max-width:800px;margin:20px auto;padding:0 15px}
.box{border:1px solid #ccc;padding:20px;border-radius:8px;margin-bottom:20px}
#fileInput{margin:10px 0;padding:8px}
#progress{width:100%;height:20px;background:#eee;border-radius:10px;margin:10px 0;display:none}
#progress-bar{height:100%;background:#2196F3;width:0%;border-radius:10px}
#status{margin:8px 0;color:#333}
ul{padding-left:20px}
a{color:#0066cc}
</style>
</head>
<body>
<h2>文件分片上传 & 下载</h2>
<div class="box">
<h3>上传文件</h3>
<input type="file" id="fileInput">
<div id="progress">
<div id="progress-bar"></div>
</div>
<div id="status">等待选择文件</div>
</div>

<div class="box">
<h3>已上传文件列表</h3>
<div id="fileList"></div>
</div>

<script>
const chunkSize = 5 * 1024 * 1024; // 每片5MB
const fileInput = document.getElementById('fileInput');
const progressBar = document.getElementById('progress-bar');
    const totalChunks = Math.ceil(file.size / chunkSize);
    progressWrap.style.display="block";
    statusEl.textContent = `开始上传 ${file.name}`;
:formData
        });
        const percent = ((i+1)/totalChunks*100).toFixed(1);
        progressBar.style.width = percent+"%";
        statusEl.textContent = `上传分片 ${i+1}/${totalChunks} ${percent}%`;
    }
    statusEl.textContent = "上传完成！";
    progressWrap.style.display="none";
    loadFiles();
}

//简易uuid
function uuidv4(){
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c=>{
        const r = Math.random()*16|0;
        return (c=='x'?r:(r&0x3|0x8)).toString(16);
    })
}
</script>
</body>
</html>
"""

def check_auth():
    # 校验：登录标记 + 会话保存的密钥版本必须等于当前缓存密钥
    return session.get("auth_ok") == True and session.get("secret_version") == CACHED_SECRET

@app.route("/")
def index():
    if not check_auth():
        # 密钥变更，清除旧会话，跳转到登录页
        session.clear()
        return render_template_string(HTML_LOGIN)
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/login", methods=["POST"])
def api_login():
    j = request.get_json()
    user_input_key = j.get("key","")
    real_secret = CACHED_SECRET
    if real_secret is None:
        return jsonify({"ok":False,"msg":"暂未获取到密钥，请稍后重试"}),500
    if user_input_key == real_secret:
        session["auth_ok"] = True
        session["secret_version"] = real_secret
        return jsonify({"ok":True})
    return jsonify({"ok":False,"msg":"密钥错误"}),403

 = int(request.form["chunkIndex"])
    total = int(request.form["totalChunks"])
    chunk = request.files["chunk"]

    temp_dir = os.path.join(UPLOAD_FOLDER, file_id)
    os.makedirs(temp_dir, exist_ok=True)
    chunk.save(os.path.join(temp_dir, f"{chunk_idx}"))

    chunks = os.listdir(temp_dir)
    if len(chunks) == total:
        out_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(out_path,"wb") as fout:
            for i in range(total):
   (p):
            files.append({"name":name})
    return jsonify({"files":files})

@app.route("/api/download/<fname>")
def download(fname):
    if not check_auth():
        session.clear()
        return jsonify({"ok":False,"msg":"未授权，密钥已更新，请重新登录"}),403
    path = os.path.join(UPLOAD_FOLDER,fname)
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)?﻿ox{background:#1e1e1e;padding:16px;border-radius:8px;margin-bottom:16px}
h3{malrgin-botthom:12px;color:#fff}
.gap:10pxflex-wrap:wrap;margin-bottom:10px;align-items:center}
input{padding:7px;border-radius:4px;border