from ..judgments.views.detail.detail_html import detail_html

class demo_request:
    def GET(self):
        return {"query": "cat cat cat cat"}
    
print(detail_html(demo_request, "/uksc/2024/1"))