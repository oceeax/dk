y{max-width:800px;margin:20px auto;padding:0 15px}
.box{border:1px solid #ccc;padding:20px;border-radius:8px;margin-bottom:20px}
#fco nst file In put ileI npu t{margin:10px 0;padding:8px}
#pro gress{width:100%;height:20px;background:#eee;border-radius:10px;margin:10px 0;display:none}
#pro gress-b ar{height:100%;background:#2196F3;width:0%;border-radius:10px}
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
const file In put = document.getElementById('fileInput');
const progressBar = document.getElementById('progress-bar');
    const totalChunks = Math.ceil(file.size / chunkSize);
    progressWrap.style.display="block";
    statusEl.textContent = `开始上传 ${file.name}`;
:formData
        });
        const percent = ((i+1)/totalChunks*100).toFixed(1);
        progressBar.style.width = percent+"%";
        statusEl.textContent = `上传分片 ${i+1}/${totalChunks} ${percent}%`;
{padding:7px;border-radius:4px;border