import os

arayuz_path = 'c:\\Windows.old.000\\Users\\nebio\\Desktop\\tum\\HATARAMA\\arayuz.py'
with open(arayuz_path, 'r', encoding='utf-8') as f:
    content = f.read()

import re

new_page_code = '''
                    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>HATA RAMA - Güncel Analiz</title>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
    <style>
        body {{ padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; }}
        .container-fluid {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class='container-fluid'>
        <h2 class='mb-4 text-primary'>Güncel SİNOPTİK Analiz Sonuçları</h2>
        <div class='mb-3 text-muted'>Son Güncellenme: {{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}}</div>
        <div class='table-responsive'>
            {{html_str}}
        </div>
    </div>

    <!-- Bootstrap Modal -->
    <div class="modal fade" id="detailModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title text-danger fw-bold">🔍 Hata Detay İncelemesi</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" id="modalContent" style="font-family: monospace; white-space: pre-wrap;">
          </div>
        </div>
      </div>
    </div>

    <script src='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'></script>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            var table = document.querySelector(".table");
            if(table) {{
                var thead = table.querySelector("thead tr");
                var tbody = table.querySelector("tbody");
                
                if (thead && tbody) {{
                    var th = document.createElement("th");
                    th.innerHTML = "Aksiyon";
                    thead.appendChild(th);
                    
                    var headers = Array.from(thead.querySelectorAll("th")).map(th => th.innerText);
                    
                    Array.from(tbody.querySelectorAll("tr")).forEach(function(tr) {{
                        var td = document.createElement("td");
                        var btn = document.createElement("button");
                        btn.className = "btn btn-primary btn-sm fw-bold";
                        btn.innerHTML = "🔍 İNCELE";
                        btn.onclick = function() {{
                            var cells = tr.querySelectorAll("td");
                            var content = "";
                            for(var i=0; i<cells.length-1; i++) {{
                                content += "• " + headers[i].toUpperCase() + ":\\n" + cells[i].innerText + "\\n\\n";
                            }}
                            document.getElementById("modalContent").innerText = content;
                            var myModal = new bootstrap.Modal(document.getElementById('detailModal'));
                            myModal.show();
                        }};
                        td.appendChild(btn);
                        tr.appendChild(td);
                    }});
                }}
            }}
            setTimeout(function(){{ location.reload(); }}, 30000);
        }});
    </script>
</body>
</html>"""
                    page = html_template
'''

content = re.sub(r'page = f"<!DOCTYPE html>.*?</html>"', new_page_code.strip(), content, flags=re.DOTALL)

with open(arayuz_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Web page updated with modal!")
