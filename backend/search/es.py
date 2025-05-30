INDEX = "ssoar_demo"

MAPPING = {
    "mappings": {
        "properties": {
            "title":      {"type": "text"},
            "abstract":   {"type": "text"},
            "full_text":  {"type": "text"},
            "authors":    {"type": "keyword"},
            "year":       {"type": "integer"}
        }
    }
}