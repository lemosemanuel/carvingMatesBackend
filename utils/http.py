from flask import jsonify

def ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status

def created(data=None):
    return ok(data, 201)

def error(message, status=400, details=None):
    return jsonify({"ok": False, "error": {"message": message, "details": details}}), status