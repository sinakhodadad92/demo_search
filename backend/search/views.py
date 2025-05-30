# File: backend/search/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from elasticsearch import Elasticsearch, NotFoundError
from .es import INDEX

# Initialize Elasticsearch client
es = Elasticsearch(settings.ES_HOST)

class SearchView(APIView):
    """
    GET /api/search/?q=<term>&page=<n>&size=<m>
    Multi-field BM25 with term suggester for spell-check.
    If q is blank, returns all documents.
    """
    def get(self, request):
        q = request.GET.get('q', '').strip()
        page = int(request.GET.get('page', 1))
        size = int(request.GET.get('size', 10))
        from_ = (page - 1) * size

        # Build query or match_all
        if q:
            query_body = {
                "multi_match": {
                    "query": q,
                    "fields": ["title^3", "abstract^2", "full_text"]
                }
            }
        else:
            query_body = {"match_all": {}}

        body = {
            "query": query_body,
            "from": from_,
            "size": size,
            "highlight": {"fields": {"title": {}, "abstract": {}, "full_text": {}}}
        }

        # Add term suggester if user provided a query
        if q:
            body["suggest"] = {
                "spellcheck": {
                    "text": q,
                    "term": {"field": "full_text"}
                }
            }

        # Include max_analyzed_offset to avoid highlight errors on large fields
        res = es.search(
            index=INDEX,
            body=body,
            # params={"max_analyzed_offset": "2000000"}   # ✔ correct place
        )
        hits = res.get('hits', {})
        total = hits.get('total', {}).get('value', 0)
        docs = hits.get('hits', [])

        results = [
            {
                "id": h['_id'],
                "score": h.get('_score'),
                "source": h.get('_source', {}),
                "highlight": h.get('highlight', {})
            }
            for h in docs
        ]

        # Extract suggestion
        suggestion = None
        if 'suggest' in res:
            opts = res['suggest']['spellcheck'][0].get('options', [])
            if opts:
                suggestion = opts[0]['text']

        payload = {"total": total, "results": results}
        if suggestion and suggestion.lower() != q.lower():
            payload['suggestion'] = suggestion

        return Response(payload)


class DocDetailView(APIView):
    """
    GET /api/doc/<id>/
    Retrieve a single document by ID.
    """
    def get(self, request, id):
        try:
            doc = es.get(index=INDEX, id=id)
        except NotFoundError:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"id": doc['_id'], "source": doc.get('_source', {})})


class HealthCheckView(APIView):
    """
    GET /api/healthz/
    Basic liveness and ES status.
    """
    def get(self, request):
        try:
            health = es.cluster.health()
            return Response({"status": "ok", "elastic_status": health.get("status")})
        except Exception:
            return Response({"status": "error"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
