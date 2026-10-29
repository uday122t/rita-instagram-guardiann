const defaults=[["منع السبام","متابعة الرسائل المتكررة"],["مراجعة الشتائم","تسجيل الإساءة للمراجعة"],["مراجعة الروابط","التنبيه للروابط غير المرغوبة"],["احترام القواعد","متابعة الالتزام بقواعد المجموعة"]];
const $=id=>document.getElementById(id);
let rules=JSON.parse(localStorage.getItem("ritaRules")||"null")||defaults.map(x=>({name:x[0],desc:x[1],enabled:true}));
let logs=JSON.parse(localStorage.getItem("ritaLogs")||"[]");
function save(){localStorage.setItem("ritaRules",JSON.stringify(rules));localStorage.setItem("ritaLogs",JSON.stringify(logs));}
function renderRules(){
  $("ruleList").innerHTML="";
  rules.forEach((r,i)=>{
    const el=document.createElement("label");el.className="rule";
    const span=document.createElement("span");
    const title=document.createElement("b");title.textContent=r.name;
    const desc=document.createElement("small");desc.textContent=r.desc;
    span.append(title,desc);
    const input=document.createElement("input");input.type="checkbox";input.checked=r.enabled;
    input.addEventListener("change",()=>{rules[i].enabled=input.checked;save();$("ruleCount").textContent=rules.filter(x=>x.enabled).length;});
    el.append(span,input);$("ruleList").append(el);
  });
  $("ruleCount").textContent=rules.filter(r=>r.enabled).length;
}
function renderLogs(){
  $("entries").innerHTML="";$("violationCount").textContent=logs.length;
  if(!logs.length){$("entries").innerHTML='<p class="empty">لا توجد مخالفات مسجلة حتى الآن</p>';return;}
  logs.slice().reverse().forEach(x=>{
    const el=document.createElement("div");el.className="entry";
    const info=document.createElement("div");const b=document.createElement("b");b.textContent=x.member+" — "+x.type;
    const d=document.createElement("small");d.textContent=x.details||"بدون تفاصيل";info.append(b,d);
    const time=document.createElement("small");time.textContent=x.time;el.append(info,time);$("entries").append(el);
  });
}
$("violationForm").addEventListener("submit",e=>{
  e.preventDefault();logs.push({member:$("member").value.trim(),type:$("type").value,details:$("details").value.trim(),time:new Date().toLocaleString("ar")});
  save();renderLogs();e.target.reset();
});
$("clearLog").addEventListener("click",()=>{
  if(confirm("مسح كل السجلات المحفوظة على هذا المتصفح؟")){logs=[];save();renderLogs();}
});
renderRules();renderLogs();
fetch("/api/health").then(r=>r.json()).then(d=>{
  $("apiStatus").textContent=d.status==="ok"?"الخادم يعمل — اتصال Instagram غير مفعّل":"تعذّر فحص الخادم";
}).catch(()=>$("apiStatus").textContent="تعذّر الوصول إلى الخادم");
