<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>服务导航</title>

<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,"Microsoft YaHei";}
body{background:linear-gradient(135deg,#dbeafe,#eef2ff);padding:15px;}
.container{max-width:520px;margin:auto;}
h1{text-align:center;margin:15px 0;font-size:22px;font-weight:900;}

/* 网格 */
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;}

/* 卡片 */
.card{
    position:relative;
    padding:15px;
    border-radius:16px;
    color:#fff;
    font-weight:800;
    text-align:center;
    text-decoration:none;
    font-size:15px;
    box-shadow:0 6px 15px rgba(0,0,0,0.15);
}
.card:active{transform:scale(0.95);}

/* 红绿灯 */
.dot{
    position:absolute;
    top:8px;
    right:8px;
    width:14px;
    height:14px;
    border-radius:50%;
    background:#aaa;
}
.ok{background:#22c55e;box-shadow:0 0 10px #22c55e;}
.bad{background:#ef4444;box-shadow:0 0 10px #ef4444;}

/* 颜色 */
.b1{background:#409eff;}
.b2{background:#f56c6c;}
.b3{background:#67c23a;}
.b4{background:#9c88ff;}
.b5{background:#e6a23c;}
.b6{background:#36cfc9;}
.b7{background:#ff7875;}
.b8{background:#73c0de;}
.b9{background:#bae637;}
.b10{background:#85a5ff;}

/* 工具 */
.tools{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px;}
button{border:none;padding:12px;border-radius:12px;color:#fff;font-weight:700;}
.addr{background:#22c55e;}
.log{background:#f59e0b;}
.down{background:#6366f1;}

/* 面板 */
.panel{
    display:none;
    margin-top:10px;
    background:#fff;
    padding:12px;
    border-radius:12px;
    font-size:13px;
    line-height:1.7;
}

/* 提示 */
.tip{
    display:none;
    margin-bottom:10px;
    background:#fff;
    padding:10px;
    border-radius:10px;
    color:red;
    text-align:center;
}
</style>
</head>

<body>

<div class="container">

<h1>服务导航</h1>

<div class="tip" id="tip"></div>

<div class="grid">

<a class="card b1" href="http://150.158.118.31:9000" onclick="go(event,'9000')">Python文件<span class="dot" id="d9000"></span></a>
<a class="card b2" href="http://150.158.118.31:9001" onclick="go(event,'9001')">Python聊天<span class="dot" id="d9001"></span></a>
<a class="card b3" href="http://150.158.118.31:8585" onclick="go(event,'8585')">Gpt1<span class="dot" id="d8585"></span></a>
<a class="card b4" href="http://150.158.118.31:8686" onclick="go(event,'8686')">Gpt2<span class="dot" id="d8686"></span></a>
<a class="card b5" href="http://150.158.118.31:8777" onclick="go(event,'8777')">C#<span class="dot" id="d8777"></span></a>
<a class="card b6" href="http://150.158.118.31:8000" onclick="go(event,'8000')">豆包<span class="dot" id="d8000"></span></a>
<a class="card b7" href="http://150.158.118.31:8111" onclick="go(event,'8111')">就是<span class="dot" id="d8111"></span></a>
<a class="card b8" href="http://150.158.118.31:8222" onclick="go(event,'8222')">OK<span class="dot" id="d8222"></span></a>
<a class="card b9" href="http://150.158.118.31:8333" onclick="go(event,'8333')">的<span class="dot" id="d8333"></span></a>
<a class="card b10" href="http://150.158.118.31:8666" onclick="go(event,'8666')">专业<span class="dot" id="d8666"></span></a>

</div>

<div class="tools">
<button class="addr" onclick="toggle('addr')">地址</button>
<button class="log" onclick="toggle('log')">日志</button>
<button class="down" onclick="downloadLog()">下载</button>
</div>

<div class="panel" id="addr">
1. Python文件：http://150.158.118.31:9000<br>
2. Python聊天：http://150.158.118.31:9001<br>
3. Gpt1：http://150.158.118.31:8585<br>
4. Gpt2：http://150.158.118.31:8686<br>
5. C#：http://150.158.118.31:8777<br>
6. 豆包：http://150.158.118.31:8000<br>
7. 就是：http://150.158.118.31:8111<br>
8. OK：http://150.158.118.31:8222<br>
9. 的：http://150.158.118.31:8333<br>
10. 专业：http://150.158.118.31:8666
</div>

<div class="panel" id="log"></div>

</div>

<script>

let logs=[];

function log(t){
    let time=new Date().toLocaleTimeString();
    logs.push(`[${time}] ${t}`);
    document.getElementById("log").innerHTML=logs.join("<br>");
}

/* 检测（不会卡死） */
function check(port){
    let url="http://150.158.118.31:"+port;
    let img=new Image();

    let timer=setTimeout(()=>{
        document.getElementById("d"+port).className="dot bad";
        log(port+" 超时");
    },2000);

    img.onload=()=>{
        clearTimeout(timer);
        document.getElementById("d"+port).className="dot ok";
        log(port+" 成功");
    };

    img.onerror=()=>{
        clearTimeout(timer);
        document.getElementById("d"+port).className="dot bad";
        log(port+" 失败");
    };

    img.src=url+"/favicon.ico?"+Date.now();
}

/* 点击跳转（绝对能跳） */
function go(e,port){
    e.preventDefault();
    let url="http://150.158.118.31:"+port;

    log("访问 "+port);

    // 后台检测（不阻塞跳转）
    check(port);

    // 直接跳转
    setTimeout(()=>location.href=url,100);
}

/* 初始化（并发不卡） */
function init(){
    let ports=["9000","9001","8585","8686","8777","8000","8111","8222","8333","8666"];
    ports.forEach(p=>check(p));
}

function toggle(id){
    let el=document.getElementById(id);
    el.style.display=el.style.display==="block"?"none":"block";
}

function downloadLog(){
    let blob=new Blob([logs.join("\n")],{type:"text/plain"});
    let a=document.createElement("a");
    a.href=URL.createObjectURL(blob);
    a.download="log.txt";
    a.click();
}

init();

</script>

</body>
</html>
