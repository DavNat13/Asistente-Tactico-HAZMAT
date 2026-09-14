# lateral_js.py — JavaScript para toggle del panel lateral
"""
Script JS para alternar la barra lateral de Streamlit
mediante manipulación del DOM. Extraído de header.py
para mantener módulos bajo 100 líneas.
"""

JS_ALTERNAR_LATERAL = """
<script>
(function(){
if(window.__hazmatInit)return;window.__hazmatInit=true;
var P=window.parent.document;
function btn(){
var b=P.querySelector('[data-testid="stSidebarCollapseButton"]');
if(b)return b;
var s=['[aria-label="Collapse sidebar"]','[aria-label="Expand sidebar"]',
'[aria-label="Cerrar barra lateral"]','[aria-label="Abrir barra lateral"]'];
for(var i=0;i<s.length;i++){b=P.querySelector('[data-testid="stSidebar"] '+s[i]);if(b)return b;}
return P.querySelector('[data-testid="stSidebar"] button')||null;
}
function abierto(){
var sb=P.querySelector('[data-testid="stSidebar"]');
if(!sb)return true;
if(sb.getAttribute('aria-hidden')==='true')return false;
if(sb.getAttribute('aria-expanded')==='false')return false;
var s=window.parent.getComputedStyle(sb);
if(s.transform&&s.transform!=='none'){
var m=s.transform.match(/matrix\\(([^)]+)\\)/);
if(m){var p=m[1].split(',');if(parseFloat(p[4])<-100)return false;}}
return true;
}
window.__hazmatAlternar=function(){var b=btn();if(b)b.click();};
function sincronizar(){
var el=document.querySelector('.hazmat-cab__toggle');
if(!el)return;var a=abierto();
el.innerHTML=a?'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="15" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>'
:'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
el.title=a?'Cerrar panel':'Abrir panel';
el.setAttribute('aria-label',a?'Cerrar panel lateral':'Abrir panel lateral');
}
var obs=null;
function adjuntar(){var sb=P.querySelector('[data-testid="stSidebar"]');if(!sb||obs)return;
obs=new MutationObserver(sincronizar);obs.observe(sb,{attributes:true,attributeFilter:['class','style','aria-hidden','aria-expanded']});}
new MutationObserver(function(){adjuntar();sincronizar();}).observe(P.body,{childList:true,subtree:true});
setTimeout(sincronizar,300);setTimeout(sincronizar,800);adjuntar();
})();
</script>
"""
