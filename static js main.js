// يتصل بـ Flask (مسار /api/analyze) بدلاً من الاتصال المباشر بالـ API
document.getElementById('btnAnalyze').onclick = async () => {
  const kw = document.getElementById('keyword').value.trim();
  if(!kw){alert('أدخل كلمة مفتاحية');return;}

  document.getElementById('loader').classList.remove('d-none');
  document.getElementById('results').classList.add('d-none');

  try{
    const res = await fetch('/api/analyze',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({keyword:kw})
    });
    const data = await res.json();
    if(data.error){alert(data.error);return;}

    // عرض النتائج
    ['suggested_title','meta_description','snippet_text','nlp_keywords']
       .forEach(f=> document.getElementById(f).textContent = data[f]||'');

    // الروابط
    const ul = document.getElementById('featured_snippets'); ul.innerHTML='';
    data.featured_snippets.forEach(h=> ul.insertAdjacentHTML('beforeend',`<li>${h}</li>`));

    // المخطط
    const ol = document.getElementById('outline'); ol.innerHTML='';
    data.outline.forEach(h=> ol.insertAdjacentHTML('beforeend',`<li>${h.text}</li>`));

    document.getElementById('results').classList.remove('d-none');
  }catch(e){
    alert('فشل الاتصال: '+e);
  }finally{
    document.getElementById('loader').classList.add('d-none');
  }
};